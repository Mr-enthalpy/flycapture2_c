"""FlyCapture2 C ctypes structures.

This module mirrors the currently reviewed structures from
``flycapture2_c.ctypes_defs``. It gives future SDK expansion a raw-layer home
without breaking existing imports from ``ctypes_defs``.
"""

from ..ctypes_defs import (
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

__all__ = [
    "fc2CameraInfo",
    "fc2Config",
    "fc2ConfigROM",
    "fc2Format7ImageSettings",
    "fc2Format7Info",
    "fc2Format7PacketInfo",
    "fc2Image",
    "fc2ImageMetadata",
    "fc2IPAddress",
    "fc2MACAddress",
    "fc2PGRGuid",
    "fc2Property",
    "fc2PropertyInfo",
    "fc2TimeStamp",
    "fc2TriggerMode",
    "fc2TriggerModeInfo",
    "fc2Version",
]
