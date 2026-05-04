from __future__ import annotations

import numpy as np

from flycapture2_c.mock import MockCamera


def test_mock_camera_capture_cycle() -> None:
    camera = MockCamera.open()
    camera.start()
    frame = camera.read_frame()
    camera.stop()
    camera.close()

    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640)
    assert frame.dtype == np.uint8
    assert frame.flags["OWNDATA"]


def test_mock_camera_close_is_idempotent() -> None:
    camera = MockCamera.open()
    camera.close()
    camera.close()
