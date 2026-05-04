"""Minimal Python wrapper for the FlyCapture2 C SDK."""

from .bus import CameraDescriptor, enumerate_cameras
from .errors import (
    CameraStateError,
    DLLLoadError,
    FlyCapture2Error,
    PropertyModeError,
    PropertyNotWritableError,
    PropertyOutOfRangeError,
    SDKNotFoundError,
    UnsupportedPropertyError,
    UnsupportedPixelFormatError,
)

__all__ = [
    "Camera",
    "CameraInfo",
    "CameraDescriptor",
    "CameraStateError",
    "CameraPropertyInfo",
    "CameraPropertyValue",
    "DLLLoadError",
    "FlyCapture2Error",
    "MockCamera",
    "PropertyModeError",
    "PropertyNotWritableError",
    "PropertyOutOfRangeError",
    "PropertyWritePolicy",
    "PropertyType",
    "SDKNotFoundError",
    "UnsupportedPropertyError",
    "UnsupportedPixelFormatError",
    "enumerate_cameras",
    "open_mock_camera",
]

__version__ = "0.1.0"


def __getattr__(name: str):
    if name == "Camera":
        from .camera import Camera

        return Camera
    if name == "CameraInfo":
        from .camera import CameraInfo

        return CameraInfo
    if name == "CameraPropertyInfo":
        from .properties import CameraPropertyInfo

        return CameraPropertyInfo
    if name == "CameraPropertyValue":
        from .properties import CameraPropertyValue

        return CameraPropertyValue
    if name == "MockCamera":
        from .mock import MockCamera

        return MockCamera
    if name == "PropertyType":
        from .properties import PropertyType

        return PropertyType
    if name == "PropertyWritePolicy":
        from .properties import PropertyWritePolicy

        return PropertyWritePolicy
    if name == "open_mock_camera":
        from .mock import open_mock_camera

        return open_mock_camera
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
