from __future__ import annotations

import pytest

from flycapture2_c import Camera

pytestmark = pytest.mark.hardware


def test_hardware_grab_timeout_write_reversible(hardware_write_guard, hardware_config) -> None:
    with Camera.open(index=hardware_config.camera_index) as camera:
        before = camera.get_configuration()
        requested_timeout = 1000 if before.grab_timeout != 1000 else 500
        written = None
        restored = None
        try:
            written = camera.set_grab_timeout(requested_timeout)
            restored = camera.set_configuration(before)
        except Exception:
            try:
                camera.set_configuration(before)
            finally:
                raise

    assert written is not None
    assert restored is not None
    assert written.grab_timeout == requested_timeout
    assert restored.grab_timeout == before.grab_timeout
    assert restored.grab_mode == before.grab_mode
    assert restored.num_buffers == before.num_buffers
