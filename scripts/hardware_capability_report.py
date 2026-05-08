from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

ENV_HARDWARE_TEST = "FLYCAPTURE2_HARDWARE_TEST"
ENV_CAMERA_INDEX = "FLYCAPTURE2_CAMERA_INDEX"
FC2_INTERFACE_GIGE = 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit a readonly FlyCapture2 hardware capability report as JSON.")
    parser.add_argument("--output", type=Path, default=None, help="write JSON report to this path")
    parser.add_argument("--camera-index", type=int, default=None, help=f"override {ENV_CAMERA_INDEX}")
    return parser.parse_args(argv)


def require_hardware_opt_in() -> None:
    if os.environ.get(ENV_HARDWARE_TEST) != "1":
        raise SystemExit(f"Refusing to touch hardware. Set {ENV_HARDWARE_TEST}=1 to enable this diagnostic.")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_json(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if is_dataclass(value):
        return normalize_json(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): normalize_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_json(item) for item in value]
    return value


def capability_ok(value: Any) -> dict[str, Any]:
    return {"status": "ok", "value": normalize_json(value)}


def capability_unsupported(exc: Exception) -> dict[str, Any]:
    return {"status": "unsupported", "error": error_payload(exc)}


def capability_error(exc: Exception) -> dict[str, Any]:
    return {"status": "error", "error": error_payload(exc)}


def error_payload(exc: Exception) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def probe(call: Callable[[], Any]) -> dict[str, Any]:
    from flycapture2_c.errors import FC2ErrorCode, FlyCapture2Error, FlyCapture2NotSupportedError

    try:
        return capability_ok(call())
    except FlyCapture2NotSupportedError as exc:
        return capability_unsupported(exc)
    except FlyCapture2Error as exc:
        if exc.code in {FC2ErrorCode.NOT_IMPLEMENTED, FC2ErrorCode.NOT_SUPPORTED}:
            return capability_unsupported(exc)
        return capability_error(exc)
    except Exception as exc:
        return capability_error(exc)


def collect_property_capabilities(camera) -> list[dict[str, Any]]:
    from flycapture2_c.properties import KNOWN_PROPERTY_TYPES

    results: list[dict[str, Any]] = []
    for property_type in KNOWN_PROPERTY_TYPES:
        item = {"property_type": property_type.name}
        info_result = probe(lambda property_type=property_type: camera.get_property_info(property_type))
        item["info"] = info_result
        if info_result["status"] == "ok":
            info = info_result["value"]
            if info.get("present") and info.get("read_out_supported"):
                item["value"] = probe(lambda property_type=property_type: camera.get_property(property_type))
            else:
                item["value"] = {"status": "skipped", "reason": "property is absent or not readable"}
        else:
            item["value"] = {"status": "skipped", "reason": "property info unavailable"}
        results.append(item)
    return results


def collect_format7_capabilities(camera) -> dict[str, Any]:
    modes: list[dict[str, Any]] = []
    for mode in range(5):
        info_result = probe(lambda mode=mode: camera.get_format7_info(mode=mode))
        item: dict[str, Any] = {"mode": mode, "info": info_result}
        if info_result["status"] == "ok":
            item["pixel_formats"] = pixel_format_summary_from_bitfield(info_result["value"]["pixel_format_bit_field"])
        modes.append(item)
    return {
        "modes": modes,
        "current_configuration": probe(camera.get_format7_configuration),
    }


def pixel_format_summary_from_bitfield(bitfield: int) -> dict[str, list[str]]:
    from flycapture2_c.pixel_format import interpret_pixel_format_bitfield

    return interpret_pixel_format_bitfield(int(bitfield))


def collect_strobe_capabilities(camera) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for source in range(4):
        info = probe(lambda source=source: camera.get_strobe_info(source))
        item = {"source": source, "info": info}
        if info["status"] == "ok" and info["value"].get("present") and info["value"].get("read_out_supported"):
            item["value"] = probe(lambda source=source: camera.get_strobe(source))
        else:
            item["value"] = {"status": "skipped", "reason": "strobe source is absent or not readable"}
        items.append(item)
    return items


def collect_gpio_capabilities(camera) -> list[dict[str, Any]]:
    return [
        {"pin": pin, "direction": probe(lambda pin=pin: camera.get_gpio_pin_direction(pin))}
        for pin in range(4)
    ]


