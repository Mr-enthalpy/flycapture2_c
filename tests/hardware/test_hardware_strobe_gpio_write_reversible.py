from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FlyCapture2Error


def _find_safe_strobe_source(camera: Camera):
    for source in range(4):
        try:
            info = camera.get_strobe_info(source)
        except FlyCapture2Error:
            continue
        if info.present and info.read_out_supported:
            return source
    return None


def test_hardware_strobe_write_reversible(hardware_write_guard, hardware_config) -> None:
    """Same-value write smoke test.

    This verifies that the SDK write path accepts and restores the existing
    strobe state. It intentionally does not actively toggle external strobe
    output or require any loopback fixture.
    """
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        source = _find_safe_strobe_source(camera)
        if source is None:
            pytest.skip("no readable strobe source was reported by this camera")

        old = camera.get_strobe(source)
        try:
            written = camera.set_strobe(old)
            assert written.source == old.source
            assert written.on_off == old.on_off
            assert written.polarity == old.polarity
            assert written.delay == pytest.approx(old.delay)
            assert written.duration == pytest.approx(old.duration)
        finally:
            camera.set_strobe(old)

        restored = camera.get_strobe(source)
        assert restored.on_off == old.on_off
        assert restored.polarity == old.polarity


def test_hardware_gpio_pin_direction_write_same_value(hardware_write_guard, hardware_config) -> None:
    _ = hardware_write_guard
    with Camera.open(index=hardware_config.camera_index) as camera:
        try:
            old = camera.get_gpio_pin_direction(0)
        except FlyCapture2Error as exc:
            pytest.skip(f"GPIO pin direction readback is not available: {exc}")

        try:
            written = camera.set_gpio_pin_direction(0, old)
            assert written == old
        except FlyCapture2Error as exc:
            pytest.skip(f"GPIO pin direction write is not available: {exc}")
        finally:
            try:
                camera.set_gpio_pin_direction(0, old)
            except FlyCapture2Error:
                pass
