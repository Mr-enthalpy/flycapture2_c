from __future__ import annotations

import pytest

from flycapture2_c import Camera
from flycapture2_c._hardware_tools import attempt_reversible_property_write

pytestmark = pytest.mark.hardware


def test_hardware_property_write_reversible(hardware_write_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        report = attempt_reversible_property_write(camera)
        if report is None:
            pytest.skip("no supported reversible absolute property write candidate was available")

    assert report.written.property_type == report.property_type
    assert report.restored.property_type == report.property_type
    tolerance = max(abs(report.requested_value) * 0.1, 0.5)
    restore_tolerance = max(abs(report.before.abs_value) * 0.1, 0.5)
    assert abs(report.written.abs_value - report.requested_value) <= tolerance
    assert abs(report.restored.abs_value - report.before.abs_value) <= restore_tolerance
    assert report.restored.auto_manual_mode == report.before.auto_manual_mode
