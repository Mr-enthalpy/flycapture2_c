from __future__ import annotations

import argparse
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flycapture2_c import Camera, enumerate_cameras
from flycapture2_c._hardware_tools import (
    ENV_HARDWARE_TEST,
    ENV_HARDWARE_WRITE_TEST,
    HardwareSmokeConfig,
    attempt_reversible_property_write,
    camera_info_to_dict,
    collect_readonly_summary,
    frame_summary_from_frame,
    frame_summary_to_dict,
    property_snapshot_to_dict,
    read_frame_checked,
    read_short_sequence,
    sequence_summary_to_dict,
    write_property_report_to_dict,
)
from flycapture2_c.api import get_api
from flycapture2_c.dll import get_sdk_layout
from flycapture2_c.errors import (
    DLLLoadError,
    PropertyModeError,
    PropertyNotWritableError,
    PropertyOutOfRangeError,
    SDKNotFoundError,
    UnsupportedPropertyError,
)
from flycapture2_c.hardware_report import ErrorCategory, HardwareReport, HardwareReportError, format_human_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FlyCapture2 hardware smoke checks")
    parser.add_argument(
        "--level",
        default="readonly",
        choices=("readonly", "grab-one", "grab-sequence", "write-property"),
        help="smoke level to run",
    )
    parser.add_argument("--report-json", type=Path, default=None, help="write structured hardware report JSON")
    parser.add_argument("--save-frame", type=Path, default=None, help="save captured frame as .npy")
    parser.add_argument("--save-sequence-dir", type=Path, default=None, help="save captured sequence as .npy frames")
    parser.add_argument("--quiet", action="store_true", help="suppress human-readable console summary")
    parser.add_argument("--show-lifecycle", action="store_true", help="print Camera lifecycle state at each step")
    return parser.parse_args()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit(text: str, *, quiet: bool) -> None:
    if not quiet:
        print(text)


def add_error(
    report: HardwareReport,
    category: ErrorCategory,
    message: str,
    *,
    exception: Exception | None = None,
    details: dict[str, object] | None = None,
) -> None:
    report.errors.append(
        HardwareReportError(
            category=category.value,
            message=message,
            exception_type=type(exception).__name__ if exception is not None else None,
            details=details,
        )
    )


def classify_exception(exc: Exception) -> ErrorCategory:
    if isinstance(exc, (DLLLoadError, SDKNotFoundError)):
        return ErrorCategory.DLL_LOAD_ERROR
    if isinstance(exc, UnsupportedPropertyError):
        return ErrorCategory.PROPERTY_UNSUPPORTED
    if isinstance(exc, PropertyNotWritableError):
        return ErrorCategory.PROPERTY_NOT_WRITABLE
    if isinstance(exc, PropertyOutOfRangeError):
        return ErrorCategory.PROPERTY_OUT_OF_RANGE
    if isinstance(exc, PropertyModeError):
        return ErrorCategory.PROPERTY_UNSUPPORTED
    return ErrorCategory.UNKNOWN


def finalize_report(report: HardwareReport, *, report_json: Path | None) -> None:
    if report.finished_at is None:
        report.finished_at = now_utc_iso()
    if report.started_at and report.finished_at:
        started = datetime.fromisoformat(report.started_at)
        finished = datetime.fromisoformat(report.finished_at)
        report.duration_s = (finished - started).total_seconds()
    if report_json is not None:
        report.save_json_report(report_json)


def save_frame_array(frame_path: Path, array: np.ndarray) -> None:
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(frame_path, array)


