from __future__ import annotations

import ctypes
from threading import Lock

from .ctypes_defs import (
    fc2CameraInfo,
    fc2Context,
    fc2Error,
    fc2FrameRate,
    fc2Image,
    fc2PGRGuid,
    fc2PixelFormat,
    fc2Property,
    fc2PropertyInfo,
    fc2TimeStamp,
    fc2TriggerMode,
    fc2TriggerModeInfo,
    fc2Version,
    fc2VideoMode,
)
from .dll import load_library
from .errors import FC2ErrorCode, raise_for_error


class FlyCapture2CAPI:
    def __init__(self) -> None:
        self._dll: ctypes.CDLL | None = None
        self._lock = Lock()

    @property
    def dll(self) -> ctypes.CDLL:
        if self._dll is None:
            with self._lock:
                if self._dll is None:
                    self._dll = load_library()
                    self._bind(self._dll)
        return self._dll

    def _bind(self, dll: ctypes.CDLL) -> None:
        dll.fc2CreateContext.argtypes = [ctypes.POINTER(fc2Context)]
        dll.fc2CreateContext.restype = fc2Error

        dll.fc2DestroyContext.argtypes = [fc2Context]
        dll.fc2DestroyContext.restype = fc2Error

        dll.fc2GetNumOfCameras.argtypes = [fc2Context, ctypes.POINTER(ctypes.c_uint32)]
        dll.fc2GetNumOfCameras.restype = fc2Error

        dll.fc2GetCameraFromIndex.argtypes = [fc2Context, ctypes.c_uint32, ctypes.POINTER(fc2PGRGuid)]
        dll.fc2GetCameraFromIndex.restype = fc2Error

        dll.fc2GetCameraInfo.argtypes = [fc2Context, ctypes.POINTER(fc2CameraInfo)]
        dll.fc2GetCameraInfo.restype = fc2Error

        dll.fc2GetPropertyInfo.argtypes = [fc2Context, ctypes.POINTER(fc2PropertyInfo)]
        dll.fc2GetPropertyInfo.restype = fc2Error

        dll.fc2GetProperty.argtypes = [fc2Context, ctypes.POINTER(fc2Property)]
        dll.fc2GetProperty.restype = fc2Error

        dll.fc2SetProperty.argtypes = [fc2Context, ctypes.POINTER(fc2Property)]
        dll.fc2SetProperty.restype = fc2Error

        dll.fc2GetTriggerModeInfo.argtypes = [fc2Context, ctypes.POINTER(fc2TriggerModeInfo)]
        dll.fc2GetTriggerModeInfo.restype = fc2Error

        dll.fc2GetTriggerMode.argtypes = [fc2Context, ctypes.POINTER(fc2TriggerMode)]
        dll.fc2GetTriggerMode.restype = fc2Error

        dll.fc2SetTriggerMode.argtypes = [fc2Context, ctypes.POINTER(fc2TriggerMode)]
        dll.fc2SetTriggerMode.restype = fc2Error

        dll.fc2SetTriggerModeBroadcast.argtypes = [fc2Context, ctypes.POINTER(fc2TriggerMode)]
        dll.fc2SetTriggerModeBroadcast.restype = fc2Error

        dll.fc2Connect.argtypes = [fc2Context, ctypes.POINTER(fc2PGRGuid)]
        dll.fc2Connect.restype = fc2Error

        dll.fc2Disconnect.argtypes = [fc2Context]
        dll.fc2Disconnect.restype = fc2Error

        dll.fc2IsConnected.argtypes = [fc2Context]
        dll.fc2IsConnected.restype = ctypes.c_int

        dll.fc2StartCapture.argtypes = [fc2Context]
        dll.fc2StartCapture.restype = fc2Error

        dll.fc2StopCapture.argtypes = [fc2Context]
        dll.fc2StopCapture.restype = fc2Error

        dll.fc2RetrieveBuffer.argtypes = [fc2Context, ctypes.POINTER(fc2Image)]
        dll.fc2RetrieveBuffer.restype = fc2Error

        dll.fc2CreateImage.argtypes = [ctypes.POINTER(fc2Image)]
        dll.fc2CreateImage.restype = fc2Error

        dll.fc2DestroyImage.argtypes = [ctypes.POINTER(fc2Image)]
        dll.fc2DestroyImage.restype = fc2Error

        dll.fc2GetImageDimensions.argtypes = [
            ctypes.POINTER(fc2Image),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(fc2PixelFormat),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        dll.fc2GetImageDimensions.restype = fc2Error

        dll.fc2GetImageData.argtypes = [ctypes.POINTER(fc2Image), ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))]
        dll.fc2GetImageData.restype = fc2Error

        dll.fc2GetImageTimeStamp.argtypes = [ctypes.POINTER(fc2Image)]
        dll.fc2GetImageTimeStamp.restype = fc2TimeStamp

        dll.fc2GetVideoModeAndFrameRate.argtypes = [
            fc2Context,
            ctypes.POINTER(fc2VideoMode),
            ctypes.POINTER(fc2FrameRate),
        ]
        dll.fc2GetVideoModeAndFrameRate.restype = fc2Error

        dll.fc2GetLibraryVersion.argtypes = [ctypes.POINTER(fc2Version)]
        dll.fc2GetLibraryVersion.restype = fc2Error

        dll.fc2ErrorToDescription.argtypes = [fc2Error]
        dll.fc2ErrorToDescription.restype = ctypes.c_char_p

    def _error_description(self, code: int) -> str | None:
        raw = self.dll.fc2ErrorToDescription(code)
        if not raw:
            return None
        return raw.decode("utf-8", errors="replace")

    def _check(self, code: int, operation: str) -> None:
        if code == FC2ErrorCode.OK:
            return
        raise_for_error(code, description=self._error_description(code), operation=operation)

    def create_context(self) -> fc2Context:
        context = fc2Context()
        self._check(self.dll.fc2CreateContext(ctypes.byref(context)), "fc2CreateContext")
        return context

    def destroy_context(self, context: fc2Context) -> None:
        self._check(self.dll.fc2DestroyContext(context), "fc2DestroyContext")

    def get_num_cameras(self, context: fc2Context) -> int:
        count = ctypes.c_uint32()
        self._check(self.dll.fc2GetNumOfCameras(context, ctypes.byref(count)), "fc2GetNumOfCameras")
        return int(count.value)

    def get_camera_from_index(self, context: fc2Context, index: int) -> fc2PGRGuid:
        guid = fc2PGRGuid()
        self._check(self.dll.fc2GetCameraFromIndex(context, index, ctypes.byref(guid)), "fc2GetCameraFromIndex")
        return guid

    def get_camera_info(self, context: fc2Context) -> fc2CameraInfo:
        info = fc2CameraInfo()
        self._check(self.dll.fc2GetCameraInfo(context, ctypes.byref(info)), "fc2GetCameraInfo")
        return info

    def get_property_info(self, context: fc2Context, property_type: int) -> fc2PropertyInfo:
        prop_info = fc2PropertyInfo()
        prop_info.type = property_type
        self._check(self.dll.fc2GetPropertyInfo(context, ctypes.byref(prop_info)), "fc2GetPropertyInfo")
        return prop_info

    def get_property(self, context: fc2Context, property_type: int) -> fc2Property:
        prop = fc2Property()
        prop.type = property_type
        self._check(self.dll.fc2GetProperty(context, ctypes.byref(prop)), "fc2GetProperty")
        return prop

    def set_property(self, context: fc2Context, prop: fc2Property) -> None:
        self._check(self.dll.fc2SetProperty(context, ctypes.byref(prop)), "fc2SetProperty")

    def get_trigger_mode_info(self, context: fc2Context) -> fc2TriggerModeInfo:
        trigger_mode_info = fc2TriggerModeInfo()
        self._check(
            self.dll.fc2GetTriggerModeInfo(context, ctypes.byref(trigger_mode_info)),
            "fc2GetTriggerModeInfo",
        )
        return trigger_mode_info

    def get_trigger_mode(self, context: fc2Context) -> fc2TriggerMode:
        trigger_mode = fc2TriggerMode()
        self._check(self.dll.fc2GetTriggerMode(context, ctypes.byref(trigger_mode)), "fc2GetTriggerMode")
        return trigger_mode

    def set_trigger_mode(self, context: fc2Context, trigger_mode: fc2TriggerMode) -> None:
        self._check(self.dll.fc2SetTriggerMode(context, ctypes.byref(trigger_mode)), "fc2SetTriggerMode")

    def set_trigger_mode_broadcast(self, context: fc2Context, trigger_mode: fc2TriggerMode) -> None:
        self._check(
            self.dll.fc2SetTriggerModeBroadcast(context, ctypes.byref(trigger_mode)),
            "fc2SetTriggerModeBroadcast",
        )

    def connect(self, context: fc2Context, guid: fc2PGRGuid) -> None:
        self._check(self.dll.fc2Connect(context, ctypes.byref(guid)), "fc2Connect")

    def disconnect(self, context: fc2Context) -> None:
        self._check(self.dll.fc2Disconnect(context), "fc2Disconnect")

    def is_connected(self, context: fc2Context) -> bool:
        return bool(self.dll.fc2IsConnected(context))

    def start_capture(self, context: fc2Context) -> None:
        self._check(self.dll.fc2StartCapture(context), "fc2StartCapture")

    def stop_capture(self, context: fc2Context) -> None:
        self._check(self.dll.fc2StopCapture(context), "fc2StopCapture")

    def create_image(self) -> fc2Image:
        image = fc2Image()
        self._check(self.dll.fc2CreateImage(ctypes.byref(image)), "fc2CreateImage")
        return image

    def destroy_image(self, image: fc2Image) -> None:
        self._check(self.dll.fc2DestroyImage(ctypes.byref(image)), "fc2DestroyImage")

    def retrieve_buffer(self, context: fc2Context, image: fc2Image) -> None:
        self._check(self.dll.fc2RetrieveBuffer(context, ctypes.byref(image)), "fc2RetrieveBuffer")

    def get_image_dimensions(self, image: fc2Image) -> tuple[int, int, int, int]:
        rows = ctypes.c_uint32()
        cols = ctypes.c_uint32()
        stride = ctypes.c_uint32()
        pixel_format = fc2PixelFormat()
        bayer_format = ctypes.c_uint32()
        self._check(
            self.dll.fc2GetImageDimensions(
                ctypes.byref(image),
                ctypes.byref(rows),
                ctypes.byref(cols),
                ctypes.byref(stride),
                ctypes.byref(pixel_format),
                ctypes.byref(bayer_format),
            ),
            "fc2GetImageDimensions",
        )
        return int(rows.value), int(cols.value), int(stride.value), int(pixel_format.value)

    def get_image_data_pointer(self, image: fc2Image) -> ctypes.POINTER(ctypes.c_ubyte):
        data_ptr = ctypes.POINTER(ctypes.c_ubyte)()
        self._check(self.dll.fc2GetImageData(ctypes.byref(image), ctypes.byref(data_ptr)), "fc2GetImageData")
        return data_ptr

    def get_image_timestamp(self, image: fc2Image) -> fc2TimeStamp:
        return self.dll.fc2GetImageTimeStamp(ctypes.byref(image))

    def get_video_mode_and_frame_rate(self, context: fc2Context) -> tuple[int, int]:
        video_mode = fc2VideoMode()
        frame_rate = fc2FrameRate()
        self._check(
            self.dll.fc2GetVideoModeAndFrameRate(context, ctypes.byref(video_mode), ctypes.byref(frame_rate)),
            "fc2GetVideoModeAndFrameRate",
        )
        return int(video_mode.value), int(frame_rate.value)

    def get_library_version(self) -> tuple[int, int, int, int]:
        version = fc2Version()
        self._check(self.dll.fc2GetLibraryVersion(ctypes.byref(version)), "fc2GetLibraryVersion")
        return (int(version.major), int(version.minor), int(version.type), int(version.build))


_API: FlyCapture2CAPI | None = None


def get_api() -> FlyCapture2CAPI:
    global _API
    if _API is None:
        _API = FlyCapture2CAPI()
    return _API
