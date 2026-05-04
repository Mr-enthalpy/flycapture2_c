from __future__ import annotations

import os
from dataclasses import dataclass
from time import perf_counter

import numpy as np

from .camera import Camera, CameraInfo
from .errors import FlyCapture2Error
from .image import ImageFrame
from .pixel_format import numpy_dtype
from .properties import CameraPropertyInfo, CameraPropertyValue, PropertyType, PropertyWritePolicy

ENV_HARDWARE_TEST = "FLYCAPTURE2_HARDWARE_TEST"
ENV_HARDWARE_WRITE_TEST = "FLYCAPTURE2_HARDWARE_WRITE_TEST"
ENV_CAMERA_INDEX = "FLYCAPTURE2_CAMERA_INDEX"
ENV_FRAME_COUNT = "FLYCAPTURE2_FRAME_COUNT"
ENV_CAPTURE_TIMEOUT_MS = "FLYCAPTURE2_CAPTURE_TIMEOUT_MS"

PROPERTY_ORDER = (
    PropertyType.AUTO_EXPOSURE,
    PropertyType.SHUTTER,
    PropertyType.GAIN,
    PropertyType.FRAME_RATE,
)

WRITE_CANDIDATE_ORDER = (
    PropertyType.GAIN,
    PropertyType.SHUTTER,
    PropertyType.FRAME_RATE,
    PropertyType.AUTO_EXPOSURE,
)


@dataclass(frozen=True)
class HardwareSmokeConfig:
    camera_index: int = 0
    frame_count: int = 30
    capture_timeout_ms: int | None = None

    @classmethod
    def from_env(cls) -> "HardwareSmokeConfig":
        timeout_value = os.environ.get(ENV_CAPTURE_TIMEOUT_MS)
        return cls(
            camera_index=int(os.environ.get(ENV_CAMERA_INDEX, "0")),
            frame_count=int(os.environ.get(ENV_FRAME_COUNT, "30")),
            capture_timeout_ms=int(timeout_value) if timeout_value else None,
        )


@dataclass(frozen=True)
class PropertySnapshot:
    property_type: PropertyType
    info: CameraPropertyInfo
    value: CameraPropertyValue | None


@dataclass(frozen=True)
class ReadonlySummary:
    camera_count: int
    camera_info: CameraInfo
    video_mode: int
    frame_rate_mode: int
    properties: tuple[PropertySnapshot, ...]


@dataclass(frozen=True)
class FrameSummary:
    width: int
    height: int
    shape: tuple[int, ...]
    dtype: str
    pixel_format: str
    stride: int
    own_data: bool
    min_value: float
    max_value: float
    mean_value: float
    std_value: float
    finite: bool
    elapsed_ms: float
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SequenceSummary:
    requested_frame_count: int
    acquired_frame_count: int
    shape: tuple[int, ...]
    dtype: str
    pixel_format: str
    stride: int
    min_value: float
    max_value: float
    mean_value: float
    total_duration_s: float
    effective_fps: float
    shape_stable: bool
    dtype_stable: bool
    pixel_format_stable: bool
    per_frame_mean_range: tuple[float, float]
    per_frame_std_range: tuple[float, float]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def frame_count(self) -> int:
        return self.acquired_frame_count

    @property
    def elapsed_s(self) -> float:
        return self.total_duration_s

    @property
    def fps_estimate(self) -> float:
        return self.effective_fps


@dataclass(frozen=True)
class FrameCaptureResult:
    summary: FrameSummary
    frame_array: np.ndarray


@dataclass(frozen=True)
class SequenceCaptureResult:
    summary: SequenceSummary
    frame_arrays: tuple[np.ndarray, ...]


@dataclass(frozen=True)
class ReversiblePropertyWriteReport:
    property_type: PropertyType
    before: CameraPropertyValue
    written: CameraPropertyValue
    restored: CameraPropertyValue
    requested_value: float


def collect_readonly_summary(camera: Camera, *, camera_count: int) -> ReadonlySummary:
    camera_info = camera.get_camera_info()
    video_mode, frame_rate_mode = camera.get_video_mode_and_frame_rate()
    properties = []
    for property_type in PROPERTY_ORDER:
        info = camera.get_property_info(property_type)
        value = camera.get_property(property_type) if info.present and info.read_out_supported else None
        properties.append(PropertySnapshot(property_type=property_type, info=info, value=value))
    return ReadonlySummary(
        camera_count=camera_count,
        camera_info=camera_info,
        video_mode=video_mode,
        frame_rate_mode=frame_rate_mode,
        properties=tuple(properties),
    )