def collect_gige_capabilities(camera) -> dict[str, Any]:
    from flycapture2_c.gige import GigEPropertyType

    stream_channels: list[dict[str, Any]] = []
    channel_count_result = probe(camera.get_num_gige_stream_channels)
    if channel_count_result["status"] == "ok":
        for channel in range(int(channel_count_result["value"])):
            stream_channels.append(
                {"channel": channel, "info": probe(lambda channel=channel: camera.get_gige_stream_channel_info(channel))}
            )

    image_settings_info = probe(camera.get_gige_image_settings_info)
    result = {
        "config": probe(camera.get_gige_config),
        "properties": [
            {"property_type": property_type.name, "value": probe(lambda property_type=property_type: camera.get_gige_property(property_type))}
            for property_type in GigEPropertyType
        ],
        "imaging_mode": probe(camera.get_gige_imaging_mode),
        "image_settings_info": image_settings_info,
        "image_settings": probe(camera.get_gige_image_settings),
        "binning_settings": probe(camera.get_gige_image_binning_settings),
        "stream_channel_count": channel_count_result,
        "stream_channels": stream_channels,
    }
    if image_settings_info["status"] == "ok":
        result["pixel_formats"] = pixel_format_summary_from_bitfield(
            image_settings_info["value"]["pixel_format_bit_field"]
        )
    return result


def collect_capability_report(camera_index: int) -> dict[str, Any]:
    from flycapture2_c import Camera, enumerate_cameras
    from flycapture2_c._hardware_tools import camera_info_to_dict
    from flycapture2_c.api import get_api

    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": now_utc_iso(),
        "camera_index": camera_index,
        "hardware_opt_in": os.environ.get(ENV_HARDWARE_TEST) == "1",
        "camera_count": None,
        "library_version": probe(lambda: get_api().get_library_version()),
        "capabilities": {},
        "errors": [],
    }

    cameras = enumerate_cameras()
    report["camera_count"] = len(cameras)
    if camera_index < 0 or camera_index >= len(cameras):
        report["errors"].append(
            {
                "capability": "open",
                "error": {
                    "type": "CameraIndexError",
                    "message": f"camera index {camera_index} is out of range for {len(cameras)} camera(s)",
                },
            }
        )
        return normalize_json(report)

    with Camera.open(index=camera_index) as camera:
        camera_info = camera.get_camera_info(refresh=True)
        report["camera_info"] = camera_info_to_dict(camera_info)
        report["capabilities"]["lifecycle"] = capability_ok({"opened": camera.is_open, "capturing": camera.is_capturing})
        report["capabilities"]["video_mode_and_frame_rate"] = probe(camera.get_video_mode_and_frame_rate)
        report["capabilities"]["format7"] = collect_format7_capabilities(camera)
        report["capabilities"]["trigger_mode_info"] = probe(camera.get_trigger_mode_info)
        report["capabilities"]["trigger_mode"] = probe(camera.get_trigger_mode)
        report["capabilities"]["software_trigger_symbols"] = capability_ok(
            {
                "fc2FireSoftwareTrigger": hasattr(get_api().dll, "fc2FireSoftwareTrigger"),
                "fc2FireSoftwareTriggerBroadcast": hasattr(get_api().dll, "fc2FireSoftwareTriggerBroadcast"),
            }
        )
        report["capabilities"]["properties"] = collect_property_capabilities(camera)
        report["capabilities"]["configuration"] = probe(camera.get_configuration)
        report["capabilities"]["embedded_image_info"] = probe(camera.get_embedded_image_info)
        report["capabilities"]["camera_stats"] = probe(camera.get_camera_stats)
        report["capabilities"]["strobe"] = collect_strobe_capabilities(camera)
        report["capabilities"]["gpio"] = collect_gpio_capabilities(camera)
        if camera_info.interface_type == FC2_INTERFACE_GIGE:
            report["capabilities"]["gige"] = collect_gige_capabilities(camera)
        else:
            report["capabilities"]["gige"] = {
                "status": "skipped",
                "reason": f"camera interface_type={camera_info.interface_type}; GigE-specific probes require GigE",
            }

    return normalize_json(report)


def emit_report(report: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(report, allow_nan=False, indent=2, sort_keys=True)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


def fatal_report(camera_index: int, exc: Exception) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": now_utc_iso(),
        "camera_index": camera_index,
        "hardware_opt_in": os.environ.get(ENV_HARDWARE_TEST) == "1",
        "camera_count": None,
        "capabilities": {},
        "errors": [{"capability": "setup", "error": error_payload(exc)}],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_hardware_opt_in()
    camera_index = args.camera_index
    if camera_index is None:
        camera_index = int(os.environ.get(ENV_CAMERA_INDEX, "0"))
    try:
        report = collect_capability_report(camera_index)
    except Exception as exc:
        report = fatal_report(camera_index, exc)
    emit_report(report, args.output)
    return 0 if not report.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
