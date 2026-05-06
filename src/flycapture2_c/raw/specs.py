"""Function signature registry for the FlyCapture2 C API.

The registry is intentionally data-oriented. ``FlyCapture2CAPI`` uses it to
bind the current SDK functions, and future raw-layer expansion can add specs
here without growing a monolithic ``api.py`` binding block.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .structs import (
    fc2CameraInfo,
    fc2CameraStats,
    fc2Config,
    fc2EmbeddedImageInfo,
    fc2Format7ImageSettings,
    fc2Format7Info,
    fc2Format7PacketInfo,
    fc2GigEConfig,
    fc2GigEImageSettings,
    fc2GigEImageSettingsInfo,
    fc2GigEProperty,
    fc2GigEStreamChannel,
    fc2Image,
    fc2ImageMetadata,
    fc2PGRGuid,
    fc2Property,
    fc2PropertyInfo,
    fc2StrobeControl,
    fc2StrobeInfo,
    fc2TimeStamp,
    fc2TriggerMode,
    fc2TriggerModeInfo,
    fc2Version,
)
from .types import fc2Context, fc2Error, fc2FrameRate, fc2Mode, fc2PixelFormat, fc2VideoMode


@dataclass(frozen=True)
class FunctionSpec:
    """ctypes signature for one FlyCapture2 C function."""

    name: str
    argtypes: Sequence[Any]
    restype: Any
    category: str
    required: bool = True

    def bind(self, dll: ctypes.CDLL) -> None:
        try:
            function = getattr(dll, self.name)
        except AttributeError:
            if self.required:
                raise
            return
        function.argtypes = list(self.argtypes)
        function.restype = self.restype


_SPECS = [
    FunctionSpec("fc2CreateContext", [ctypes.POINTER(fc2Context)], fc2Error, "context"),
    FunctionSpec("fc2DestroyContext", [fc2Context], fc2Error, "context"),
    FunctionSpec("fc2GetNumOfCameras", [fc2Context, ctypes.POINTER(ctypes.c_uint32)], fc2Error, "bus"),
    FunctionSpec(
        "fc2GetCameraFromIndex",
        [fc2Context, ctypes.c_uint32, ctypes.POINTER(fc2PGRGuid)],
        fc2Error,
        "bus",
    ),
    FunctionSpec("fc2GetCameraInfo", [fc2Context, ctypes.POINTER(fc2CameraInfo)], fc2Error, "camera"),
    FunctionSpec("fc2GetPropertyInfo", [fc2Context, ctypes.POINTER(fc2PropertyInfo)], fc2Error, "property"),
    FunctionSpec("fc2GetProperty", [fc2Context, ctypes.POINTER(fc2Property)], fc2Error, "property"),
    FunctionSpec("fc2SetProperty", [fc2Context, ctypes.POINTER(fc2Property)], fc2Error, "property"),
    FunctionSpec(
        "fc2GetEmbeddedImageInfo",
        [fc2Context, ctypes.POINTER(fc2EmbeddedImageInfo)],
        fc2Error,
        "metadata",
    ),
    FunctionSpec(
        "fc2SetEmbeddedImageInfo",
        [fc2Context, ctypes.POINTER(fc2EmbeddedImageInfo)],
        fc2Error,
        "metadata",
    ),
    FunctionSpec("fc2GetConfiguration", [fc2Context, ctypes.POINTER(fc2Config)], fc2Error, "configuration"),
    FunctionSpec("fc2SetConfiguration", [fc2Context, ctypes.POINTER(fc2Config)], fc2Error, "configuration"),
    FunctionSpec("fc2GetStats", [fc2Context, ctypes.POINTER(fc2CameraStats)], fc2Error, "diagnostics"),
    FunctionSpec("ResetStats", [], fc2Error, "diagnostics", required=False),
    FunctionSpec(
        "fc2GetGPIOPinDirection",
        [fc2Context, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)],
        fc2Error,
        "gpio",
        required=False,
    ),
    FunctionSpec(
        "fc2SetGPIOPinDirection",
        [fc2Context, ctypes.c_uint32, ctypes.c_uint32],
        fc2Error,
        "gpio",
        required=False,
    ),
    FunctionSpec(
        "fc2SetGPIOPinDirectionBroadcast",
        [fc2Context, ctypes.c_uint32, ctypes.c_uint32],
        fc2Error,
        "gpio",
        required=False,
    ),
    FunctionSpec(
        "fc2GetFormat7Info",
        [fc2Context, ctypes.POINTER(fc2Format7Info), ctypes.POINTER(ctypes.c_int)],
        fc2Error,
        "format7",
    ),
    FunctionSpec(
        "fc2ValidateFormat7Settings",
        [
            fc2Context,
            ctypes.POINTER(fc2Format7ImageSettings),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(fc2Format7PacketInfo),
        ],
        fc2Error,
        "format7",
    ),
    FunctionSpec(
        "fc2GetFormat7Configuration",
        [
            fc2Context,
            ctypes.POINTER(fc2Format7ImageSettings),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_float),
        ],
        fc2Error,
        "format7",
    ),
    FunctionSpec(
        "fc2SetFormat7ConfigurationPacket",
        [fc2Context, ctypes.POINTER(fc2Format7ImageSettings), ctypes.c_uint32],
        fc2Error,
        "format7",
    ),
    FunctionSpec(
        "fc2SetFormat7Configuration",
        [fc2Context, ctypes.POINTER(fc2Format7ImageSettings), ctypes.c_float],
        fc2Error,
        "format7",
    ),
    FunctionSpec("fc2GetTriggerModeInfo", [fc2Context, ctypes.POINTER(fc2TriggerModeInfo)], fc2Error, "trigger"),
    FunctionSpec("fc2GetTriggerMode", [fc2Context, ctypes.POINTER(fc2TriggerMode)], fc2Error, "trigger"),
    FunctionSpec("fc2SetTriggerMode", [fc2Context, ctypes.POINTER(fc2TriggerMode)], fc2Error, "trigger"),
    FunctionSpec(
        "fc2SetTriggerModeBroadcast",
        [fc2Context, ctypes.POINTER(fc2TriggerMode)],
        fc2Error,
        "trigger",
    ),
    FunctionSpec("fc2FireSoftwareTrigger", [fc2Context], fc2Error, "trigger", required=False),
    FunctionSpec("fc2FireSoftwareTriggerBroadcast", [fc2Context], fc2Error, "trigger", required=False),
    FunctionSpec(
        "fc2GetGigEProperty",
        [fc2Context, ctypes.POINTER(fc2GigEProperty)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2SetGigEProperty",
        [fc2Context, ctypes.POINTER(fc2GigEProperty)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2DiscoverGigEPacketSize",
        [fc2Context, ctypes.POINTER(ctypes.c_uint32)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2QueryGigEImagingMode",
        [fc2Context, fc2Mode, ctypes.POINTER(ctypes.c_int)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2GetGigEImagingMode",
        [fc2Context, ctypes.POINTER(fc2Mode)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec("fc2SetGigEImagingMode", [fc2Context, fc2Mode], fc2Error, "gige", required=False),
    FunctionSpec(
        "fc2GetGigEImageSettingsInfo",
        [fc2Context, ctypes.POINTER(fc2GigEImageSettingsInfo)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2GetGigEImageSettings",
        [fc2Context, ctypes.POINTER(fc2GigEImageSettings)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2SetGigEImageSettings",
        [fc2Context, ctypes.POINTER(fc2GigEImageSettings)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2GetGigEImageBinningSettings",
        [fc2Context, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2SetGigEImageBinningSettings",
        [fc2Context, ctypes.c_uint32, ctypes.c_uint32],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2GetNumStreamChannels",
        [fc2Context, ctypes.POINTER(ctypes.c_uint32)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2GetGigEStreamChannelInfo",
        [fc2Context, ctypes.c_uint32, ctypes.POINTER(fc2GigEStreamChannel)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2SetGigEStreamChannelInfo",
        [fc2Context, ctypes.c_uint32, ctypes.POINTER(fc2GigEStreamChannel)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2GetGigEConfig",
        [fc2Context, ctypes.POINTER(fc2GigEConfig)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec(
        "fc2SetGigEConfig",
        [fc2Context, ctypes.POINTER(fc2GigEConfig)],
        fc2Error,
        "gige",
        required=False,
    ),
    FunctionSpec("fc2GetStrobeInfo", [fc2Context, ctypes.POINTER(fc2StrobeInfo)], fc2Error, "strobe"),
    FunctionSpec("fc2GetStrobe", [fc2Context, ctypes.POINTER(fc2StrobeControl)], fc2Error, "strobe"),
    FunctionSpec("fc2SetStrobe", [fc2Context, ctypes.POINTER(fc2StrobeControl)], fc2Error, "strobe"),
    FunctionSpec(
        "fc2SetStrobeBroadcast",
        [fc2Context, ctypes.POINTER(fc2StrobeControl)],
        fc2Error,
        "strobe",
        required=False,
    ),
    FunctionSpec("fc2Connect", [fc2Context, ctypes.POINTER(fc2PGRGuid)], fc2Error, "camera"),
    FunctionSpec("fc2Disconnect", [fc2Context], fc2Error, "camera"),
    FunctionSpec("fc2IsConnected", [fc2Context], ctypes.c_int, "camera"),
    FunctionSpec("fc2StartCapture", [fc2Context], fc2Error, "capture"),
    FunctionSpec("fc2StopCapture", [fc2Context], fc2Error, "capture"),
    FunctionSpec("fc2RetrieveBuffer", [fc2Context, ctypes.POINTER(fc2Image)], fc2Error, "capture"),
    FunctionSpec("fc2CreateImage", [ctypes.POINTER(fc2Image)], fc2Error, "image"),
    FunctionSpec("fc2DestroyImage", [ctypes.POINTER(fc2Image)], fc2Error, "image"),
    FunctionSpec(
        "fc2GetImageDimensions",
        [
            ctypes.POINTER(fc2Image),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(fc2PixelFormat),
            ctypes.POINTER(ctypes.c_uint32),
        ],
        fc2Error,
        "image",
    ),
    FunctionSpec(
        "fc2GetImageData",
        [ctypes.POINTER(fc2Image), ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))],
        fc2Error,
        "image",
    ),
    FunctionSpec(
        "fc2GetImageMetadata",
        [ctypes.POINTER(fc2Image), ctypes.POINTER(fc2ImageMetadata)],
        fc2Error,
        "image",
    ),
    FunctionSpec("fc2GetImageTimeStamp", [ctypes.POINTER(fc2Image)], fc2TimeStamp, "image"),
    FunctionSpec(
        "fc2GetVideoModeAndFrameRate",
        [fc2Context, ctypes.POINTER(fc2VideoMode), ctypes.POINTER(fc2FrameRate)],
        fc2Error,
        "camera",
    ),
    FunctionSpec("fc2GetLibraryVersion", [ctypes.POINTER(fc2Version)], fc2Error, "library"),
    FunctionSpec("fc2ErrorToDescription", [fc2Error], ctypes.c_char_p, "error"),
]


FUNCTION_SPECS: Mapping[str, FunctionSpec] = {spec.name: spec for spec in _SPECS}


def get_function_spec(name: str) -> FunctionSpec:
    return FUNCTION_SPECS[name]


def bind_function_specs(dll: ctypes.CDLL) -> None:
    for spec in FUNCTION_SPECS.values():
        spec.bind(dll)


__all__ = [
    "FUNCTION_SPECS",
    "FunctionSpec",
    "bind_function_specs",
    "get_function_spec",
]
