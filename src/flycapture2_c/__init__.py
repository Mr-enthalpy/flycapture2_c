"""Python wrapper for the FlyCapture2 C SDK."""

from .bus import CameraDescriptor, enumerate_cameras
from .errors import (
    CameraStateError,
    CameraConfigurationError,
    DLLLoadError,
    FlyCapture2Error,
    Format7ValidationError,
    GigEConfigurationError,
    GPIOConfigurationError,
    PropertyModeError,
    PropertyNotWritableError,
    PropertyOutOfRangeError,
    SDKNotFoundError,
    TriggerModeError,
    StrobeConfigurationError,
    UnsupportedFormat7Error,
    UnsupportedGigEError,
    UnsupportedMetadataError,
    UnsupportedPropertyError,
    UnsupportedPixelFormatError,
    UnsupportedStrobeError,
    UnsupportedTriggerError,
)

__all__ = [
    "Camera",
    "CameraConfiguration",
    "CameraConfigurationError",
    "CameraInfo",
    "CameraStats",
    "CameraDescriptor",
    "CameraStateError",
    "CameraPropertyInfo",
    "CameraPropertySnapshot",
    "CameraPropertyValue",
    "DLLLoadError",
    "FlyCapture2Error",
    "Format7Configuration",
    "Format7ImageSettings",
    "Format7Info",
    "Format7PacketInfo",
    "Format7Validation",
    "Format7ValidationError",
    "GigEConfig",
    "GigEConfigurationError",
    "GigEImageBinningSettings",
    "GigEImageSettings",
    "GigEImageSettingsInfo",
    "GigEProperty",
    "GigEPropertyType",
    "GigEStreamChannelInfo",
    "GPIOConfigurationError",
    "EmbeddedImageField",
    "EmbeddedImageInfo",
    "ImageMetadata",
    "GrabMode",
    "MockCamera",
    "PixelFormat",
    "PropertyModeError",
    "PropertyNotWritableError",
    "PropertyOutOfRangeError",
    "PropertyWritePolicy",
    "PropertyType",
    "SDKNotFoundError",
    "StrobeConfigurationError",
    "StrobeControl",
    "StrobeInfo",
    "TriggerMode",
    "TriggerModeError",
    "TriggerModeInfo",
    "UnsupportedFormat7Error",
    "UnsupportedGigEError",
    "UnsupportedMetadataError",
    "UnsupportedPropertyError",
    "UnsupportedPixelFormatError",
    "UnsupportedStrobeError",
    "UnsupportedTriggerError",
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
    if name == "CameraStats":
        from .metadata import CameraStats

        return CameraStats
    if name == "EmbeddedImageField":
        from .metadata import EmbeddedImageField

        return EmbeddedImageField
    if name == "EmbeddedImageInfo":
        from .metadata import EmbeddedImageInfo

        return EmbeddedImageInfo
    if name == "CameraPropertyInfo":
        from .properties import CameraPropertyInfo

        return CameraPropertyInfo
    if name == "CameraPropertySnapshot":
        from .properties import CameraPropertySnapshot

        return CameraPropertySnapshot
    if name == "CameraPropertyValue":
        from .properties import CameraPropertyValue

        return CameraPropertyValue
    if name == "CameraConfiguration":
        from .config import CameraConfiguration

        return CameraConfiguration
    if name == "Format7Configuration":
        from .format7 import Format7Configuration

        return Format7Configuration
    if name == "Format7ImageSettings":
        from .format7 import Format7ImageSettings

        return Format7ImageSettings
    if name == "Format7Info":
        from .format7 import Format7Info

        return Format7Info
    if name == "Format7PacketInfo":
        from .format7 import Format7PacketInfo

        return Format7PacketInfo
    if name == "Format7Validation":
        from .format7 import Format7Validation

        return Format7Validation
    if name == "ImageMetadata":
        from .metadata import ImageMetadata

        return ImageMetadata
    if name == "GigEConfig":
        from .gige import GigEConfig

        return GigEConfig
    if name == "GigEImageBinningSettings":
        from .gige import GigEImageBinningSettings

        return GigEImageBinningSettings
    if name == "GigEImageSettings":
        from .gige import GigEImageSettings

        return GigEImageSettings
    if name == "GigEImageSettingsInfo":
        from .gige import GigEImageSettingsInfo

        return GigEImageSettingsInfo
    if name == "GigEProperty":
        from .gige import GigEProperty

        return GigEProperty
    if name == "GigEPropertyType":
        from .gige import GigEPropertyType

        return GigEPropertyType
    if name == "GigEStreamChannelInfo":
        from .gige import GigEStreamChannelInfo

        return GigEStreamChannelInfo
    if name == "GrabMode":
        from .config import GrabMode

        return GrabMode
    if name == "StrobeControl":
        from .strobe import StrobeControl

        return StrobeControl
    if name == "StrobeInfo":
        from .strobe import StrobeInfo

        return StrobeInfo
    if name == "MockCamera":
        from .mock import MockCamera

        return MockCamera
    if name == "PixelFormat":
        from .pixel_format import PixelFormat

        return PixelFormat
    if name == "PropertyType":
        from .properties import PropertyType

        return PropertyType
    if name == "PropertyWritePolicy":
        from .properties import PropertyWritePolicy

        return PropertyWritePolicy
    if name == "TriggerMode":
        from .trigger import TriggerMode

        return TriggerMode
    if name == "TriggerModeInfo":
        from .trigger import TriggerModeInfo

        return TriggerModeInfo
    if name == "open_mock_camera":
        from .mock import open_mock_camera

        return open_mock_camera
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
