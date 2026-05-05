from __future__ import annotations

import ctypes

import numpy as np
import pytest

from flycapture2_c.camera import Camera
from flycapture2_c.ctypes_defs import fc2CameraInfo, fc2Image, fc2ImageMetadata, fc2PGRGuid, fc2TimeStamp
from flycapture2_c.errors import FC2ErrorCode, FlyCapture2NotSupportedError, UnsupportedMetadataError
from flycapture2_c.image import ImageFrame, image_to_frame
from flycapture2_c.metadata import CameraStats, EmbeddedImageInfo, ImageMetadata
from flycapture2_c.pixel_format import PixelFormat
from flycapture2_c.raw.structs import fc2CameraStats, fc2EmbeddedImageInfo


class MetadataFakeAPI:
    def __init__(self) -> None:
        self._context = object()
        self.embedded_info = fc2EmbeddedImageInfo()
        self.embedded_info.timestamp.available = 1
        self.embedded_info.timestamp.onOff = 0
        self.embedded_info.frameCounter.available = 1
        self.embedded_info.frameCounter.onOff = 0
        self.embedded_info.gain.available = 0
        self.last_set_info: fc2EmbeddedImageInfo | None = None
        self.reset_stats_called = False
        self._image_buffer = (ctypes.c_ubyte * 2)(1, 2)

    def create_context(self):
        return self._context

    def destroy_context(self, context) -> None:
        assert context is self._context

    def get_num_cameras(self, context) -> int:
        assert context is self._context
        return 1

    def get_camera_from_index(self, context, index: int) -> fc2PGRGuid:
        assert context is self._context
        assert index == 0
        guid = fc2PGRGuid()
        guid.value[:] = [1, 2, 3, 4]
        return guid

    def connect(self, context, guid) -> None:
        assert context is self._context

    def disconnect(self, context) -> None:
        assert context is self._context

    def create_image(self) -> fc2Image:
        return fc2Image()

    def destroy_image(self, image: fc2Image) -> None:
        _ = image

    def get_camera_info(self, context) -> fc2CameraInfo:
        assert context is self._context
        return fc2CameraInfo()

    def start_capture(self, context) -> None:
        assert context is self._context

    def stop_capture(self, context) -> None:
        assert context is self._context

    def retrieve_buffer(self, context, image: fc2Image) -> None:
        assert context is self._context
        image.rows = 1
        image.cols = 2
        image.stride = 2
        image.pData = self._image_buffer
        image.dataSize = 2
        image.receivedDataSize = 2
        image.format = int(PixelFormat.MONO8)

    def get_image_timestamp(self, image: fc2Image) -> fc2TimeStamp:
        _ = image
        timestamp = fc2TimeStamp()
        timestamp.seconds = 5
        return timestamp

    def get_image_metadata(self, image: fc2Image) -> fc2ImageMetadata:
        _ = image
        metadata = fc2ImageMetadata()
        metadata.embeddedTimeStamp = 100
        metadata.embeddedFrameCounter = 123
        return metadata

    def get_embedded_image_info(self, context) -> fc2EmbeddedImageInfo:
        assert context is self._context
        return _copy_embedded_info(self.embedded_info)

    def set_embedded_image_info(self, context, info: fc2EmbeddedImageInfo) -> None:
        assert context is self._context
        self.last_set_info = _copy_embedded_info(info)
        self.embedded_info = _copy_embedded_info(info)

    def get_camera_stats(self, context) -> fc2CameraStats:
        assert context is self._context
        stats = fc2CameraStats()
        stats.imageDropped = 2
        stats.imageCorrupt = 1
        stats.cameraPowerUp = 1
        stats.cameraVoltages[0] = 12.5
        stats.numVoltages = 1
        stats.cameraCurrents[0] = 0.25
        stats.numCurrents = 1
        stats.temperature = 3001
        stats.timeSinceInitialization = 10
        stats.timeStamp.seconds = 123
        stats.numResendPacketsRequested = 7
        stats.numResendPacketsReceived = 6
        return stats

    def reset_camera_stats(self) -> None:
        self.reset_stats_called = True


class MetadataUnsupportedFakeAPI(MetadataFakeAPI):
    def get_image_metadata(self, image: fc2Image) -> fc2ImageMetadata:
        _ = image
        raise FlyCapture2NotSupportedError(
            "metadata unsupported",
            code=FC2ErrorCode.NOT_SUPPORTED,
            operation="fc2GetImageMetadata",
        )


def _copy_embedded_info(source: fc2EmbeddedImageInfo) -> fc2EmbeddedImageInfo:
    target = fc2EmbeddedImageInfo()
    ctypes.memmove(ctypes.byref(target), ctypes.byref(source), ctypes.sizeof(source))
    return target


def _open_camera(api: MetadataFakeAPI) -> Camera:
    return Camera.open(api=api)


