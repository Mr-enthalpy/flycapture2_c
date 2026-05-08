from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flycapture2_c import Camera  # noqa: E402
from flycapture2_c._hardware_tools import (  # noqa: E402
    ENV_CAMERA_INDEX,
    ENV_HARDWARE_TEST,
    ENV_HARDWARE_WRITE_TEST,
    camera_info_to_dict,
)
from flycapture2_c.api import get_api  # noqa: E402
from flycapture2_c.errors import FlyCapture2Error  # noqa: E402
from flycapture2_c.properties import PropertyType  # noqa: E402

DEFAULT_HOST_NOTE = "Stage 6.8 good-host capture-rate validation"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure real-time FlyCapture2 frame acquisition rate.")
    parser.add_argument("--camera-index", type=int, default=int(os.environ.get(ENV_CAMERA_INDEX, "0")))
    parser.add_argument("--duration", type=float, default=10.0, help="timed capture duration in seconds")
    parser.add_argument("--warmup", type=float, default=0.0, help="warmup capture duration in seconds")
    parser.add_argument("--fps", type=float, nargs="*", default=None, help="requested frame-rate property values")
    parser.add_argument("--output", type=Path, default=None, help="JSON output path")
    parser.add_argument("--host-note", default=DEFAULT_HOST_NOTE)
    parser.add_argument("--grab-timeout-ms", type=int, default=2000)
    return parser.parse_args(argv)


def require_hardware_opt_in() -> None:
    if os.environ.get(ENV_HARDWARE_TEST) != "1":
        raise SystemExit(f"Refusing to touch hardware. Set {ENV_HARDWARE_TEST}=1.")


def write_enabled() -> bool:
    return os.environ.get(ENV_HARDWARE_WRITE_TEST) == "1"


def normalize_json(value: Any) -> Any:
    if is_dataclass(value):
        return normalize_json(asdict(value))
    if isinstance(value, dict):
        return {str(key): normalize_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_json(item) for item in value]
    if hasattr(value, "name"):
        return value.name
    return value


def format7_to_dict(configuration: Any) -> dict[str, Any]:
    settings = configuration.settings
    return {
        "mode": settings.mode,
        "offset_x": settings.offset_x,
        "offset_y": settings.offset_y,
        "width": settings.width,
        "height": settings.height,
        "pixel_format": settings.pixel_format.name,
        "packet_size": configuration.packet_size,
        "percentage": configuration.percentage,
    }


def configuration_to_dict(configuration: Any) -> dict[str, Any]:
    payload = asdict(configuration)
    payload["grab_mode"] = configuration.grab_mode.name
    payload["bandwidth_allocation"] = configuration.bandwidth_allocation.name
    return payload


def property_to_dict(value: Any) -> dict[str, Any]:
    payload = asdict(value)
    payload["property_type"] = value.property_type.name
    return payload


def trigger_to_dict(value: Any) -> dict[str, Any]:
    return asdict(value)


def same_dataclass(left: Any, right: Any) -> bool:
    return asdict(left) == asdict(right)


def safe_error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def is_timeout_error(exc: BaseException) -> bool:
    text = f"{type(exc).__name__} {exc}".upper()
    return "TIMEOUT" in text or "TIMED OUT" in text


