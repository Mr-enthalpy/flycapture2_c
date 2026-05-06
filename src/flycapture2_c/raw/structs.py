"""FlyCapture2 C ctypes structures.

This module re-exports the currently reviewed compatibility structures from
``flycapture2_c.ctypes_defs`` and defines new SDK structures in the raw layer.
"""

import ctypes

from ..ctypes_defs import (
    BOOL,
    fc2CameraInfo,
    fc2Config,
    fc2ConfigROM,
    fc2Format7ImageSettings,
    fc2Format7Info,
    fc2Format7PacketInfo,
    fc2Image,
    fc2ImageMetadata,
    fc2IPAddress,
    fc2MACAddress,
    fc2PGRGuid,
    fc2Property,
    fc2PropertyInfo,
    fc2TimeStamp,
    fc2TriggerMode,
    fc2TriggerModeInfo,
    fc2Version,
)
from .types import fc2GigEPropertyType, fc2PixelFormat


class fc2EmbeddedImageInfoProperty(ctypes.Structure):
    _fields_ = [
        ("available", BOOL),
        ("onOff", BOOL),
    ]


class fc2EmbeddedImageInfo(ctypes.Structure):
    _fields_ = [
        ("timestamp", fc2EmbeddedImageInfoProperty),
        ("gain", fc2EmbeddedImageInfoProperty),
        ("shutter", fc2EmbeddedImageInfoProperty),
        ("brightness", fc2EmbeddedImageInfoProperty),
        ("exposure", fc2EmbeddedImageInfoProperty),
        ("whiteBalance", fc2EmbeddedImageInfoProperty),
        ("frameCounter", fc2EmbeddedImageInfoProperty),
        ("strobePattern", fc2EmbeddedImageInfoProperty),
        ("GPIOPinState", fc2EmbeddedImageInfoProperty),
        ("ROIPosition", fc2EmbeddedImageInfoProperty),
    ]


class fc2CameraStats(ctypes.Structure):
    _fields_ = [
        ("imageDropped", ctypes.c_uint32),
        ("imageCorrupt", ctypes.c_uint32),
        ("imageXmitFailed", ctypes.c_uint32),
        ("imageDriverDropped", ctypes.c_uint32),
        ("regReadFailed", ctypes.c_uint32),
        ("regWriteFailed", ctypes.c_uint32),
        ("portErrors", ctypes.c_uint32),
        ("cameraPowerUp", BOOL),
        ("cameraVoltages", ctypes.c_float * 8),
        ("numVoltages", ctypes.c_uint32),
        ("cameraCurrents", ctypes.c_float * 8),
        ("numCurrents", ctypes.c_uint32),
        ("temperature", ctypes.c_uint32),
        ("timeSinceInitialization", ctypes.c_uint32),
        ("timeSinceBusReset", ctypes.c_uint32),
        ("timeStamp", fc2TimeStamp),
        ("numResendPacketsRequested", ctypes.c_uint32),
        ("numResendPacketsReceived", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 16),
    ]


class fc2StrobeInfo(ctypes.Structure):
    _fields_ = [
        ("source", ctypes.c_uint32),
        ("present", BOOL),
        ("readOutSupported", BOOL),
        ("onOffSupported", BOOL),
        ("polaritySupported", BOOL),
        ("minValue", ctypes.c_float),
        ("maxValue", ctypes.c_float),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2StrobeControl(ctypes.Structure):
    _fields_ = [
        ("source", ctypes.c_uint32),
        ("onOff", BOOL),
        ("polarity", ctypes.c_uint32),
        ("delay", ctypes.c_float),
        ("duration", ctypes.c_float),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2GigEProperty(ctypes.Structure):
    _fields_ = [
        ("propType", fc2GigEPropertyType),
        ("isReadable", BOOL),
        ("isWritable", BOOL),
        ("min", ctypes.c_uint32),
        ("max", ctypes.c_uint32),
        ("value", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2GigEStreamChannel(ctypes.Structure):
    _fields_ = [
        ("networkInterfaceIndex", ctypes.c_uint32),
        ("hostPort", ctypes.c_uint32),
        ("doNotFragment", BOOL),
        ("packetSize", ctypes.c_uint32),
        ("interPacketDelay", ctypes.c_uint32),
        ("destinationIpAddress", fc2IPAddress),
        ("sourcePort", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2GigEConfig(ctypes.Structure):
    _fields_ = [
        ("enablePacketResend", BOOL),
        ("registerTimeoutRetries", ctypes.c_uint32),
        ("registerTimeout", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2GigEImageSettingsInfo(ctypes.Structure):
    _fields_ = [
        ("maxWidth", ctypes.c_uint32),
        ("maxHeight", ctypes.c_uint32),
        ("offsetHStepSize", ctypes.c_uint32),
        ("offsetVStepSize", ctypes.c_uint32),
        ("imageHStepSize", ctypes.c_uint32),
        ("imageVStepSize", ctypes.c_uint32),
        ("pixelFormatBitField", ctypes.c_uint32),
        ("vendorPixelFormatBitField", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 16),
    ]


class fc2GigEImageSettings(ctypes.Structure):
    _fields_ = [
        ("offsetX", ctypes.c_uint32),
        ("offsetY", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("pixelFormat", fc2PixelFormat),
        ("reserved", ctypes.c_uint32 * 8),
    ]


__all__ = [
    "fc2CameraInfo",
    "fc2CameraStats",
    "fc2Config",
    "fc2ConfigROM",
    "fc2EmbeddedImageInfo",
    "fc2EmbeddedImageInfoProperty",
    "fc2Format7ImageSettings",
    "fc2Format7Info",
    "fc2Format7PacketInfo",
    "fc2GigEConfig",
    "fc2GigEImageSettings",
    "fc2GigEImageSettingsInfo",
    "fc2GigEProperty",
    "fc2GigEStreamChannel",
    "fc2Image",
    "fc2ImageMetadata",
    "fc2IPAddress",
    "fc2MACAddress",
    "fc2PGRGuid",
    "fc2Property",
    "fc2PropertyInfo",
    "fc2StrobeControl",
    "fc2StrobeInfo",
    "fc2TimeStamp",
    "fc2TriggerMode",
    "fc2TriggerModeInfo",
    "fc2Version",
]
