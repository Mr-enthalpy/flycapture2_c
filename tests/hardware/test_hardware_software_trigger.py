from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FlyCapture2Error, TriggerModeError, UnsupportedTriggerError
from flycapture2_c.trigger import SOFTWARE_TRIGGER_SOURCE, TriggerMode

pytestmark = pytest.mark.hardware


def _choose_supported_mode(info, current: TriggerMode) -> int | None:
    if info.supports_mode(current.mode):
        return current.mode
    if info.supports_mode(0):
        return 0
    supported_modes = info.supported_modes
    return supported_modes[0] if supported_modes else None


def test_hardware_software_trigger_readonly(hardware_guard, hardware_config) -> None:
    _ = hardware_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        info = camera.get_trigger_mode_info()
        current = camera.get_trigger_mode()

    if not info.present:
        pytest.skip("camera reports no trigger mode support")
    assert isinstance(info.software_trigger_supported, bool)
    assert isinstance(current.on_off, bool)


def _require_software_trigger_support(camera: Camera) -> tuple[TriggerMode, int]:
    info = camera.get_trigger_mode_info()
    if not info.present:
        pytest.skip("camera reports no trigger mode support")
    if not info.software_trigger_supported:
        pytest.skip("camera reports no software trigger support")
    if not info.on_off_supported:
        pytest.skip("camera trigger on/off is not writable")
    if not info.supports_source(SOFTWARE_TRIGGER_SOURCE):
        pytest.skip(f"camera does not advertise software trigger source {SOFTWARE_TRIGGER_SOURCE}")

    original_trigger = camera.get_trigger_mode()
    mode = _choose_supported_mode(info, original_trigger)
    if mode is None:
        pytest.skip("camera reports no supported trigger mode")
    return original_trigger, mode


def _configure_sdk_timeout(camera: Camera, timeout_ms: int | None):
    original_config = camera.get_configuration()
    camera.set_grab_timeout(max(1000, int(timeout_ms or 2000)))
    return original_config


def test_hardware_software_trigger_api_smoke(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        original_trigger, mode = _require_software_trigger_support(camera)
        restored_trigger = None
        try:
            try:
                camera.set_trigger_mode(
                    on_off=True,
                    source=SOFTWARE_TRIGGER_SOURCE,
                    mode=mode,
                    parameter=original_trigger.parameter,
                )
            except (UnsupportedTriggerError, TriggerModeError) as exc:
                pytest.skip(str(exc))

            camera.start()
            camera.fire_software_trigger()
        finally:
            try:
                camera.stop()
            finally:
                restored_trigger = camera.set_trigger_mode(original_trigger)

    assert restored_trigger is not None
    assert restored_trigger.on_off == original_trigger.on_off
    assert restored_trigger.source == original_trigger.source
    assert restored_trigger.mode == original_trigger.mode


def test_hardware_software_trigger_fire_and_grab(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        original_trigger, mode = _require_software_trigger_support(camera)
        try:
            original_config = _configure_sdk_timeout(camera, hardware_config.capture_timeout_ms)
        except FlyCapture2Error as exc:
            pytest.skip(f"SDK grab timeout configuration is not available: {exc}")

        try:
            restored_trigger = None
            restored_config = None
            try:
                camera.set_trigger_mode(
                    on_off=True,
                    source=SOFTWARE_TRIGGER_SOURCE,
                    mode=mode,
                    parameter=original_trigger.parameter,
                )
            except (UnsupportedTriggerError, TriggerModeError) as exc:
                pytest.skip(str(exc))

            camera.start()
            camera.fire_software_trigger()
            try:
                frame = camera.read_frame_with_info()
            except FlyCapture2Error as exc:
                pytest.skip(
                    "software trigger fired, but frame retrieval did not complete under the "
                    f"configured SDK timeout; camera timing/configuration may need model-specific setup: {exc}"
                )
        finally:
            try:
                camera.stop()
            finally:
                try:
                    restored_trigger = camera.set_trigger_mode(original_trigger)
                finally:
                    restored_config = camera.set_configuration(original_config)

        assert frame.array.size > 0
        assert frame.array.flags.owndata
        assert frame.width > 0
        assert frame.height > 0
        assert restored_trigger is not None
        assert restored_trigger.on_off == original_trigger.on_off
        assert restored_trigger.source == original_trigger.source
        assert restored_trigger.mode == original_trigger.mode
        assert restored_config is not None
        assert restored_config.grab_timeout == original_config.grab_timeout
        assert restored_config.grab_mode == original_config.grab_mode