class CameraStateRestorer:
    def __init__(self, camera: Camera, *, grab_timeout_ms: int) -> None:
        self.camera = camera
        self.grab_timeout_ms = int(grab_timeout_ms)
        self.original_frame_rate = None
        self.original_video_mode_and_frame_rate = None
        self.original_format7 = None
        self.original_configuration = None
        self.original_trigger = None
        self.touched: list[str] = []
        self.restore_failed = False
        self.restore_errors: list[dict[str, str]] = []

    def snapshot(self) -> None:
        self.original_frame_rate = self.camera.get_frame_rate()
        self.original_video_mode_and_frame_rate = self.camera.get_video_mode_and_frame_rate()
        self.original_format7 = self.camera.get_format7_configuration()
        self.original_configuration = self.camera.get_configuration()
        self.original_trigger = self.camera.get_trigger_mode()

    def prepare_for_streaming(self) -> None:
        if self.original_configuration is None or self.original_trigger is None:
            self.snapshot()
        if self.original_configuration.grab_timeout != self.grab_timeout_ms:
            self.camera.set_grab_timeout(self.grab_timeout_ms)
            self.touched.append("capture_config")
        if self.original_trigger.on_off:
            self.camera.disable_trigger()
            self.touched.append("trigger")

    def set_requested_fps(self, requested_fps: float) -> Any:
        if self.original_frame_rate is None:
            self.snapshot()
        written = self.camera.set_frame_rate(float(requested_fps), auto=False)
        self.touched.append("frame_rate_property")
        return written

    def restore(self) -> None:
        try:
            self.camera.stop()
        except Exception as exc:
            self._record_restore_error("stop_capture", exc)
        if self.original_format7 is not None and "format7" in self.touched:
            try:
                settings = self.original_format7.settings
                self.camera.set_format7(
                    mode=settings.mode,
                    offset_x=settings.offset_x,
                    offset_y=settings.offset_y,
                    width=settings.width,
                    height=settings.height,
                    pixel_format=settings.pixel_format,
                    packet_size=self.original_format7.packet_size,
                )
            except Exception as exc:
                self._record_restore_error("format7", exc)
        if self.original_configuration is not None and "capture_config" in self.touched:
            try:
                self.camera.set_configuration(self.original_configuration)
            except Exception as exc:
                self._record_restore_error("capture_config", exc)
        if self.original_frame_rate is not None and "frame_rate_property" in self.touched:
            self._restore_frame_rate_property()
        if self.original_trigger is not None and "trigger" in self.touched:
            try:
                self.camera.set_trigger_mode(self.original_trigger)
            except Exception as exc:
                self._record_restore_error("trigger", exc)
        if (
            self.original_frame_rate is not None
            and self.original_trigger is not None
            and self.original_trigger.on_off
            and "frame_rate_property" in self.touched
        ):
            try:
                self.camera.disable_trigger()
                self._restore_frame_rate_property()
                self.camera.set_trigger_mode(self.original_trigger)
            except Exception as exc:
                self._record_restore_error("frame_rate_property_post_trigger", exc)

    def _record_restore_error(self, name: str, exc: BaseException) -> None:
        self.restore_failed = True
        self.restore_errors.append({"operation": name, **safe_error(exc)})

    def _restore_frame_rate_property(self) -> None:
        assert self.original_frame_rate is not None
        try:
            if self.original_frame_rate.abs_value > 0:
                self.camera.set_frame_rate(float(self.original_frame_rate.abs_value), auto=False)
            self.camera.set_property_raw(
                PropertyType.FRAME_RATE,
                on_off=self.original_frame_rate.on_off,
                one_push=self.original_frame_rate.one_push if self.original_frame_rate.one_push else None,
            )
        except Exception as exc:
            self._record_restore_error("frame_rate_property", exc)


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def capture_for_duration(camera: Camera, *, duration: float, warmup: float) -> dict[str, Any]:
    first_frame = None
    timestamps: list[float] = []
    errors: list[dict[str, str]] = []
    stall = False
    timeout = False
    started = perf_counter()
    deadline = started + max(0.0, duration)
    warmup_deadline = started + max(0.0, warmup)

    capture_started = perf_counter()
    try:
        camera.start()
        while perf_counter() < warmup_deadline:
            try:
                camera.read_frame_with_info()
            except (TimeoutError, FlyCapture2Error) as exc:
                timeout = timeout or is_timeout_error(exc)
                errors.append(safe_error(exc))
                break

        capture_started = perf_counter()
        deadline = capture_started + max(0.0, duration)
        while perf_counter() < deadline:
            try:
                frame = camera.read_frame_with_info()
            except (TimeoutError, FlyCapture2Error) as exc:
                timeout = timeout or is_timeout_error(exc)
                errors.append(safe_error(exc))
                break
            now = perf_counter()
            if first_frame is None:
                first_frame = frame
            timestamps.append(now)
    finally:
        camera.stop()

    elapsed = perf_counter() - capture_started
    frames = len(timestamps)
    interarrival = [(right - left) for left, right in zip(timestamps, timestamps[1:])]
    if frames == 0 or (duration > 0 and elapsed < duration * 0.5 and errors):
        stall = True
    bytes_per_frame = int(first_frame.array.nbytes) if first_frame is not None else None
    actual_fps = frames / elapsed if elapsed > 0 else 0.0
    return {
        "frames": frames,
        "elapsed_seconds": elapsed,
        "actual_wall_clock_fps": actual_fps,
        "frame_shape": list(first_frame.array.shape) if first_frame is not None else None,
        "dtype": str(first_frame.array.dtype) if first_frame is not None else None,
        "pixel_format": first_frame.pixel_format.name if first_frame is not None else None,
        "bytes_per_frame": bytes_per_frame,
        "mib_per_second": (actual_fps * bytes_per_frame / (1024.0 * 1024.0)) if bytes_per_frame else None,
        "interarrival_seconds": {
            "mean": statistics.fmean(interarrival) if interarrival else None,
            "p50": percentile(interarrival, 0.50),
            "p95": percentile(interarrival, 0.95),
            "max": max(interarrival) if interarrival else None,
        },
        "timeout": timeout,
        "stall": stall,
        "sdk_errors": errors,
    }


