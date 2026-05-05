from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.errors import FlyCapture2Error, UnsupportedPixelFormatError
from flycapture2_c.format7 import choose_preferred_pixel_format
from flycapture2_c.pixel_format import PixelFormat

pytestmark = pytest.mark.hardware


def test_hardware_format7_write_reversible(hardware_write_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        try:
            before = camera.get_format7_configuration()
        except FlyCapture2Error as exc:
            pytest.skip(f"camera is not currently in Format7 or cannot report Format7 configuration: {exc}")

        info = camera.get_format7_info(mode=before.settings.mode)
        if not info.supported:
            pytest.skip(f"current Format7 mode {before.settings.mode} is not reported as supported")

        try:
            test_pixel_format = PixelFormat.MONO8 if info.supports_pixel_format(PixelFormat.MONO8) else choose_preferred_pixel_format(
                info,
                current=before.settings.pixel_format,
            )
        except UnsupportedPixelFormatError as exc:
            pytest.skip(str(exc))

        written = None
        restored = None
        try:
            written = camera.set_format7(
                mode=before.settings.mode,
                offset_x=0,
                offset_y=0,
                width=info.max_width,
                height=info.max_height,
                pixel_format=test_pixel_format,
            )
            restored = camera.set_format7(
                mode=before.settings.mode,
                offset_x=before.settings.offset_x,
                offset_y=before.settings.offset_y,
                width=before.settings.width,
                height=before.settings.height,
                pixel_format=before.settings.pixel_format,
                packet_size=before.packet_size,
            )
        except Exception:
            try:
                camera.set_format7(
                    mode=before.settings.mode,
                    offset_x=before.settings.offset_x,
                    offset_y=before.settings.offset_y,
                    width=before.settings.width,
                    height=before.settings.height,
                    pixel_format=before.settings.pixel_format,
                    packet_size=before.packet_size,
                )
            finally:
                raise

    assert written is not None
    assert restored is not None
    assert written.settings.mode == before.settings.mode
    assert written.settings.offset_x == 0
    assert written.settings.offset_y == 0
    assert written.settings.width == info.max_width
    assert written.settings.height == info.max_height
    assert written.settings.pixel_format == test_pixel_format
    assert restored.settings.mode == before.settings.mode
    assert restored.settings.offset_x == before.settings.offset_x
    assert restored.settings.offset_y == before.settings.offset_y
    assert restored.settings.width == before.settings.width
    assert restored.settings.height == before.settings.height
    assert restored.settings.pixel_format == before.settings.pixel_format
