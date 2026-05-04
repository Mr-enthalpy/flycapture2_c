from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .errors import CameraStateError
from .typing import FrameArray


@dataclass(frozen=True)
class MockCameraConfig:
    width: int = 640
    height: int = 480
    dtype: type[np.uint8] | type[np.uint16] = np.uint8
    seed: int = 0


class MockCamera:
    def __init__(self, config: MockCameraConfig | None = None) -> None:
        self._config = config or MockCameraConfig()
        self._rng = np.random.default_rng(self._config.seed)
        self._open = False
        self._capturing = False
        self._frame_id = 0

    @classmethod
    def open(cls, index: int = 0, config: MockCameraConfig | None = None) -> "MockCamera":
        _ = index
        camera = cls(config=config)
        camera._open = True
        return camera

    def start(self) -> None:
        self._require_open()
        self._capturing = True

    def read_frame(self) -> FrameArray:
        self._require_open()
        if not self._capturing:
            raise CameraStateError("Mock camera capture has not been started.")
        self._frame_id += 1
        width = self._config.width
        height = self._config.height
        frame = np.arange(width * height, dtype=np.uint32).reshape(height, width)
        frame = (frame + self._frame_id) % np.iinfo(self._config.dtype).max
        noise = self._rng.integers(0, 3, size=(height, width), dtype=np.uint8)
        return (frame.astype(self._config.dtype) + noise.astype(self._config.dtype)).copy()

    def stop(self) -> None:
        self._capturing = False

    def close(self) -> None:
        self._capturing = False
        self._open = False

    def _require_open(self) -> None:
        if not self._open:
            raise CameraStateError("Mock camera is not open.")

    def __enter__(self) -> "MockCamera":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def open_mock_camera(index: int = 0, config: MockCameraConfig | None = None) -> MockCamera:
    return MockCamera.open(index=index, config=config)