def measure_once(
    camera: Camera,
    restorer: CameraStateRestorer,
    *,
    requested_fps: float | None,
    duration: float,
    warmup: float,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "requested_fps": requested_fps,
        "status": "ok",
        "unsupported": False,
        "error": None,
    }
    try:
        if requested_fps is not None:
            restorer.set_requested_fps(float(requested_fps))
        readback = camera.get_frame_rate()
        result["sdk_readback_fps"] = readback.abs_value
        result["frame_rate_property"] = property_to_dict(readback)
        result.update(capture_for_duration(camera, duration=duration, warmup=warmup))
        result["actual_readback_ratio"] = (
            result["actual_wall_clock_fps"] / readback.abs_value if readback.abs_value > 0 else None
        )
        if result["frames"] == 0 or result["sdk_errors"]:
            result["status"] = "error"
    except Exception as exc:
        result["status"] = "skipped" if requested_fps is not None else "error"
        result["unsupported"] = requested_fps is not None
        result["error"] = safe_error(exc)
    return result


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    requested_values = args.fps if args.fps else [None]
    if args.fps and not write_enabled():
        raise SystemExit(f"--fps modifies camera frame-rate property; set {ENV_HARDWARE_WRITE_TEST}=1.")

    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "camera_index": args.camera_index,
        "duration_seconds": args.duration,
        "warmup_seconds": args.warmup,
        "host_note": args.host_note,
        "hardware_opt_in": os.environ.get(ENV_HARDWARE_TEST) == "1",
        "write_opt_in": write_enabled(),
        "os": platform.platform(),
        "python_version": sys.version,
        "flycapture2_library_version": list(get_api().get_library_version()),
        "results": [],
        "restore_failed": False,
        "restore_errors": [],
    }

    with Camera.open(index=args.camera_index) as camera:
        info = camera.get_camera_info()
        restorer = CameraStateRestorer(camera, grab_timeout_ms=args.grab_timeout_ms)
        restorer.snapshot()
        report["camera"] = camera_info_to_dict(info)
        report["camera_model"] = info.model_name
        report["serial"] = info.serial_number
        report["interface_type"] = info.interface_type
        report["original_frame_rate_property"] = property_to_dict(restorer.original_frame_rate)
        report["original_video_mode_and_frame_rate"] = list(restorer.original_video_mode_and_frame_rate)
        report["original_format7"] = format7_to_dict(restorer.original_format7)
        report["original_configuration"] = configuration_to_dict(restorer.original_configuration)
        report["original_trigger"] = trigger_to_dict(restorer.original_trigger)
        baseline_needs_frame_rate_enable = bool(
            not args.fps and restorer.original_frame_rate.abs_value > 0 and not restorer.original_frame_rate.on_off
        )
        needs_streaming_write = (
            restorer.original_trigger.on_off
            or restorer.original_configuration.grab_timeout != args.grab_timeout_ms
            or baseline_needs_frame_rate_enable
        )
        if needs_streaming_write and not write_enabled():
            report["results"].append(
                {
                    "requested_fps": None,
                    "status": "skipped",
                    "unsupported": False,
                    "error": {
                        "type": "WriteOptInRequired",
                        "message": (
                            "Current camera state requires disabling trigger or setting SDK grab timeout before "
                            f"safe rate measurement; set {ENV_HARDWARE_WRITE_TEST}=1."
                        ),
                    },
                }
            )
            return report, 0
        try:
            restorer.prepare_for_streaming()
            if baseline_needs_frame_rate_enable:
                requested_values = [float(restorer.original_frame_rate.abs_value)]
                report["baseline_frame_rate_source"] = "original_frame_rate_readback_enabled_for_measurement"
            for requested in requested_values:
                result = measure_once(
                    camera,
                    restorer,
                    requested_fps=requested,
                    duration=args.duration,
                    warmup=args.warmup,
                )
                video_mode, frame_rate_mode = camera.get_video_mode_and_frame_rate()
                format7 = camera.get_format7_configuration()
                result["video_mode"] = video_mode
                result["frame_rate_mode"] = frame_rate_mode
                result["format7"] = format7_to_dict(format7)
                report["results"].append(result)
        finally:
            restorer.restore()
            report["restore_failed"] = restorer.restore_failed
            report["restore_errors"] = restorer.restore_errors
            report["touched_state"] = sorted(set(restorer.touched))
            try:
                restored_frame_rate = camera.get_frame_rate()
                restored_configuration = camera.get_configuration()
                restored_trigger = camera.get_trigger_mode()
                report["restored_frame_rate_property"] = property_to_dict(restored_frame_rate)
                report["restored_configuration"] = configuration_to_dict(restored_configuration)
                report["restored_trigger"] = trigger_to_dict(restored_trigger)
                report["restore_verification"] = {
                    "configuration_matches_original": same_dataclass(
                        restored_configuration, restorer.original_configuration
                    ),
                    "trigger_matches_original": same_dataclass(restored_trigger, restorer.original_trigger),
                    "frame_rate_on_off_matches_original": (
                        restored_frame_rate.on_off == restorer.original_frame_rate.on_off
                    ),
                    "frame_rate_abs_control_matches_original": (
                        restored_frame_rate.abs_control == restorer.original_frame_rate.abs_control
                    ),
                    "frame_rate_abs_value_matches_original": (
                        abs(restored_frame_rate.abs_value - restorer.original_frame_rate.abs_value) < 1e-3
                    ),
                }
            except Exception as exc:
                report["restore_failed"] = True
                report["restore_errors"].append({"operation": "restore_verification", **safe_error(exc)})
    measurement_failed = any(result.get("status") == "error" for result in report["results"])
    return report, 1 if report["restore_failed"] or measurement_failed else 0


def emit_report(report: dict[str, Any], output: Path | None) -> None:
    payload = normalize_json(report)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_hardware_opt_in()
    report, returncode = build_report(args)
    emit_report(report, args.output)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