def save_sequence_arrays(output_dir: Path, arrays: tuple[np.ndarray, ...]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, array in enumerate(arrays):
        np.save(output_dir / f"frame_{index:04d}.npy", array)


def populate_sdk_metadata(report: HardwareReport) -> None:
    try:
        report.sdk_root = str(get_sdk_layout().root)
    except SDKNotFoundError:
        report.sdk_root = None
    dll_path = getattr(get_api()._dll, "_flycapture2_path", None) if getattr(get_api(), "_dll", None) is not None else None
    report.dll_path = str(dll_path) if dll_path is not None else report.dll_path


def main() -> int:
    args = parse_args()
    report = HardwareReport(
        python_version=platform.python_version(),
        platform=platform.platform(),
        started_at=now_utc_iso(),
    )

    if os.environ.get(ENV_HARDWARE_TEST) != "1":
        emit(f"Hardware smoke skipped. Set {ENV_HARDWARE_TEST}=1 to enable.", quiet=args.quiet)
        finalize_report(report, report_json=args.report_json)
        return 0

    config = HardwareSmokeConfig.from_env()
    report.camera_index = config.camera_index

    camera: Camera | None = None
    exit_code = 0
    try:
        cameras = enumerate_cameras()
        populate_sdk_metadata(report)
        if not cameras:
            add_error(report, ErrorCategory.NO_CAMERA, "No cameras detected.")
            exit_code = 1
            return exit_code
        if config.camera_index < 0 or config.camera_index >= len(cameras):
            add_error(
                report,
                ErrorCategory.OPEN_FAILED,
                f"Configured camera index {config.camera_index} is out of range for {len(cameras)} camera(s).",
            )
            exit_code = 1
            return exit_code

        try:
            camera = Camera.open(index=config.camera_index)
        except Exception as exc:
            add_error(report, ErrorCategory.OPEN_FAILED, str(exc), exception=exc)
            exit_code = 1
            return exit_code

        if args.show_lifecycle:
            emit(
                f"lifecycle: opened={camera.is_open} "
                f"capturing={camera.is_capturing} "
                f"cleanup_errors={len(camera.cleanup_errors)}",
                quiet=args.quiet,
            )

        readonly = collect_readonly_summary(camera, camera_count=len(cameras))
        report.camera_info = camera_info_to_dict(readonly.camera_info)
        report.video_mode = readonly.video_mode
        report.frame_rate = readonly.frame_rate_mode
        report.property_summary = [property_snapshot_to_dict(item) for item in readonly.properties]

        if args.level == "readonly":
            return exit_code

        if args.level == "grab-one":
            try:
                camera.start()
            except Exception as exc:
                add_error(report, ErrorCategory.START_CAPTURE_FAILED, str(exc), exception=exc)
                exit_code = 1
                return exit_code
            if args.show_lifecycle:
                emit(
                    f"lifecycle: opened={camera.is_open} "
                    f"capturing={camera.is_capturing}",
                    quiet=args.quiet,
                )
            try:
                frame, elapsed_ms = read_frame_checked(camera, timeout_ms=config.capture_timeout_ms)
                summary = frame_summary_from_frame(frame, elapsed_ms=elapsed_ms)
                report.capture_summary = frame_summary_to_dict(summary)
                if args.save_frame is not None:
                    save_frame_array(args.save_frame, frame.array)
            except Exception as exc:
                add_error(report, ErrorCategory.READ_FRAME_FAILED, str(exc), exception=exc)
                exit_code = 1
            finally:
                try:
                    camera.stop()
                except Exception as exc:
                    add_error(report, ErrorCategory.STOP_CAPTURE_FAILED, str(exc), exception=exc)
                    exit_code = 1
                if args.show_lifecycle:
                    emit(
                        f"lifecycle: stop_called capturing={camera.is_capturing} "
                        f"cleanup_errors={len(camera.cleanup_errors)}",
                        quiet=args.quiet,
                    )
            return exit_code

        if args.level == "grab-sequence":
            try:
                camera.start()
            except Exception as exc:
                add_error(report, ErrorCategory.START_CAPTURE_FAILED, str(exc), exception=exc)
                exit_code = 1
                return exit_code
            if args.show_lifecycle:
                emit(
                    f"lifecycle: opened={camera.is_open} "
                    f"capturing={camera.is_capturing}",
                    quiet=args.quiet,
                )
            try:
                result = read_short_sequence(
                    camera,
                    frame_count=config.frame_count,
                    timeout_ms=config.capture_timeout_ms,
                    collect_arrays=args.save_sequence_dir is not None,
                )
                report.sequence_summary = sequence_summary_to_dict(result.summary)
                if args.save_sequence_dir is not None:
                    save_sequence_arrays(args.save_sequence_dir, result.frame_arrays)
                if result.summary.errors:
                    for item in result.summary.errors:
                        add_error(report, ErrorCategory.READ_FRAME_FAILED, item)
                    exit_code = 1
                if result.summary.acquired_frame_count != config.frame_count:
                    exit_code = 1
                if not result.summary.shape_stable or not result.summary.dtype_stable or not result.summary.pixel_format_stable:
                    exit_code = 1
            finally:
                try:
                    camera.stop()
                except Exception as exc:
                    add_error(report, ErrorCategory.STOP_CAPTURE_FAILED, str(exc), exception=exc)
                    exit_code = 1
                if args.show_lifecycle:
                    emit(
                        f"lifecycle: stop_called capturing={camera.is_capturing} "
                        f"cleanup_errors={len(camera.cleanup_errors)}",
                        quiet=args.quiet,
                    )
            return exit_code

        if args.level == "write-property":
            if os.environ.get(ENV_HARDWARE_WRITE_TEST) != "1":
                return exit_code
            try:
                write_report = attempt_reversible_property_write(camera)
            except Exception as exc:
                add_error(report, classify_exception(exc), str(exc), exception=exc)
                exit_code = 1
                return exit_code
            if write_report is not None:
                report.write_property_summary = write_property_report_to_dict(write_report)
            return exit_code
        return exit_code
    except Exception as exc:
        add_error(report, classify_exception(exc), str(exc), exception=exc)
        return 1
    finally:
        if camera is not None:
            try:
                camera.close()
            except Exception as exc:
                add_error(report, ErrorCategory.STOP_CAPTURE_FAILED, str(exc), exception=exc)
                exit_code = 1
            if args.show_lifecycle:
                emit(
                    f"lifecycle: close_called opened={camera.is_open} "
                    f"capturing={camera.is_capturing} "
                    f"cleanup_errors={len(camera.cleanup_errors)}",
                    quiet=args.quiet,
                )
        populate_sdk_metadata(report)
        finalize_report(report, report_json=args.report_json)
        emit(format_human_report(report), quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