def test_embedded_image_info_dataclass_round_trip() -> None:
    raw = fc2EmbeddedImageInfo()
    raw.timestamp.available = 1
    raw.timestamp.onOff = 1
    raw.whiteBalance.available = 1
    raw.whiteBalance.onOff = 0

    info = EmbeddedImageInfo.from_c(raw)
    restored = info.to_c()

    assert info.timestamp.available is True
    assert info.timestamp.on_off is True
    assert info.white_balance.available is True
    assert restored.timestamp.available == 1
    assert restored.timestamp.onOff == 1
    assert restored.whiteBalance.available == 1


def test_image_metadata_dataclass_from_c_struct() -> None:
    raw = fc2ImageMetadata()
    raw.embeddedTimeStamp = 10
    raw.embeddedFrameCounter = 42
    raw.embeddedROIPosition = 3

    metadata = ImageMetadata.from_c(raw)

    assert metadata.timestamp == 10
    assert metadata.frame_counter == 42
    assert metadata.roi_position == 3


def test_camera_stats_dataclass_from_c_struct() -> None:
    raw = fc2CameraStats()
    raw.imageDropped = 3
    raw.cameraPowerUp = 1
    raw.cameraVoltages[0] = 5.0
    raw.cameraVoltages[1] = 12.0
    raw.numVoltages = 2
    raw.cameraCurrents[0] = 0.5
    raw.numCurrents = 1
    raw.temperature = 3015
    raw.timeStamp.seconds = 99

    stats = CameraStats.from_c(raw)

    assert stats.image_dropped == 3
    assert stats.camera_power_up is True
    assert stats.camera_voltages == (5.0, 12.0)
    assert stats.camera_currents == (0.5,)
    assert stats.temperature_kelvin == 301.5
    assert stats.timestamp_seconds == 99


def test_camera_get_and_set_embedded_image_info_with_fake_api() -> None:
    api = MetadataFakeAPI()
    camera = _open_camera(api)
    try:
        info = camera.get_embedded_image_info()
        assert info.timestamp.available is True
        assert info.timestamp.on_off is False

        updated = camera.set_embedded_image_info(timestamp=True, frame_counter=True)

        assert updated.timestamp.on_off is True
        assert updated.frame_counter.on_off is True
        assert api.last_set_info is not None
        assert api.last_set_info.timestamp.onOff == 1
        assert api.last_set_info.frameCounter.onOff == 1
    finally:
        camera.close()


def test_camera_rejects_unsupported_embedded_image_field_update() -> None:
    camera = _open_camera(MetadataFakeAPI())
    try:
        with pytest.raises(UnsupportedMetadataError):
            camera.set_embedded_image_info(gain=True)
    finally:
        camera.close()


def test_camera_restores_full_embedded_info_without_validating_unsupported_fields() -> None:
    api = MetadataFakeAPI()
    camera = _open_camera(api)
    try:
        old = camera.get_embedded_image_info()
        camera.set_embedded_image_info(timestamp=True)
        restored = camera.set_embedded_image_info(old)

        assert restored.timestamp.on_off is False
    finally:
        camera.close()


def test_camera_get_and_reset_stats_with_fake_api() -> None:
    api = MetadataFakeAPI()
    camera = _open_camera(api)
    try:
        stats = camera.get_camera_stats()
        assert stats.image_dropped == 2
        assert stats.image_corrupt == 1
        assert stats.temperature_kelvin == 300.1

        camera.reset_camera_stats()

        assert api.reset_stats_called is True
    finally:
        camera.close()


def test_image_frame_metadata_is_backward_compatible() -> None:
    array = np.array([[1, 2]], dtype=np.uint8)
    frame = ImageFrame(array=array, width=2, height=1, stride=2, pixel_format=PixelFormat.MONO8)

    assert frame.metadata is None
    assert frame.timestamp is None


def test_camera_read_frame_with_info_includes_image_metadata() -> None:
    camera = _open_camera(MetadataFakeAPI())
    try:
        camera.start()
        frame = camera.read_frame_with_info()

        assert frame.array.tolist() == [[1, 2]]
        assert frame.timestamp is not None
        assert frame.timestamp.seconds == 5
        assert frame.metadata is not None
        assert frame.metadata.timestamp == 100
        assert frame.metadata.frame_counter == 123
    finally:
        camera.close()


def test_camera_read_frame_with_info_allows_unsupported_image_metadata() -> None:
    camera = _open_camera(MetadataUnsupportedFakeAPI())
    try:
        camera.start()
        frame = camera.read_frame_with_info()

        assert frame.array.tolist() == [[1, 2]]
        assert frame.metadata is None
    finally:
        camera.close()


def test_image_to_frame_accepts_copied_metadata() -> None:
    payload = (ctypes.c_ubyte * 2)(1, 2)
    image = fc2Image()
    image.rows = 1
    image.cols = 2
    image.stride = 2
    image.pData = payload
    image.dataSize = 2
    image.receivedDataSize = 2
    image.format = int(PixelFormat.MONO8)
    metadata = ImageMetadata(timestamp=1, gain=2, shutter=3, brightness=4, exposure=5, white_balance=6, frame_counter=7, strobe_pattern=8, gpio_pin_state=9, roi_position=10)

    frame = image_to_frame(image, metadata=metadata)

    assert frame.array.tolist() == [[1, 2]]
    assert frame.metadata == metadata
