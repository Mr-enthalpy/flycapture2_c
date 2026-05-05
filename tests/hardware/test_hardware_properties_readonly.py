from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c.properties import PropertyType

pytestmark = pytest.mark.hardware


def test_hardware_property_discovery_readonly(hardware_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        infos = camera.list_property_infos()
        snapshots = camera.snapshot_properties()

        present = [item for item in snapshots if item.info is not None and item.info.present]
        for property_type in (
            PropertyType.AUTO_EXPOSURE,
            PropertyType.SHUTTER,
            PropertyType.GAIN,
            PropertyType.FRAME_RATE,
        ):
            info = camera.get_property_info(property_type)
            if info.present and info.read_out_supported:
                value = camera.get_property(property_type)
                assert value.property_type == property_type

    assert len(infos) > 0
    assert len(snapshots) == len(infos)
    assert present, "expected at least one present camera property"
    assert any(item.property_type == PropertyType.SHUTTER for item in snapshots)