def read_frame_checked(camera: Camera, *, timeout_ms: int | None = None) -> tuple[ImageFrame, float]:
    started_at = perf_counter()
    frame = camera.read_frame_with_info()
    elapsed_ms = (perf_counter() - started_at) * 1000.0
    validate_frame(frame)
    if timeout_ms is not None and elapsed_ms > timeout_ms:
        raise TimeoutError(f"Frame read exceeded timeout: {elapsed_ms:.2f} ms > {timeout_ms} ms")
    return frame, elapsed_ms


def validate_frame(frame: ImageFrame) -> None:
    if frame.array.shape != (frame.height, frame.width):
        raise AssertionError(f"Frame shape mismatch: {frame.array.shape} vs ({frame.height}, {frame.width})")
    if frame.array.dtype != numpy_dtype(frame.pixel_format):
        raise AssertionError(f"Frame dtype mismatch: {frame.array.dtype} vs {numpy_dtype(frame.pixel_format)}")
    if frame.width * frame.array.dtype.itemsize > frame.stride:
        raise AssertionError(
            f"Frame stride is smaller than required row size: stride={frame.stride}, width={frame.width}, dtype={frame.array.dtype}"
        )
    if not frame.array.flags["OWNDATA"]:
        raise AssertionError("Frame array must own its memory.")
    if not np.isfinite(frame.array).all():
        raise AssertionError("Frame contains non-finite values.")


def _frame_warnings(array: np.ndarray) -> tuple[str, ...]:
    warnings: list[str] = []
    min_value = float(array.min())
    max_value = float(array.max())
    std_value = float(array.std())
    if min_value == 0.0 and max_value == 0.0:
        warnings.append("ALL_ZERO")
    if np.issubdtype(array.dtype, np.integer):
        dtype_max = float(np.iinfo(array.dtype).max)
        if min_value == dtype_max and max_value == dtype_max:
            warnings.append("ALL_SATURATED")
    if std_value < 1e-6:
        warnings.append("LOW_STD")
    return tuple(warnings)


def frame_summary_from_frame(frame: ImageFrame, *, elapsed_ms: float) -> FrameSummary:
    validate_frame(frame)
    array = frame.array
    return FrameSummary(
        width=frame.width,
        height=frame.height,
        shape=array.shape,
        dtype=str(array.dtype),
        pixel_format=frame.pixel_format.name,
        stride=frame.stride,
        own_data=bool(array.flags["OWNDATA"]),
        min_value=float(array.min()),
        max_value=float(array.max()),
        mean_value=float(array.mean()),
        std_value=float(array.std()),
        finite=bool(np.isfinite(array).all()),
        elapsed_ms=elapsed_ms,
        warnings=_frame_warnings(array),
    )


def capture_one_frame_result(camera: Camera, *, timeout_ms: int | None = None) -> FrameCaptureResult:
    camera.start()
    try:
        frame, elapsed_ms = read_frame_checked(camera, timeout_ms=timeout_ms)
        return FrameCaptureResult(summary=frame_summary_from_frame(frame, elapsed_ms=elapsed_ms), frame_array=frame.array)
    finally:
        camera.stop()


def capture_one_frame(camera: Camera, *, timeout_ms: int | None = None) -> FrameSummary:
    return capture_one_frame_result(camera, timeout_ms=timeout_ms).summary


