from __future__ import annotations

import ctypes

fc2Context = ctypes.c_void_p
fc2Error = ctypes.c_int
fc2InterfaceType = ctypes.c_int
fc2DriverType = ctypes.c_int
fc2BusSpeed = ctypes.c_int
fc2PCIeBusSpeed = ctypes.c_int
fc2PropertyType = ctypes.c_int
fc2VideoMode = ctypes.c_int
fc2FrameRate = ctypes.c_int
fc2PixelFormat = ctypes.c_uint32
fc2BayerTileFormat = ctypes.c_uint32


BOOL = ctypes.c_int


class fc2PGRGuid(ctypes.Structure):
    _fields_ = [
        ("value", ctypes.c_uint32 * 4),
    ]


class fc2Version(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_uint32),
        ("minor", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("build", ctypes.c_uint32),
    ]


class fc2TimeStamp(ctypes.Structure):
    _fields_ = [
        ("seconds", ctypes.c_longlong),
        ("microSeconds", ctypes.c_uint32),
        ("cycleSeconds", ctypes.c_uint32),
        ("cycleCount", ctypes.c_uint32),
        ("cycleOffset", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2IPAddress(ctypes.Structure):
    _fields_ = [
        ("octets", ctypes.c_ubyte * 4),
    ]


class fc2MACAddress(ctypes.Structure):
    _fields_ = [
        ("octets", ctypes.c_ubyte * 6),
    ]


class fc2ImageMetadata(ctypes.Structure):
    _fields_ = [
        ("embeddedTimeStamp", ctypes.c_uint32),
        ("embeddedGain", ctypes.c_uint32),
        ("embeddedShutter", ctypes.c_uint32),
        ("embeddedBrightness", ctypes.c_uint32),
        ("embeddedExposure", ctypes.c_uint32),
        ("embeddedWhiteBalance", ctypes.c_uint32),
        ("embeddedFrameCounter", ctypes.c_uint32),
        ("embeddedStrobePattern", ctypes.c_uint32),
        ("embeddedGPIOPinState", ctypes.c_uint32),
        ("embeddedROIPosition", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 31),
    ]


class fc2ConfigROM(ctypes.Structure):
    _fields_ = [
        ("nodeVendorId", ctypes.c_uint32),
        ("chipIdHi", ctypes.c_uint32),
        ("chipIdLo", ctypes.c_uint32),
        ("unitSpecId", ctypes.c_uint32),
        ("unitSWVer", ctypes.c_uint32),
        ("unitSubSWVer", ctypes.c_uint32),
        ("vendorUniqueInfo_0", ctypes.c_uint32),
        ("vendorUniqueInfo_1", ctypes.c_uint32),
        ("vendorUniqueInfo_2", ctypes.c_uint32),
        ("vendorUniqueInfo_3", ctypes.c_uint32),
        ("pszKeyword", ctypes.c_char * 512),
        ("reserved", ctypes.c_uint32 * 16),
    ]


class fc2CameraInfo(ctypes.Structure):
    _fields_ = [
        ("serialNumber", ctypes.c_uint32),
        ("interfaceType", fc2InterfaceType),
        ("driverType", fc2DriverType),
        ("isColorCamera", ctypes.c_int),
        ("modelName", ctypes.c_char * 512),
        ("vendorName", ctypes.c_char * 512),
        ("sensorInfo", ctypes.c_char * 512),
        ("sensorResolution", ctypes.c_char * 512),
        ("driverName", ctypes.c_char * 512),
        ("firmwareVersion", ctypes.c_char * 512),
        ("firmwareBuildTime", ctypes.c_char * 512),
        ("maximumBusSpeed", fc2BusSpeed),
        ("bayerTileFormat", fc2BayerTileFormat),
        ("pcieBusSpeed", fc2PCIeBusSpeed),
        ("nodeNumber", ctypes.c_uint16),
        ("busNumber", ctypes.c_uint16),
        ("iidcVer", ctypes.c_uint32),
        ("configROM", fc2ConfigROM),
        ("gigEMajorVersion", ctypes.c_uint32),
        ("gigEMinorVersion", ctypes.c_uint32),
        ("userDefinedName", ctypes.c_char * 512),
        ("xmlURL1", ctypes.c_char * 512),
        ("xmlURL2", ctypes.c_char * 512),
        ("macAddress", fc2MACAddress),
        ("ipAddress", fc2IPAddress),
        ("subnetMask", fc2IPAddress),
        ("defaultGateway", fc2IPAddress),
        ("ccpStatus", ctypes.c_uint32),
        ("applicationIPAddress", ctypes.c_uint32),
        ("applicationPort", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 16),
    ]


class fc2PropertyInfo(ctypes.Structure):
    _fields_ = [
        ("type", fc2PropertyType),
        ("present", ctypes.c_int),
        ("autoSupported", ctypes.c_int),
        ("manualSupported", ctypes.c_int),
        ("onOffSupported", ctypes.c_int),
        ("onePushSupported", ctypes.c_int),
        ("absValSupported", ctypes.c_int),
        ("readOutSupported", ctypes.c_int),
        ("min", ctypes.c_uint32),
        ("max", ctypes.c_uint32),
        ("absMin", ctypes.c_float),
        ("absMax", ctypes.c_float),
        ("pUnits", ctypes.c_char * 512),
        ("pUnitAbbr", ctypes.c_char * 512),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2Property(ctypes.Structure):
    _fields_ = [
        ("type", fc2PropertyType),
        ("present", ctypes.c_int),
        ("absControl", ctypes.c_int),
        ("onePush", ctypes.c_int),
        ("onOff", ctypes.c_int),
        ("autoManualMode", ctypes.c_int),
        ("valueA", ctypes.c_uint32),
        ("valueB", ctypes.c_uint32),
        ("absValue", ctypes.c_float),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2TriggerModeInfo(ctypes.Structure):
    _fields_ = [
        ("present", BOOL),
        ("readOutSupported", BOOL),
        ("onOffSupported", BOOL),
        ("polaritySupported", BOOL),
        ("valueReadable", BOOL),
        ("sourceMask", ctypes.c_uint32),
        ("softwareTriggerSupported", BOOL),
        ("modeMask", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2TriggerMode(ctypes.Structure):
    _fields_ = [
        ("onOff", BOOL),
        ("polarity", ctypes.c_uint32),
        ("source", ctypes.c_uint32),
        ("mode", ctypes.c_uint32),
        ("parameter", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class fc2Image(ctypes.Structure):
    _fields_ = [
        ("rows", ctypes.c_uint32),
        ("cols", ctypes.c_uint32),
        ("stride", ctypes.c_uint32),
        ("pData", ctypes.POINTER(ctypes.c_ubyte)),
        ("dataSize", ctypes.c_uint32),
        ("receivedDataSize", ctypes.c_uint32),
        ("format", fc2PixelFormat),
        ("bayerFormat", fc2BayerTileFormat),
        ("imageImpl", ctypes.c_void_p),
    ]
