from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ErrorCategory(str, Enum):
    DLL_LOAD_ERROR = "DLL_LOAD_ERROR"
    NO_CAMERA = "NO_CAMERA"
    OPEN_FAILED = "OPEN_FAILED"
    START_CAPTURE_FAILED = "START_CAPTURE_FAILED"
    READ_FRAME_FAILED = "READ_FRAME_FAILED"
    STOP_CAPTURE_FAILED = "STOP_CAPTURE_FAILED"
    PROPERTY_UNSUPPORTED = "PROPERTY_UNSUPPORTED"
    PROPERTY_NOT_WRITABLE = "PROPERTY_NOT_WRITABLE"
    PROPERTY_OUT_OF_RANGE = "PROPERTY_OUT_OF_RANGE"
    UNKNOWN = "UNKNOWN"


@dataclass
class HardwareReportError:
    category: str
    message: str
    exception_type: str | None = None
    details: dict[str, Any] | None = None


@dataclass
class HardwareReport:
    sdk_root: str | None = None
    dll_path: str | None = None
    python_version: str | None = None
    platform: str | None = None
    camera_index: int | None = None
    camera_info: dict[str, Any] | None = None
    video_mode: int | None = None
    frame_rate: int | None = None
    property_summary: list[dict[str, Any]] = field(default_factory=list)
    capture_summary: dict[str, Any] | None = None
    sequence_summary: dict[str, Any] | None = None
    write_property_summary: dict[str, Any] | None = None
    errors: list[HardwareReportError] = field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None
    duration_s: float | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return _normalize_json_value(asdict(self))

    def save_json_report(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_json_dict(), indent=2, sort_keys=False), encoding="utf-8")
        return output_path


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return _normalize_json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json_value(item) for item in value]
    return value


def format_human_report(report: HardwareReport) -> str:
    lines: list[str] = []

    def add_section(title: str, content_lines: list[str]) -> None:
        lines.append(f"[{title}]")
        lines.extend(content_lines if content_lines else ["status=not-run"])

    add_section(
        "SDK",
        [
            f"sdk_root={report.sdk_root or '-'}",
            f"dll_path={report.dll_path or '-'}",
            f"python_version={report.python_version or '-'}",
            f"platform={report.platform or '-'}",
            f"started_at={report.started_at or '-'}",
            f"finished_at={report.finished_at or '-'}",
            f"duration_s={_format_float(report.duration_s)}",
        ],
    )

    camera_lines = [
        f"camera_index={report.camera_index if report.camera_index is not None else '-'}",
    ]
    if report.camera_info:
        for key in (
            "serial_number",
            "model_name",
            "vendor_name",
            "sensor_info",
            "sensor_resolution",
            "firmware_version",
            "interface_type",
            "is_color_camera",
        ):
            camera_lines.append(f"{key}={_format_scalar(report.camera_info.get(key))}")
    else:
        camera_lines.append("status=not-run")
    add_section("Camera", camera_lines)

    add_section(
        "Video",
        [
            f"video_mode={_format_scalar(report.video_mode)}",
            f"frame_rate={_format_scalar(report.frame_rate)}",
        ],
    )

    property_lines: list[str] = []
    if report.property_summary:
        for item in report.property_summary:
            property_lines.append(
                "property="
                f"{item.get('property_type', '-')}, "
                f"present={_format_scalar(item.get('present'))}, "
                f"writable={_format_scalar(item.get('writable'))}, "
                f"auto_supported={_format_scalar(item.get('auto_supported'))}, "
                f"manual_supported={_format_scalar(item.get('manual_supported'))}, "
                f"abs_supported={_format_scalar(item.get('abs_val_supported'))}, "
                f"range_abs={_format_scalar(item.get('abs_range'))}, "
                f"units={_format_scalar(item.get('unit_abbr') or item.get('units'))}, "
                f"value_abs={_format_scalar(item.get('value_abs'))}, "
                f"auto={_format_scalar(item.get('value_auto_manual_mode'))}"
            )
    add_section("Properties", property_lines)

    add_section("Capture", _format_mapping(report.capture_summary, _capture_field_order()))
    add_section("Sequence", _format_mapping(report.sequence_summary, _sequence_field_order()))
    add_section("WriteProperty", _format_mapping(report.write_property_summary, _write_property_field_order()))

    error_lines: list[str] = [f"count={len(report.errors)}"]
    for item in report.errors:
        error_lines.append(
            f"category={item.category}, exception_type={item.exception_type or '-'}, message={item.message}"
        )
    add_section("Errors", error_lines)
    return "\n".join(lines)


def _capture_field_order() -> tuple[str, ...]:
    return (
        "shape",
        "dtype",
        "pixel_format",
        "width",
        "height",
        "stride",
        "min",
        "max",
        "mean",
        "std",
        "finite",
        "own_data",
        "elapsed_ms",
        "warnings",
    )


def _sequence_field_order() -> tuple[str, ...]:
    return (
        "requested_frame_count",
        "acquired_frame_count",
        "total_duration_s",
        "effective_fps",
        "shape",
        "dtype",
        "pixel_format",
        "stride",
        "shape_stable",
        "dtype_stable",
        "pixel_format_stable",
        "per_frame_mean_range",
        "per_frame_std_range",
        "warnings",
        "errors",
    )


def _write_property_field_order() -> tuple[str, ...]:
    return (
        "property_type",
        "requested_value",
        "before_abs_value",
        "written_abs_value",
        "restored_abs_value",
        "before_auto_manual_mode",
        "restored_auto_manual_mode",
    )


def _format_mapping(mapping: dict[str, Any] | None, field_order: tuple[str, ...]) -> list[str]:
    if not mapping:
        return []
    return [f"{field_name}={_format_scalar(mapping.get(field_name))}" for field_name in field_order]


def _format_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6f}"


def _format_scalar(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_format_scalar(item) for item in value) + "]"
    return str(value)