def read_short_sequence(
    camera: Camera,
    *,
    frame_count: int,
    timeout_ms: int | None = None,
    collect_arrays: bool = False,
) -> SequenceCaptureResult:
    if frame_count <= 0:
        raise ValueError("frame_count must be positive")

    started_at = perf_counter()
    arrays: list[np.ndarray] = []
    errors: list[str] = []
    means: list[float] = []
    stds: list[float] = []
    mins: list[float] = []
    maxs: list[float] = []
    warnings: list[str] = []
    shape: tuple[int, ...] = ()
    dtype = "-"
    pixel_format = "-"
    stride = 0
    shape_stable = True
    dtype_stable = True
    pixel_format_stable = True

    for index in range(frame_count):
        try:
            frame, _elapsed_ms = read_frame_checked(camera, timeout_ms=timeout_ms)
        except Exception as exc:
            errors.append(f"frame_index={index}: {exc}")
            break

        if index == 0:
            shape = frame.array.shape
            dtype = str(frame.array.dtype)
            pixel_format = frame.pixel_format.name
            stride = frame.stride
        else:
            shape_stable = shape_stable and frame.array.shape == shape
            dtype_stable = dtype_stable and str(frame.array.dtype) == dtype
            pixel_format_stable = pixel_format_stable and frame.pixel_format.name == pixel_format
        means.append(float(frame.array.mean()))
        stds.append(float(frame.array.std()))
        mins.append(float(frame.array.min()))
        maxs.append(float(frame.array.max()))
        warnings.extend(item for item in _frame_warnings(frame.array) if item not in warnings)
        if collect_arrays:
            arrays.append(frame.array.copy())

    elapsed_s = perf_counter() - started_at
    acquired_frame_count = len(means)
    if acquired_frame_count == 0:
        summary = SequenceSummary(
            requested_frame_count=frame_count,
            acquired_frame_count=0,
            shape=(),
            dtype="-",
            pixel_format="-",
            stride=0,
            min_value=float("nan"),
            max_value=float("nan"),
            mean_value=float("nan"),
            total_duration_s=elapsed_s,
            effective_fps=0.0,
            shape_stable=True,
            dtype_stable=True,
            pixel_format_stable=True,
            per_frame_mean_range=(float("nan"), float("nan")),
            per_frame_std_range=(float("nan"), float("nan")),
            warnings=tuple(warnings),
            errors=tuple(errors),
        )
        return SequenceCaptureResult(summary=summary, frame_arrays=tuple(arrays))

    summary = SequenceSummary(
        requested_frame_count=frame_count,
        acquired_frame_count=acquired_frame_count,
        shape=shape,
        dtype=dtype,
        pixel_format=pixel_format,
        stride=stride,
        min_value=min(mins),
        max_value=max(maxs),
        mean_value=sum(means) / acquired_frame_count,
        total_duration_s=elapsed_s,
        effective_fps=(acquired_frame_count / elapsed_s) if elapsed_s > 0 else float("inf"),
        shape_stable=shape_stable,
        dtype_stable=dtype_stable,
        pixel_format_stable=pixel_format_stable,
        per_frame_mean_range=(min(means), max(means)),
        per_frame_std_range=(min(stds), max(stds)),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
    return SequenceCaptureResult(summary=summary, frame_arrays=tuple(arrays))


def capture_short_sequence(
    camera: Camera,
    *,
    frame_count: int,
    timeout_ms: int | None = None,
) -> SequenceSummary:
    camera.start()
    try:
        result = read_short_sequence(camera, frame_count=frame_count, timeout_ms=timeout_ms, collect_arrays=False)
    finally:
        camera.stop()
    if result.summary.errors:
        raise AssertionError("; ".join(result.summary.errors))
    if result.summary.acquired_frame_count != frame_count:
        raise AssertionError(
            f"Requested {frame_count} frames but acquired {result.summary.acquired_frame_count}."
        )
    if not result.summary.shape_stable or not result.summary.dtype_stable or not result.summary.pixel_format_stable:
        raise AssertionError("Frame shape/dtype/pixel format changed during sequence.")
    return result.summary


def choose_safe_absolute_value(prop_info: CameraPropertyInfo, current_value: CameraPropertyValue) -> float | None:
    if not prop_info.abs_val_supported:
        return None
    span = prop_info.abs_max - prop_info.abs_min
    if span <= 0:
        return None

    current = float(current_value.abs_value)
    if current < prop_info.abs_min or current > prop_info.abs_max:
        current = (prop_info.abs_min + prop_info.abs_max) / 2.0

    delta = max(span * 0.05, 0.01)
    increase = min(current + delta, prop_info.abs_max)
    decrease = max(current - delta, prop_info.abs_min)
    epsilon = max(span * 0.001, 1e-6)

    if abs(increase - current) > epsilon:
        return increase
    if abs(decrease - current) > epsilon:
        return decrease
    midpoint = (prop_info.abs_min + prop_info.abs_max) / 2.0
    if abs(midpoint - current) > epsilon:
        return midpoint
    return None


def restore_property_value(camera: Camera, property_type: PropertyType, value: CameraPropertyValue) -> CameraPropertyValue:
    return camera.set_property(
        property_type,
        auto_manual_mode=value.auto_manual_mode,
        on_off=value.on_off,
        abs_control=value.abs_control,
        one_push=value.one_push,
        value_a=None if value.abs_control else value.value_a,
        value_b=None if value.abs_control else value.value_b,
        abs_value=value.abs_value if value.abs_control else None,
        policy=PropertyWritePolicy.RAW,
    )


def attempt_reversible_property_write(camera: Camera) -> ReversiblePropertyWriteReport | None:
    for property_type in WRITE_CANDIDATE_ORDER:
        prop_info = camera.get_property_info(property_type)
        if not prop_info.present:
            continue
        if not prop_info.writable:
            continue
        if not prop_info.manual_supported:
            continue
        if not prop_info.abs_val_supported:
            continue
        current = camera.get_property(property_type)
        safe_value = choose_safe_absolute_value(prop_info, current)
        if safe_value is None:
            continue

        written: CameraPropertyValue | None = None
        restored: CameraPropertyValue | None = None
        try:
            if property_type == PropertyType.AUTO_EXPOSURE:
                written = camera.set_exposure(safe_value, auto=False)
            elif property_type == PropertyType.SHUTTER:
                written = camera.set_shutter(safe_value, auto=False)
            elif property_type == PropertyType.GAIN:
                written = camera.set_gain(safe_value, auto=False)
            elif property_type == PropertyType.FRAME_RATE:
                written = camera.set_frame_rate(safe_value, auto=False)
            else:
                continue
            restored = restore_property_value(camera, property_type, current)
        except Exception:
            try:
                if written is not None:
                    restore_property_value(camera, property_type, current)
            except Exception:
                pass
            raise
        return ReversiblePropertyWriteReport(
            property_type=property_type,
            before=current,
            written=written,
            restored=restored,
            requested_value=safe_value,
        )
    return None


def format_camera_info(info: CameraInfo) -> str:
    return "\n".join(
        [
            f"serial={info.serial_number}",
            f"model={info.model_name}",
            f"vendor={info.vendor_name}",
            f"sensor={info.sensor_info}",
            f"resolution={info.sensor_resolution}",
            f"firmware={info.firmware_version}",
            f"interface_type={info.interface_type}",
            f"is_color_camera={info.is_color_camera}",
        ]
    )


def format_property_snapshot(snapshot: PropertySnapshot) -> str:
    info = snapshot.info
    value = snapshot.value
    if value is None:
        value_summary = "value=<unavailable>"
    else:
        value_summary = (
            f"value_abs={value.abs_value:.4f}, auto={value.auto_manual_mode}, "
            f"on={value.on_off}, abs_control={value.abs_control}"
        )
    return (
        f"{snapshot.property_type.name}: present={info.present}, writable={info.writable}, "
        f"auto_supported={info.auto_supported}, manual_supported={info.manual_supported}, "
        f"abs_supported={info.abs_val_supported}, range=[{info.abs_min:.4f}, {info.abs_max:.4f}], "
        f"units={info.unit_abbr or info.units or '-'}, {value_summary}"
    )


def format_frame_summary(summary: FrameSummary) -> str:
    return (
        f"shape={summary.shape}, dtype={summary.dtype}, pixel_format={summary.pixel_format}, stride={summary.stride}, "
        f"own_data={summary.own_data}, min={summary.min_value:.3f}, max={summary.max_value:.3f}, "
        f"mean={summary.mean_value:.3f}, std={summary.std_value:.3f}, finite={summary.finite}, "
        f"read_ms={summary.elapsed_ms:.2f}, warnings={list(summary.warnings)}"
    )


def format_sequence_summary(summary: SequenceSummary) -> str:
    return (
        f"requested_frame_count={summary.requested_frame_count}, acquired_frame_count={summary.acquired_frame_count}, "
        f"shape={summary.shape}, dtype={summary.dtype}, pixel_format={summary.pixel_format}, stride={summary.stride}, "
        f"min={summary.min_value:.3f}, max={summary.max_value:.3f}, mean={summary.mean_value:.3f}, "
        f"total_duration_s={summary.total_duration_s:.3f}, effective_fps={summary.effective_fps:.2f}, "
        f"shape_stable={summary.shape_stable}, dtype_stable={summary.dtype_stable}, "
        f"pixel_format_stable={summary.pixel_format_stable}, per_frame_mean_range={summary.per_frame_mean_range}, "
        f"per_frame_std_range={summary.per_frame_std_range}, warnings={list(summary.warnings)}, errors={list(summary.errors)}"
    )


def camera_info_to_dict(info: CameraInfo) -> dict[str, object]:
    return {
        "serial_number": info.serial_number,
        "interface_type": info.interface_type,
        "driver_type": info.driver_type,
        "is_color_camera": info.is_color_camera,
        "model_name": info.model_name,
        "vendor_name": info.vendor_name,
        "sensor_info": info.sensor_info,
        "sensor_resolution": info.sensor_resolution,
        "driver_name": info.driver_name,
        "firmware_version": info.firmware_version,
        "firmware_build_time": info.firmware_build_time,
        "maximum_bus_speed": info.maximum_bus_speed,
        "bayer_tile_format": info.bayer_tile_format,
        "pcie_bus_speed": info.pcie_bus_speed,
        "node_number": info.node_number,
        "bus_number": info.bus_number,
        "iidc_version": info.iidc_version,
        "config_rom_keyword": info.config_rom_keyword,
        "gige_major_version": info.gige_major_version,
        "gige_minor_version": info.gige_minor_version,
        "user_defined_name": info.user_defined_name,
        "xml_url_1": info.xml_url_1,
        "xml_url_2": info.xml_url_2,
        "mac_address": list(info.mac_address),
        "ip_address": list(info.ip_address),
        "subnet_mask": list(info.subnet_mask),
        "default_gateway": list(info.default_gateway),
        "ccp_status": info.ccp_status,
        "application_ip_address": info.application_ip_address,
        "application_port": info.application_port,
    }


def property_snapshot_to_dict(snapshot: PropertySnapshot) -> dict[str, object]:
    payload = {
        "property_type": snapshot.property_type.name,
        "present": snapshot.info.present,
        "writable": snapshot.info.writable,
        "auto_supported": snapshot.info.auto_supported,
        "manual_supported": snapshot.info.manual_supported,
        "on_off_supported": snapshot.info.on_off_supported,
        "one_push_supported": snapshot.info.one_push_supported,
        "abs_val_supported": snapshot.info.abs_val_supported,
        "read_out_supported": snapshot.info.read_out_supported,
        "min_value": snapshot.info.min_value,
        "max_value": snapshot.info.max_value,
        "abs_range": [snapshot.info.abs_min, snapshot.info.abs_max],
        "units": snapshot.info.units,
        "unit_abbr": snapshot.info.unit_abbr,
        "value_abs": None,
        "value_auto_manual_mode": None,
        "value_on_off": None,
        "value_abs_control": None,
    }
    if snapshot.value is not None:
        payload.update(
            {
                "value_abs": snapshot.value.abs_value,
                "value_auto_manual_mode": snapshot.value.auto_manual_mode,
                "value_on_off": snapshot.value.on_off,
                "value_abs_control": snapshot.value.abs_control,
            }
        )
    return payload


def frame_summary_to_dict(summary: FrameSummary) -> dict[str, object]:
    return {
        "shape": list(summary.shape),
        "dtype": summary.dtype,
        "pixel_format": summary.pixel_format,
        "width": summary.width,
        "height": summary.height,
        "stride": summary.stride,
        "min": summary.min_value,
        "max": summary.max_value,
        "mean": summary.mean_value,
        "std": summary.std_value,
        "finite": summary.finite,
        "own_data": summary.own_data,
        "elapsed_ms": summary.elapsed_ms,
        "warnings": list(summary.warnings),
    }


def sequence_summary_to_dict(summary: SequenceSummary) -> dict[str, object]:
    return {
        "requested_frame_count": summary.requested_frame_count,
        "acquired_frame_count": summary.acquired_frame_count,
        "shape": list(summary.shape),
        "dtype": summary.dtype,
        "pixel_format": summary.pixel_format,
        "stride": summary.stride,
        "min": summary.min_value,
        "max": summary.max_value,
        "mean": summary.mean_value,
        "total_duration_s": summary.total_duration_s,
        "effective_fps": summary.effective_fps,
        "shape_stable": summary.shape_stable,
        "dtype_stable": summary.dtype_stable,
        "pixel_format_stable": summary.pixel_format_stable,
        "per_frame_mean_range": list(summary.per_frame_mean_range),
        "per_frame_std_range": list(summary.per_frame_std_range),
        "warnings": list(summary.warnings),
        "errors": list(summary.errors),
    }


def write_property_report_to_dict(report: ReversiblePropertyWriteReport) -> dict[str, object]:
    return {
        "property_type": report.property_type.name,
        "requested_value": report.requested_value,
        "before_abs_value": report.before.abs_value,
        "written_abs_value": report.written.abs_value,
        "restored_abs_value": report.restored.abs_value,
        "before_auto_manual_mode": report.before.auto_manual_mode,
        "restored_auto_manual_mode": report.restored.auto_manual_mode,
    }
