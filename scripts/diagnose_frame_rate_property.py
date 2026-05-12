from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flycapture2_c import Camera  # noqa: E402
from flycapture2_c._hardware_tools import ENV_CAMERA_INDEX, ENV_HARDWARE_TEST  # noqa: E402
from flycapture2_c.properties import PropertyType  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print readonly FRAME_RATE property readback fields.")
    parser.add_argument("--camera-index", type=int, default=int(os.environ.get(ENV_CAMERA_INDEX, "0")))
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser.parse_args(argv)


def require_hardware_opt_in() -> None:
    if os.environ.get(ENV_HARDWARE_TEST) != "1":
        raise SystemExit(f"Refusing to touch hardware. Set {ENV_HARDWARE_TEST}=1.")


def build_frame_rate_property_diagnostic(camera: Any) -> dict[str, Any]:
    info = camera.get_property_info(PropertyType.FRAME_RATE)
    value = camera.get_property(PropertyType.FRAME_RATE) if info.present and info.read_out_supported else None
    payload: dict[str, Any] = {
        "property": PropertyType.FRAME_RATE.name,
        "present": info.present,
        "abs_val_supported": info.abs_val_supported,
        "read_out_supported": info.read_out_supported,
        "manual_supported": info.manual_supported,
        "auto_supported": info.auto_supported,
        "min_value": info.min_value,
        "max_value": info.max_value,
        "abs_min": info.abs_min,
        "abs_max": info.abs_max,
        "units": info.units,
        "unit_abbr": info.unit_abbr,
        "display_range": list(info.display_range),
        "readback_policy": "abs_value" if info.abs_val_supported else "value_a",
    }
    if value is None:
        payload.update(
            {
                "abs_control": None,
                "auto_manual_mode": None,
                "value_a": None,
                "value_b": None,
                "abs_value": None,
                "display_value": None,
            }
        )
        return payload

    payload.update(
        {
            "abs_control": value.abs_control,
            "auto_manual_mode": value.auto_manual_mode,
            "value_a": value.value_a,
            "value_b": value.value_b,
            "abs_value": value.abs_value,
            "display_value": camera.get_property_display_value(PropertyType.FRAME_RATE),
        }
    )
    return payload


def format_diagnostic(payload: dict[str, Any]) -> str:
    keys = (
        "property",
        "present",
        "abs_val_supported",
        "read_out_supported",
        "manual_supported",
        "auto_supported",
        "min_value",
        "max_value",
        "abs_min",
        "abs_max",
        "units",
        "unit_abbr",
        "abs_control",
        "auto_manual_mode",
        "value_a",
        "value_b",
        "abs_value",
        "display_value",
        "display_range",
        "readback_policy",
    )
    return "\n".join(f"{key}: {payload[key]}" for key in keys)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_hardware_opt_in()
    try:
        with Camera.open(index=args.camera_index) as camera:
            payload = build_frame_rate_property_diagnostic(camera)
    except Exception as exc:
        error = {"status": "error", "type": type(exc).__name__, "message": str(exc)}
        if args.json:
            print(json.dumps(error, indent=2, sort_keys=True))
        else:
            print(f"error: {error['type']}: {error['message']}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_diagnostic(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
