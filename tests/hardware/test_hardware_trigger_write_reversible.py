from __future__ import annotations

import pytest

from flycapture2_c import Camera, TriggerMode
from flycapture2_c.errors import TriggerModeError, UnsupportedTriggerError

pytestmark = pytest.mark.hardware


def _choose_supported_source(info, current: TriggerMode) -> int | None:
    if info.supports_source(current.source):
        return current.source
    if info.supports_source(0):
        return 0
    if info.software_trigger_supported and info.supports_source(7):
        return 7
    supported_sources = info.supported_sources
    return supported_sources[0] if supported_sources else None


def _choose_supported_mode(info, current: TriggerMode) -> int | None:
    if info.supports_mode(current.mode):
        return current.mode
    if info.supports_mode(0):
        return 0
    supported_modes = info.supported_modes
    return supported_modes[0] if supported_modes else None


def test_hardware_trigger_write_reversible(hardware_write_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        info = camera.get_trigger_mode_info()
        if not info.present:
            pytest.skip("camera reports no trigger mode support")
        if not info.on_off_supported:
            pytest.skip("camera trigger on/off is not writable")

        before = camera.get_trigger_mode()
        source = _choose_supported_source(info, before)
        mode = _choose_supported_mode(info, before)
        if source is None:
            pytest.skip("camera reports no supported trigger source")
        if mode is None:
            pytest.skip("camera reports no supported trigger mode")

        test_state = TriggerMode(
            on_off=not before.on_off,
            polarity=before.polarity,
            source=source,
            mode=mode,
            parameter=before.parameter,
        )

        written = None
        restored = None
        try:
            written = camera.set_trigger_mode(test_state)
            restored = camera.set_trigger_mode(before)
        except (UnsupportedTriggerError, TriggerModeError) as exc:
            pytest.skip(str(exc))
        except Exception:
            try:
                camera.set_trigger_mode(before)
            finally:
                raise

    assert written is not None
    assert restored is not None
    assert written.on_off == test_state.on_off
    assert written.source == test_state.source
    assert written.mode == test_state.mode
    assert restored.on_off == before.on_off
    assert restored.source == before.source
    assert restored.mode == before.mode
