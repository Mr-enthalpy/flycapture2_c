from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.pixel_format import PixelFormat, interpret_pixel_format_bitfield

pytestmark = pytest.mark.hardware


def test_hardware_format7_pixel_format_matrix_interpretation(hardware_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        summaries = []
        for mode in range(5):
            info = camera.get_format7_info(mode=mode)
            if not info.supported:
                continue
            summary = interpret_pixel_format_bitfield(info.pixel_format_bit_field)
            summaries.append(summary)

    if not summaries:
        pytest.skip("camera reports no supported Format7 modes")

    for summary in summaries:
        assert "supported_by_camera" in summary
        assert "read_frame_decodable" in summary
        assert "raw_copy_only" in summary
        assert "unsupported_or_compressed" in summary
        if PixelFormat.RGB8.name in summary["supported_by_camera"]:
            assert PixelFormat.RGB8.name in summary["read_frame_decodable"]
