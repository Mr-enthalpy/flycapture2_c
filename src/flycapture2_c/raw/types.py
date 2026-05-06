"""Primitive FlyCapture2 C ctypes aliases.

The aliases are bridged from ``flycapture2_c.ctypes_defs`` for compatibility
while the raw package is introduced. New primitive aliases should live here
first, then be re-exported by compatibility modules as needed.
"""

from ..ctypes_defs import (
    BOOL,
    fc2BandwidthAllocation,
    fc2BayerTileFormat,
    fc2BusSpeed,
    fc2Context,
    fc2DriverType,
    fc2Error,
    fc2FrameRate,
    fc2GrabMode,
    fc2GrabTimeout,
    fc2InterfaceType,
    fc2Mode,
    fc2PCIeBusSpeed,
    fc2PixelFormat,
    fc2PropertyType,
    fc2VideoMode,
)

fc2GigEPropertyType = fc2PropertyType

__all__ = [
    "BOOL",
    "fc2BandwidthAllocation",
    "fc2BayerTileFormat",
    "fc2BusSpeed",
    "fc2Context",
    "fc2DriverType",
    "fc2Error",
    "fc2FrameRate",
    "fc2GigEPropertyType",
    "fc2GrabMode",
    "fc2GrabTimeout",
    "fc2InterfaceType",
    "fc2Mode",
    "fc2PCIeBusSpeed",
    "fc2PixelFormat",
    "fc2PropertyType",
    "fc2VideoMode",
]
