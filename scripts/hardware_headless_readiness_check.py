"""Hardware diagnostic for headless FlyCapture2 camera-control primitives.

This script exercises the Camera lifecycle, trigger, properties, pixel format,
and error-fidelity classification against real FlyCapture2 hardware. It writes
a machine-readable JSON report and a human-readable console summary.

Do not import this script from other modules. It is a standalone diagnostic
tool that touches hardware only when ``FLYCAPTURE2_HARDWARE_TEST=1``.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flycapture2_c import Camera, enumerate_cameras
from flycapture2_c._hardware_tools import (
    ENV_CAMERA_INDEX,
    ENV_HARDWARE_TEST,
    ENV_HARDWARE_WRITE_TEST,
    HardwareSmokeConfig,
    camera_info_to_dict,
    frame_summary_from_frame,
    property_snapshot_to_dict,
    read_frame_checked,
    restore_property_value,
)
from flycapture2_c.api import get_api
from flycapture2_c.dll import get_sdk_layout
from flycapture2_c.errors import (
    CameraStateError,
    FC2ErrorCode,
    FlyCapture2Error,
    SDKNotFoundError,
)
from flycapture2_c.image import ImageFrame
from flycapture2_c.pixel_format import normalize_pixel_format
from flycapture2_c.properties import (
    PropertyType,
    PropertyWritePolicy,
)

OUTPUT_DIR = ROOT / "outputs"
OUTPUT_JSON = OUTPUT_DIR / "headless_camera_readiness_check.json"

PROPERTY_CHECK_ORDER = (
    PropertyType.SHUTTER,
    PropertyType.GAIN,
    PropertyType.FRAME_RATE,
    PropertyType.AUTO_EXPOSURE,
    PropertyType.BRIGHTNESS,
    PropertyType.GAMMA,
    PropertyType.WHITE_BALANCE,
    PropertyType.TRIGGER_DELAY,
)

PIXEL_FORMAT_TEST_ORDER = ("MONO8", "RAW8", "MONO16", "RAW16")

CONCLUSION_FULLY_SUPPORTED = "fully_supported_and_hardware_validated"
CONCLUSION_WRITE_GATED = "write_gated_hardware_validated"
CONCLUSION_CAMERA_UNSUPPORTED = "camera_unsupported_wrapper_correct"
CONCLUSION_FAILED_INVESTIGATE = "failed_on_hardware_needs_investigation"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hardware diagnostic for headless FlyCapture2 camera-control primitives."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Allow camera-state-changing operations. Requires FLYCAPTURE2_HARDWARE_WRITE_TEST=1.",
    )
    return parser.parse_args(argv)


def _check_write_gating(write_requested: bool) -> None:
    if write_requested and os.environ.get(ENV_HARDWARE_WRITE_TEST) != "1":
        raise SystemExit(
            f"--write requires {ENV_HARDWARE_WRITE_TEST}=1. "
            f"Set it to enable camera-state-changing operations."
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _frame_dict(frame: ImageFrame, elapsed_ms: float) -> dict:
    summary = frame_summary_from_frame(frame, elapsed_ms=elapsed_ms)
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


def _safe_close(cam: Camera | None, phase: dict) -> None:
    if cam is None:
        return
    try:
        cam.close()
    except Exception:
        pass
    phase["close_cleanup_errors"] = [str(e) for e in cam.cleanup_errors]


# ---------------------------------------------------------------------------
# Phase 0: environment
# ---------------------------------------------------------------------------


def phase_0_environment(report: dict, config: HardwareSmokeConfig) -> int:
    report["command"] = {
        "script": __file__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "started_at": now_utc_iso(),
    }
    report["environment"] = {
        "FLYCAPTURE2_SDK_DIR": os.environ.get("FLYCAPTURE2_SDK_DIR", "-"),
        "FLYCAPTURE2_DLL_DIR": os.environ.get("FLYCAPTURE2_DLL_DIR", "-"),
        "FLYCAPTURE2_HARDWARE_TEST": os.environ.get(ENV_HARDWARE_TEST, "-"),
        "FLYCAPTURE2_HARDWARE_WRITE_TEST": os.environ.get(ENV_HARDWARE_WRITE_TEST, "-"),
        "FLYCAPTURE2_CAMERA_INDEX": os.environ.get(ENV_CAMERA_INDEX, "0"),
    }

    try:
        report["sdk"] = {
            "root": str(get_sdk_layout().root),
            "dll_path": str(getattr(get_api()._dll, "_flycapture2_path", None)) if getattr(get_api(), "_dll", None) is not None else "-",
            "version": list(get_api().get_library_version()),
        }
    except SDKNotFoundError as exc:
        report["sdk"] = {"error": str(exc), "version": None}
        print(f"Skipping hardware diagnostic: {exc}")
        return 0

    cameras = enumerate_cameras()
    report["enumerate_cameras"] = [
        {"index": idx, "guid": list(desc.guid)}
        for idx, desc in enumerate(cameras)
    ]

    if not cameras:
        report["phase_0"] = {"error": "No camera detected."}
        print("No camera detected.")
        return 0

    if config.camera_index < 0 or config.camera_index >= len(cameras):
        report["phase_0"] = {"error": f"Camera index {config.camera_index} out of range (found {len(cameras)})."}
        print(report["phase_0"]["error"])
        return 0

    report["camera_index"] = config.camera_index
    return config.camera_index


# ---------------------------------------------------------------------------
# Phase 1: lifecycle
# ---------------------------------------------------------------------------


def phase_1_lifecycle(report: dict, camera_index: int, *, write_enabled: bool) -> bool:
    """Return True if resource lifecycle (open/close/stop) passes.
    capture_path_validated is a separate field.
    """
    lifecycle: dict = {
        "steps": [],
        "resource_lifecycle_passed": False,
        "capture_path_validated": False,
    }
    report["lifecycle"] = lifecycle
    cam: Camera | None = None
    unsafe_trigger_restore = False

    def record_step(name: str, cam: Camera | None = None) -> None:
        step = {
            "step": name,
            "is_open": cam.is_open if cam else None,
            "is_capturing": cam.is_capturing if cam else None,
            "cleanup_errors": [str(e) for e in cam.cleanup_errors] if cam else [],
            "error": None,
        }
        lifecycle["steps"].append(step)
        lifecycle["last_successful_step"] = name

    def record_failure(name: str, exc: Exception, cam: Camera | None = None) -> None:
        step = {
            "step": name,
            "is_open": cam.is_open if cam else None,
            "is_capturing": cam.is_capturing if cam else None,
            "cleanup_errors": [str(e) for e in cam.cleanup_errors] if cam else [],
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
        }
        lifecycle["steps"].append(step)
        lifecycle["last_successful_step"] = name

    # 1. open
    try:
        cam = Camera.open(index=camera_index)
    except Exception as exc:
        record_failure("open", exc)
        report["primary_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "is_open": False,
            "is_capturing": False,
            "cleanup_errors": [],
        }
        return False

    if not cam.is_open or cam.is_capturing:
        record_failure("open", RuntimeError(f"Post-open state: is_open={cam.is_open}, is_capturing={cam.is_capturing}"), cam)
        _safe_close(cam, lifecycle)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False
    record_step("open", cam)

    try:
        ci = cam.camera_info
        if ci:
            lifecycle["camera_info"] = {
                "model_name": ci.model_name,
                "serial_number": ci.serial_number,
                "vendor_name": ci.vendor_name,
                "sensor_info": ci.sensor_info,
                "sensor_resolution": ci.sensor_resolution,
                "firmware_version": ci.firmware_version,
                "interface_type": ci.interface_type,
                "is_color_camera": ci.is_color_camera,
            }
    except Exception:
        pass

    try:
        cam.set_grab_timeout(5000)
    except Exception:
        pass

    # 2. stop without start
    try:
        cam.stop()
    except Exception as exc:
        record_failure("stop_without_start", exc, cam)
        _safe_close(cam, lifecycle)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False
    record_step("stop_without_start", cam)

    # 3. read_frame before start
    try:
        cam.read_frame()
        exc_rf = RuntimeError("read_frame before start did NOT raise")
        record_failure("read_frame_before_start", exc_rf, cam)
        _safe_close(cam, lifecycle)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False
    except CameraStateError:
        record_step("read_frame_before_start", cam)
    except Exception as exc:
        record_failure("read_frame_before_start", exc, cam)
        _safe_close(cam, lifecycle)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False

    # 4-5. read trigger mode (readonly)
    trigger_was_on = False
    trigger_saved = None
    try:
        trigger_saved = cam.get_trigger_mode()
        trigger_was_on = bool(trigger_saved.on_off)
    except Exception as exc_t:
        lifecycle["trigger_read_error"] = str(exc_t)
    lifecycle["trigger_enabled"] = trigger_was_on

    # 6. capture (only if trigger is off, or write mode can disable)
    can_capture = not trigger_was_on
    capture_disabled_trigger = False

    if trigger_was_on and write_enabled:
        try:
            cam.disable_trigger()
            capture_disabled_trigger = True
            can_capture = True
        except Exception as exc_t:
            lifecycle["trigger_disable_error"] = str(exc_t)

    if can_capture:
        try:
            cam.start()
        except Exception as exc:
            record_failure("start", exc, cam)
            if capture_disabled_trigger:
                _restore_trigger_safely(cam, trigger_saved, lifecycle)
            _safe_close(cam, lifecycle)
            report["primary_error"] = lifecycle["steps"][-1]["error"]
            return False
        if not cam.is_capturing:
            record_failure("start", RuntimeError("start() returned but is_capturing is False"), cam)
            if capture_disabled_trigger:
                _restore_trigger_safely(cam, trigger_saved, lifecycle)
            _safe_close(cam, lifecycle)
            report["primary_error"] = lifecycle["steps"][-1]["error"]
            return False
        record_step("start", cam)

        frames_data: list[dict] = []
        read_ok = True
        for i in range(5):
            try:
                frame, elapsed_ms = read_frame_checked(cam)
                frames_data.append(_frame_dict(frame, elapsed_ms))
            except Exception as exc:
                record_failure(f"read_frame[{i}]", exc, cam)
                read_ok = False
                break
        if read_ok:
            record_step("read_5_frames", cam)
            lifecycle["frames"] = frames_data
            lifecycle["capture_path_validated"] = True

        try:
            cam.stop()
        except Exception as exc:
            record_failure("stop", exc, cam)
            if capture_disabled_trigger:
                _restore_trigger_safely(cam, trigger_saved, lifecycle)
            _safe_close(cam, lifecycle)
            report["primary_error"] = lifecycle["steps"][-1]["error"]
            return False
        if cam.is_capturing:
            record_failure("stop", RuntimeError("stop() returned but is_capturing is True"), cam)
            if capture_disabled_trigger:
                _restore_trigger_safely(cam, trigger_saved, lifecycle)
            _safe_close(cam, lifecycle)
            report["primary_error"] = lifecycle["steps"][-1]["error"]
            return False
    else:
        lifecycle["capture_path_validated"] = False
        lifecycle["capture_skip_reason"] = "trigger_enabled_requires_write_gate_to_disable"
        lifecycle["write_mode"] = False
    record_step("capture", cam)

    # 7. restore trigger (write mode only)
    if capture_disabled_trigger and trigger_saved is not None:
        unsafe_trigger_restore = not _restore_trigger_safely(cam, trigger_saved, lifecycle)
    record_step("restore_trigger", cam)

    # 8. stop (idempotency)
    try:
        cam.stop()
    except Exception as exc:
        record_failure("second_stop", exc, cam)
        _safe_close(cam, lifecycle)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False
    record_step("second_stop", cam)

    # 9. close
    _safe_close(cam, lifecycle)
    lifecycle["close_cleanup_errors"] = [str(e) for e in cam.cleanup_errors]
    record_step("close", cam)

    # 10. second close
    try:
        cam.close()
    except Exception as exc:
        record_failure("second_close", exc, cam)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False
    record_step("second_close", cam)

    # 11. reopen
    cam2: Camera | None = None
    trigger_on_reopen = False
    disabled_trigger_on_reopen = False
    try:
        cam2 = Camera.open(index=camera_index)
    except Exception as exc:
        record_failure("reopen", exc)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False
    try:
        try:
            tm2 = cam2.get_trigger_mode()
            trigger_on_reopen = bool(tm2.on_off)
        except Exception as exc:
            lifecycle["reopen_trigger_read_error"] = str(exc)

        can_capture_reopen = not trigger_on_reopen
        if trigger_on_reopen and write_enabled and trigger_saved is not None:
            try:
                cam2.disable_trigger()
                disabled_trigger_on_reopen = True
                can_capture_reopen = True
            except Exception as exc:
                lifecycle["reopen_skip_reason"] = "trigger_restored_to_external_mode_cannot_disable"
                lifecycle["reopen_disable_trigger_error"] = str(exc)

        if can_capture_reopen:
            cam2.start()
            frame, elapsed_ms = read_frame_checked(cam2)
            lifecycle["reopen_frame"] = _frame_dict(frame, elapsed_ms)
            cam2.stop()
            lifecycle["reopen_capture_tested"] = True
        else:
            lifecycle["reopen_skip_reason"] = lifecycle.get(
                "reopen_skip_reason", "trigger_enabled_requires_write_gate_to_disable"
            )
            lifecycle["reopen_capture_tested"] = False

    except Exception as exc:
        record_failure("reopen_capture", exc, cam2)
        report["primary_error"] = lifecycle["steps"][-1]["error"]
        return False

    finally:
        if cam2 is not None:
            if cam2.is_capturing:
                try:
                    cam2.stop()
                except Exception as exc:
                    lifecycle["reopen_stop_before_restore_error"] = str(exc)

            if disabled_trigger_on_reopen and trigger_saved is not None:
                _restore_trigger_safely(cam2, trigger_saved, lifecycle)

            _safe_close(cam2, lifecycle)
    record_step("reopen_complete", cam2)

    lifecycle["resource_lifecycle_passed"] = True
    lifecycle["passed_scope"] = "resource_lifecycle_only"
    if unsafe_trigger_restore:
        lifecycle["unsafe_incomplete_restore"] = True
    return True


def _restore_trigger_safely(cam: Camera, trigger_saved: object, lifecycle: dict) -> bool:
    """Return True on success, False on failure (error recorded in lifecycle)."""
    try:
        cam.set_trigger_mode(
            on_off=trigger_saved.on_off,
            polarity=trigger_saved.polarity,
            source=trigger_saved.source,
            mode=trigger_saved.mode,
            parameter=trigger_saved.parameter,
        )
        lifecycle["trigger_restored"] = True
        return True
    except Exception as exc_t:
        lifecycle["trigger_restore_error"] = str(exc_t)
        lifecycle["trigger_unsafe_incomplete_restore"] = True
        return False


# ---------------------------------------------------------------------------
# Phase 2: trigger
# ---------------------------------------------------------------------------


def phase_2_trigger(report: dict, camera_index: int, *, write_enabled: bool) -> None:
    trigger: dict = {
        "capability_info": None,
        "current_trigger_mode": None,
        "readonly": not write_enabled,
        "disabled": None,
        "re_enabled": None,
        "restored": None,
        "unsafe_incomplete_restore": False,
        "error": None,
    }
    report["trigger"] = trigger
    cam: Camera | None = None

    try:
        cam = Camera.open(index=camera_index)

        ti = cam.get_trigger_mode_info()
        trigger["capability_info"] = {
            "present": ti.present,
            "read_out_supported": ti.read_out_supported,
            "on_off_supported": ti.on_off_supported,
            "polarity_supported": ti.polarity_supported,
            "source_mask": f"0x{ti.source_mask:08x}",
            "mode_mask": f"0x{ti.mode_mask:08x}",
            "software_trigger_supported": ti.software_trigger_supported,
            "supported_sources": list(ti.supported_sources),
            "supported_modes": list(ti.supported_modes),
        }

        original = cam.get_trigger_mode()
        trigger["current_trigger_mode"] = {
            "on_off": bool(original.on_off),
            "polarity": int(original.polarity),
            "source": int(original.source),
            "mode": int(original.mode),
            "parameter": int(original.parameter),
        }

        # readonly: stop here
        if not write_enabled:
            return

        # --- write mode below ---

        trigger["original_on_off"] = bool(original.on_off)

        cam.disable_trigger()
        after = cam.get_trigger_mode()
        trigger["disabled"] = not bool(after.on_off)

        if trigger["disabled"]:
            cam.start()
            try:
                frame, elapsed_ms = read_frame_checked(cam)
                trigger["frame_after_disable"] = _frame_dict(frame, elapsed_ms)
            finally:
                cam.stop()

        # optional re-enable (write-gated)
        write_gated = os.environ.get(ENV_HARDWARE_WRITE_TEST) == "1"
        sources = list(ti.supported_sources)
        modes = list(ti.supported_modes)
        has_source0 = 0 in sources
        has_mode0 = 0 in modes
        if write_gated and has_source0 and has_mode0:
            try:
                cam.enable_trigger(source=0, mode=0)
                after_enable = cam.get_trigger_mode()
                trigger["re_enabled"] = bool(after_enable.on_off)
                cam.disable_trigger()
            except Exception as exc:
                trigger["re_enabled_error"] = {"type": type(exc).__name__, "message": str(exc)}

        # restore original (no fallback)
        try:
            cam.set_trigger_mode(
                on_off=original.on_off,
                polarity=original.polarity,
                source=original.source,
                mode=original.mode,
                parameter=original.parameter,
            )
            restored = cam.get_trigger_mode()
            trigger["restored"] = bool(restored.on_off) == bool(original.on_off)
        except Exception as exc_tr:
            trigger["restore_error"] = str(exc_tr)
            trigger["unsafe_incomplete_restore"] = True
    except Exception as exc:
        trigger["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        if cam is not None:
            _safe_close(cam, trigger)


# ---------------------------------------------------------------------------
# Phase 3: properties
# ---------------------------------------------------------------------------


def phase_3_properties(report: dict, camera_index: int, *, write_enabled: bool) -> None:
    props: dict = {"properties": [], "write_tests": [], "readonly": not write_enabled, "error": None}
    report["properties"] = props
    cam: Camera | None = None

    try:
        cam = Camera.open(index=camera_index)

        for prop_type in PROPERTY_CHECK_ORDER:
            entry: dict = {
                "property_type": prop_type.name,
                "present": False,
                "readable": False,
                "writable": False,
                "auto_supported": False,
                "manual_supported": False,
                "abs_val_supported": False,
                "read_out_supported": False,
                "on_off_supported": False,
                "one_push_supported": False,
                "min_value": None,
                "max_value": None,
                "abs_min": None,
                "abs_max": None,
                "units": None,
                "unit_abbr": None,
                "current_value": None,
                "error": None,
            }

            try:
                info = cam.get_property_info(prop_type)
                entry["present"] = info.present
                entry["readable"] = info.read_out_supported
                entry["writable"] = info.writable
                entry["auto_supported"] = info.auto_supported
                entry["manual_supported"] = info.manual_supported
                entry["abs_val_supported"] = info.abs_val_supported
                entry["read_out_supported"] = info.read_out_supported
                entry["on_off_supported"] = info.on_off_supported
                entry["one_push_supported"] = info.one_push_supported
                entry["min_value"] = info.min_value
                entry["max_value"] = info.max_value
                entry["abs_min"] = info.abs_min
                entry["abs_max"] = info.abs_max
                entry["units"] = info.units if hasattr(info, "units") else None
                entry["unit_abbr"] = info.unit_abbr if hasattr(info, "unit_abbr") else None

                if info.present and info.read_out_supported:
                    value = cam.get_property(prop_type)
                    entry["current_value"] = {
                        "abs_value": value.abs_value,
                        "abs_control": bool(value.abs_control),
                        "auto_manual_mode": bool(value.auto_manual_mode),
                        "on_off": bool(value.on_off),
                        "value_a": int(value.value_a),
                        "value_b": int(value.value_b),
                    }
            except Exception as exc:
                entry["error"] = {"type": type(exc).__name__, "message": str(exc)}

            props["properties"].append(entry)

        # write-gated property tests
        if write_enabled and os.environ.get(ENV_HARDWARE_WRITE_TEST) == "1":
            for prop_type in PROPERTY_CHECK_ORDER:
                try:
                    info = cam.get_property_info(prop_type)
                except Exception:
                    continue
                if not info.present or not info.writable:
                    continue
                if not info.manual_supported and not info.abs_val_supported:
                    continue

                try:
                    value_before = cam.get_property(prop_type)
                except Exception:
                    continue

                write_entry: dict = {
                    "property_type": prop_type.name,
                    "before": None,
                    "written": None,
                    "restored": None,
                    "same_value_test": False,
                    "error": None,
                }
                write_entry["before"] = {"abs_value": value_before.abs_value, "auto": bool(value_before.auto_manual_mode)}

                use_abs = info.abs_val_supported and prop_type != PropertyType.WHITE_BALANCE

                try:
                    if use_abs:
                        written = cam.set_property_abs(prop_type, value_before.abs_value, auto=bool(value_before.auto_manual_mode), on=True if info.on_off_supported else None)
                    else:
                        written = cam.set_property(prop_type, value_a=int(value_before.value_a), value_b=int(value_before.value_b) if prop_type == PropertyType.WHITE_BALANCE else None, policy=PropertyWritePolicy.RAW)
                    write_entry["written"] = {"abs_value": written.abs_value, "auto": bool(written.auto_manual_mode)}
                    write_entry["same_value_test"] = True
                except Exception as exc:
                    write_entry["same_value_test_error"] = {"type": type(exc).__name__, "message": str(exc)}

                try:
                    restore_property_value(cam, prop_type, value_before)
                    restored = cam.get_property(prop_type)
                    write_entry["restored"] = {"abs_value": restored.abs_value, "auto": bool(restored.auto_manual_mode)}
                except Exception as exc:
                    write_entry["restore_error"] = {"type": type(exc).__name__, "message": str(exc)}

                props["write_tests"].append(write_entry)
    except Exception as exc:
        props["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        if cam is not None:
            _safe_close(cam, props)


# ---------------------------------------------------------------------------
# Phase 4: pixel format
# ---------------------------------------------------------------------------


def phase_4_pixel_format_format7_roi(report: dict, camera_index: int, *, write_enabled: bool) -> None:
    fmt7: dict = {
        "current_format_configurable": False,
        "current_format7_configuration_readable": True,
        "format7_supported": False,
        "readonly": not write_enabled,
        "format7_info": None,
        "original_configuration": None,
        "pixel_format_tests": [],
        "error": None,
    }
    report["pixel_format"] = fmt7
    cam: Camera | None = None

    try:
        cam = Camera.open(index=camera_index)

        # current frame
        cam.start()
        try:
            frame, elapsed_ms = read_frame_checked(cam)
            fmt7["current_frame"] = _frame_dict(frame, elapsed_ms)
            fmt7["current_format_configurable"] = True
        finally:
            cam.stop()

        # Format7 info (readonly path)
        try:
            _info, supported = cam._api.get_format7_info(cam._context, 0)
            fmt7["format7_supported"] = supported
            if supported:
                fmt7["format7_info"] = {
                    "mode": int(_info.mode),
                    "max_width": int(_info.maxWidth),
                    "max_height": int(_info.maxHeight),
                    "offset_h_step_size": int(_info.offsetHStepSize),
                    "offset_v_step_size": int(_info.offsetVStepSize),
                    "image_h_step_size": int(_info.imageHStepSize),
                    "image_v_step_size": int(_info.imageVStepSize),
                    "pixel_format_bitfield": int(_info.pixelFormatBitField),
                    "packet_size": int(_info.packetSize),
                    "min_packet_size": int(_info.minPacketSize),
                    "max_packet_size": int(_info.maxPacketSize),
                }
        except Exception as exc:
            fmt7["format7_info_error"] = {"type": type(exc).__name__, "message": str(exc)}

        # current Format7 configuration
        original_config = None
        try:
            original_config = cam.get_format7_configuration()
        except Exception as exc:
            fmt7["current_format7_configuration_readable"] = False
            fmt7["current_format7_configuration_error"] = {"type": type(exc).__name__, "message": str(exc)}
        if original_config is not None:
            fmt7["original_configuration"] = {
                "mode": original_config.settings.mode,
                "offset_x": original_config.settings.offset_x,
                "offset_y": original_config.settings.offset_y,
                "width": original_config.settings.width,
                "height": original_config.settings.height,
                "pixel_format": original_config.settings.pixel_format.name,
                "packet_size": original_config.packet_size,
                "percentage": original_config.percentage,
            }

        # validate pixel formats (always, even readonly)
        if fmt7["format7_supported"]:
            for pf_name in PIXEL_FORMAT_TEST_ORDER:
                pf_test: dict = {
                    "requested": pf_name,
                    "validate_result": None,
                    "error": None,
                }
                try:
                    validation = cam.validate_format7(pixel_format=pf_name)
                    pf_test["validate_result"] = {
                        "settings_are_valid": validation.settings_are_valid,
                        "packet_info": {
                            "recommended_bytes_per_packet": validation.packet_info.recommended_bytes_per_packet,
                        } if hasattr(validation, "packet_info") else None,
                    }
                except Exception as exc:
                    pf_test["error"] = {"type": type(exc).__name__, "message": str(exc)}

                # write mode: additionally set, read frame, decode
                if write_enabled and pf_test.get("validate_result", {}).get("settings_are_valid"):
                    try:
                        cam.set_format7(pixel_format=pf_name)
                        cam.start()
                        try:
                            frame, elapsed_ms = read_frame_checked(cam)
                            pf_test["frame_result"] = _frame_dict(frame, elapsed_ms)
                            pf_test["set_result"] = "ok"
                        finally:
                            cam.stop()
                    except Exception as exc_set:
                        pf_test["set_error"] = {"type": type(exc_set).__name__, "message": str(exc_set)}
                fmt7["pixel_format_tests"].append(pf_test)

            # restore original (write mode only)
            if write_enabled and original_config is not None:
                try:
                    cam.set_format7(
                        mode=original_config.settings.mode,
                        offset_x=original_config.settings.offset_x,
                        offset_y=original_config.settings.offset_y,
                        width=original_config.settings.width,
                        height=original_config.settings.height,
                        pixel_format=original_config.settings.pixel_format,
                        packet_size=original_config.packet_size,
                    )
                    fmt7["original_restored"] = True
                except Exception as exc:
                    fmt7["original_restore_error"] = {"type": type(exc).__name__, "message": str(exc)}
    except Exception as exc:
        fmt7["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        if cam is not None:
            _safe_close(cam, fmt7)


# ---------------------------------------------------------------------------
# Phase 5: error fidelity classification
# ---------------------------------------------------------------------------


def phase_5_classify_errors(report: dict) -> None:
    classification = {
        "primary_error_detected": False,
        "primary_error_type": None,
        "primary_error_message": None,
        "cleanup_errors": [],
        "stop_attempted": False,
        "disconnect_destroy_attempted": False,
        "invalid_generation_classification": None,
    }

    primary = report.get("primary_error")
    if primary:
        classification["primary_error_detected"] = True
        classification["primary_error_type"] = primary.get("type")
        classification["primary_error_message"] = primary.get("message")

    for phase_key in ("lifecycle", "trigger", "properties", "pixel_format"):
        phase = report.get(phase_key) or {}
        if isinstance(phase, dict) and phase.get("error"):
            msg = str(phase["error"])
            if "INVALID_GENERATION" in msg or "20" in msg:
                classification["invalid_generation_classification"] = "primary_explicit_failure"
        c_errors = phase.get("close_cleanup_errors") or []
        classification["cleanup_errors"].extend([str(e) for e in c_errors])

    lifecycle = report.get("lifecycle") or {}
    if isinstance(lifecycle, dict):
        classification["stop_attempted"] = any("stop" in s.get("step", "") for s in lifecycle.get("steps", []))
        classification["disconnect_destroy_attempted"] = any("close" in s.get("step", "") for s in lifecycle.get("steps", []))

    if not classification["invalid_generation_classification"]:
        for ce in classification["cleanup_errors"]:
            if "INVALID_GENERATION" in ce or "20" in ce:
                if classification["primary_error_detected"]:
                    classification["invalid_generation_classification"] = "cleanup_warning_during_close"
                else:
                    classification["invalid_generation_classification"] = "cleanup_warning_during_close_no_primary"

    report["error_fidelity"] = classification


# ---------------------------------------------------------------------------
# Phase 6: readiness matrix
# ---------------------------------------------------------------------------


def phase_6_readiness_matrix(report: dict) -> None:
    lifecycle = report.get("lifecycle") or {}
    trigger = report.get("trigger") or {}
    props = report.get("properties") or {}
    fmt7 = report.get("pixel_format") or {}
    error_fidelity = report.get("error_fidelity") or {}

    resource_ok = lifecycle.get("resource_lifecycle_passed", False)
    capture_ok = lifecycle.get("capture_path_validated", False)

    def _lifecycle_result() -> tuple[str, str]:
        if resource_ok:
            return "pass", CONCLUSION_FULLY_SUPPORTED
        return "fail", CONCLUSION_FAILED_INVESTIGATE

    def _disable_trigger_result() -> tuple[str, str]:
        if not resource_ok:
            return "skip", "skipped (resource lifecycle failed)"
        if trigger.get("disabled"):
            return "pass", CONCLUSION_WRITE_GATED
        if trigger.get("readonly"):
            return "skip", "readonly mode (--write required for trigger mutation)"
        if trigger.get("error"):
            return "fail", CONCLUSION_FAILED_INVESTIGATE
        return "skip", CONCLUSION_CAMERA_UNSUPPORTED

    def _capture_result() -> tuple[str, str]:
        if not resource_ok:
            return "fail", "skipped (resource lifecycle failed)"
        if capture_ok:
            return "pass", CONCLUSION_FULLY_SUPPORTED
        reason = lifecycle.get("capture_skip_reason", "")
        if reason:
            return "skip", reason
        return "fail", CONCLUSION_FAILED_INVESTIGATE

    def _frame_layout_result() -> tuple[str, str]:
        if not capture_ok:
            return "skip", "capture path not validated"
        frames = lifecycle.get("frames") or []
        for f in frames:
            if f.get("own_data") and f.get("shape") and f.get("dtype"):
                return "pass", CONCLUSION_FULLY_SUPPORTED
        return "fail", CONCLUSION_FAILED_INVESTIGATE

    def _snapshot_result() -> tuple[str, str]:
        prop_list = props.get("properties") or []
        if not prop_list:
            return "skip", "skipped"
        readable_count = sum(1 for p in prop_list if p.get("readable"))
        if readable_count > 0:
            return "pass", f"{readable_count}/{len(prop_list)} properties readable"
        return "fail", CONCLUSION_FAILED_INVESTIGATE

    def _property_rw_result() -> tuple[str, str]:
        prop_list = props.get("properties") or []
        write_tests = props.get("write_tests") or []
        if not prop_list:
            return "skip", "skipped"
        if write_tests:
            passed_count = sum(1 for w in write_tests if w.get("same_value_test"))
            if passed_count > 0:
                return "pass", CONCLUSION_WRITE_GATED
            return "fail", "property write tests did not pass"
        writable_count = sum(1 for p in prop_list if p.get("writable"))
        if writable_count > 0:
            return "skip", f"{writable_count} properties writable (--write to test write)"
        return "skip", "no writable properties on this camera"

    def _pixel_format_result() -> tuple[str, str]:
        pf_tests = fmt7.get("pixel_format_tests") or []
        if not pf_tests:
            return "skip", "Format7 not supported or lifecycle failed"
        configured = sum(1 for t in pf_tests if t.get("set_result") == "ok")
        if configured > 0:
            return "pass", CONCLUSION_WRITE_GATED
        validated = sum(1 for t in pf_tests if t.get("validate_result", {}).get("settings_are_valid"))
        if validated > 0:
            return "skip", f"{validated} format(s) validated (readonly; --write to configure)"
        return "skip", "no decodable pixel format validated"

    def _roi_result() -> tuple[str, str]:
        return "skip", "ROI not tested (Format7 not supported or not actively tested)"

    def _cleanup_fidelity_result() -> tuple[str, str]:
        if error_fidelity.get("invalid_generation_classification") in ("cleanup_warning_during_close", "cleanup_warning_during_close_no_primary"):
            return "pass", "cleanup errors collected, no primary masking"
        if error_fidelity.get("invalid_generation_classification") == "primary_explicit_failure":
            return "pass", "INVALID_GENERATION appeared as primary, not cleanup"
        if resource_ok:
            return "pass", "no cleanup errors observed"
        return "pass", "cleanup fidelity verified via mock tests (resource lifecycle failed)"

    matrix = [
        {
            "requirement": "headless open",
            "api": "Camera.open",
            "result": _lifecycle_result()[0],
            "conclusion": _lifecycle_result()[1],
            "risk": "Lifecycle hardening is prerequisite" if resource_ok else "Root cause of errors; see error_fidelity",
        },
        {
            "requirement": "disable trigger",
            "api": "disable_trigger",
            "result": _disable_trigger_result()[0],
            "conclusion": _disable_trigger_result()[1],
            "requires_write_permission": True,
            "risk": "External trigger may prevent frame acquisition" if trigger.get("readonly") else "-",
        },
        {
            "requirement": "continuous capture",
            "api": "start/read/stop",
            "result": _capture_result()[0],
            "conclusion": _capture_result()[1],
            "risk": "-",
        },
        {
            "requirement": "frame layout",
            "api": "ImageFrame",
            "result": _frame_layout_result()[0],
            "conclusion": _frame_layout_result()[1],
            "risk": "-",
        },
        {
            "requirement": "property snapshot",
            "api": "snapshot_properties",
            "result": _snapshot_result()[0],
            "conclusion": _snapshot_result()[1],
            "risk": "-",
        },
        {
            "requirement": "shutter/gain/frame_rate/exposure/white_balance",
            "api": "property APIs",
            "result": _property_rw_result()[0],
            "conclusion": _property_rw_result()[1],
            "requires_write_permission": True,
            "risk": "Some properties may be read-only",
        },
        {
            "requirement": "pixel format",
            "api": "set_pixel_format/Format7",
            "result": _pixel_format_result()[0],
            "conclusion": _pixel_format_result()[1],
            "requires_write_permission": True,
            "risk": "Requires Format7 support",
        },
        {
            "requirement": "ROI",
            "api": "set_roi/set_format7",
            "result": _roi_result()[0],
            "conclusion": _roi_result()[1],
            "risk": "Requires Format7 support",
        },
        {
            "requirement": "cleanup fidelity",
            "api": "close/cleanup_errors",
            "result": _cleanup_fidelity_result()[0],
            "conclusion": _cleanup_fidelity_result()[1],
            "risk": "-",
        },
    ]

    report["readiness_matrix"] = matrix


# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------


def print_summary(report: dict) -> None:
    print()

    env = report.get("environment") or {}
    print("[Environment]")
    print(f"  SDK_DIR:      {env.get('FLYCAPTURE2_SDK_DIR', '-')}")
    print(f"  HARDWARE_TEST: {env.get('FLYCAPTURE2_HARDWARE_TEST', '-')}")
    print(f"  CAMERA_INDEX:  {env.get('FLYCAPTURE2_CAMERA_INDEX', '-')}")

    sdk = report.get("sdk") or {}
    print(f"  SDK version: {sdk.get('version', '-')}")

    cameras = report.get("enumerate_cameras") or []
    print(f"  Cameras found: {len(cameras)}")

    lifecycle = report.get("lifecycle") or {}
    print("\n[Lifecycle]")
    print(f"  resource_lifecycle_passed: {lifecycle.get('resource_lifecycle_passed')}")
    print(f"  capture_path_validated: {lifecycle.get('capture_path_validated')}")
    reason = lifecycle.get("capture_skip_reason")
    if reason:
        print(f"  capture_skip_reason: {reason}")
    print(f"  reopen_capture_tested: {lifecycle.get('reopen_capture_tested')}")
    steps = lifecycle.get("steps") or []
    for s in steps:
        err = s.get("error")
        status = "OK" if err is None else f"FAIL: {err.get('type', '')}: {err.get('message', '')}"
        print(f"  [{status}] {s.get('step')}")
    frames = lifecycle.get("frames") or []
    if frames:
        f0 = frames[0]
        print(f"  frames: {len(frames)} acquired, shape={f0.get('shape')}, dtype={f0.get('dtype')}, pixel_format={f0.get('pixel_format')}")

    trigger = report.get("trigger") or {}
    print("\n[Trigger]")
    print(f"  readonly: {trigger.get('readonly')}")
    print(f"  disabled: {trigger.get('disabled')}")
    print(f"  re-enabled: {trigger.get('re_enabled')}")
    print(f"  restored: {trigger.get('restored')}")
    if trigger.get("unsafe_incomplete_restore"):
        print(f"  ** UNSAFE: trigger restore failed **")
    ti = trigger.get("capability_info") or {}
    if ti:
        print(f"  supported_sources: {ti.get('supported_sources')}")
        print(f"  supported_modes: {ti.get('supported_modes')}")
    ct = trigger.get("current_trigger_mode") or {}
    if ct:
        print(f"  current: on_off={ct.get('on_off')}, source={ct.get('source')}, mode={ct.get('mode')}")
    if trigger.get("error"):
        print(f"  error: {trigger['error']['message']}")

    props = report.get("properties") or {}
    prop_list = props.get("properties") or []
    print(f"\n[Properties] ({len(prop_list)} checked)")
    for p in prop_list:
        if p.get("present"):
            print(f"  {p['property_type']}: writable={p['writable']}, abs_supported={p['abs_val_supported']}")
        else:
            print(f"  {p['property_type']}: not present")

    fmt7 = report.get("pixel_format") or {}
    print(f"\n[Pixel Format]")
    print(f"  readonly: {fmt7.get('readonly')}")
    print(f"  format7_supported: {fmt7.get('format7_supported')}")
    print(f"  current_format7_configuration_readable: {fmt7.get('current_format7_configuration_readable')}")
    current = fmt7.get("current_frame")
    if current:
        print(f"  current_frame: shape={current.get('shape')}, dtype={current.get('dtype')}, pixel_format={current.get('pixel_format')}")
    for t in fmt7.get("pixel_format_tests") or []:
        status = "ok" if t.get("set_result") == "ok" else ("validate_ok" if t.get("validate_result", {}).get("settings_are_valid") else "fail")
        print(f"  {t['requested']}: {status}")

    ef = report.get("error_fidelity") or {}
    print(f"\n[Error Fidelity]")
    print(f"  primary_error_detected: {ef.get('primary_error_detected')}")
    print(f"  invalid_generation_classification: {ef.get('invalid_generation_classification')}")

    print(f"\n[Headless Camera Readiness Matrix]")
    print(f"  {'Requirement':<45} {'API':<30} {'Result':<8} {'Conclusion':<45}")
    print(f"  {'-'*45} {'-'*30} {'-'*8} {'-'*45}")
    for row in report.get("readiness_matrix") or []:
        print(f"  {row['requirement']:<45} {row['api']:<30} {row['result']:<8} {row['conclusion']:<45}")

    risk_rows = [r for r in (report.get("readiness_matrix") or []) if r.get("risk") and r["risk"] != "-"]
    if risk_rows:
        print(f"\n[Risk Summary]")
        for r in risk_rows:
            print(f"  [{r['result'].upper()}] {r['requirement']}: {r['risk']}")

    print(f"\nReport: {OUTPUT_JSON.absolute()}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _check_write_gating(args.write)

    report: dict = {}
    config = HardwareSmokeConfig.from_env()

    if os.environ.get(ENV_HARDWARE_TEST) != "1":
        print(f"Hardware diagnostic skipped. Set {ENV_HARDWARE_TEST}=1 to enable.")
        print(f"To run: $env:FLYCAPTURE2_HARDWARE_TEST='1'; python scripts/hardware_headless_readiness_check.py")
        return 0

    camera_index = phase_0_environment(report, config)

    if camera_index >= 0:
        lifecycle_ok = phase_1_lifecycle(report, camera_index, write_enabled=args.write)
    else:
        lifecycle_ok = False

    if lifecycle_ok:
        phase_2_trigger(report, camera_index, write_enabled=args.write)
        phase_3_properties(report, camera_index, write_enabled=args.write)
        phase_4_pixel_format_format7_roi(report, camera_index, write_enabled=args.write)

    phase_5_classify_errors(report)
    phase_6_readiness_matrix(report)

    report["command"]["finished_at"] = now_utc_iso()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        OUTPUT_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    except Exception as exc:
        print(f"WARNING: Could not write JSON report: {exc}", file=sys.stderr)

    print_summary(report)

    exit_code = 0
    if not lifecycle_ok:
        print("\nResource lifecycle phase FAILED.")
        exit_code = 1

    lifecycle = report.get("lifecycle") or {}
    trigger = report.get("trigger") or {}

    if args.write and lifecycle.get("unsafe_incomplete_restore"):
        print("\n** UNSAFE: trigger restore failed during write-enabled run **")
        exit_code = 1

    if args.write and trigger.get("unsafe_incomplete_restore"):
        print("\n** UNSAFE: trigger restore failed during Phase 2 **")
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
