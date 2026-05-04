from __future__ import annotations

import pytest

from flycapture2_c import Camera, enumerate_cameras
from flycapture2_c._hardware_tools import collect_readonly_summary

pytestmark = pytest.mark.hardware


def test_hardware_readonly_info(hardware_guard, hardware_config) -> None:
    cameras = enumerate_cameras()
    with Camera.open(index=hardware_config.camera_index) as camera:
        summary = collect_readonly_summary(camera, camera_count=len(cameras))

    assert isinstance(summary.camera_info.model_name, str)
    assert isinstance(summary.video_mode, int)
    assert isinstance(summary.frame_rate_mode, int)
    assert len(summary.properties) == 4
    assert summary.camera_count == len(cameras)
    for snapshot in summary.properties:
        assert snapshot.info.property_type == snapshot.property_type
        if snapshot.info.present and snapshot.info.read_out_supported:
            assert snapshot.value is not None
            assert snapshot.value.property_type == snapshot.property_type
