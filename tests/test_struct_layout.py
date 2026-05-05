from __future__ import annotations

import ctypes

from flycapture2_c.ctypes_defs import (
    fc2Config,
    fc2Format7ImageSettings,
    fc2Format7Info,
    fc2Format7PacketInfo,
    fc2Image,
    fc2ImageMetadata,
    fc2PGRGuid,
    fc2TriggerMode,
    fc2TriggerModeInfo,
)
from flycapture2_c.raw.structs import fc2CameraStats, fc2EmbeddedImageInfo, fc2EmbeddedImageInfoProperty


def test_fc2_pgr_guid_layout() -> None:
    assert ctypes.sizeof(fc2PGRGuid) == 16
    assert fc2PGRGuid.value.offset == 0


def test_fc2_image_layout() -> None:
    ptr_size = ctypes.sizeof(ctypes.c_void_p)
    expected_offsets = {
        "rows": 0,
        "cols": 4,
        "stride": 8,
        "pData": 16 if ptr_size == 8 else 12,
        "dataSize": 24 if ptr_size == 8 else 16,
        "receivedDataSize": 28 if ptr_size == 8 else 20,
        "format": 32 if ptr_size == 8 else 24,
        "bayerFormat": 36 if ptr_size == 8 else 28,
        "imageImpl": 40 if ptr_size == 8 else 32,
    }
    expected_size = 48 if ptr_size == 8 else 36

    assert ctypes.sizeof(fc2Image) == expected_size
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2Image, field_name).offset == offset


def test_fc2_trigger_mode_info_layout() -> None:
    expected_offsets = {
        "present": 0,
        "readOutSupported": 4,
        "onOffSupported": 8,
        "polaritySupported": 12,
        "valueReadable": 16,
        "sourceMask": 20,
        "softwareTriggerSupported": 24,
        "modeMask": 28,
        "reserved": 32,
    }

    assert ctypes.sizeof(fc2TriggerModeInfo) == 64
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2TriggerModeInfo, field_name).offset == offset


def test_fc2_trigger_mode_layout() -> None:
    expected_offsets = {
        "onOff": 0,
        "polarity": 4,
        "source": 8,
        "mode": 12,
        "parameter": 16,
        "reserved": 20,
    }

    assert ctypes.sizeof(fc2TriggerMode) == 52
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2TriggerMode, field_name).offset == offset


def test_fc2_format7_image_settings_layout() -> None:
    expected_offsets = {
        "mode": 0,
        "offsetX": 4,
        "offsetY": 8,
        "width": 12,
        "height": 16,
        "pixelFormat": 20,
        "reserved": 24,
    }

    assert ctypes.sizeof(fc2Format7ImageSettings) == 56
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2Format7ImageSettings, field_name).offset == offset


def test_fc2_format7_info_layout() -> None:
    expected_offsets = {
        "mode": 0,
        "maxWidth": 4,
        "maxHeight": 8,
        "offsetHStepSize": 12,
        "offsetVStepSize": 16,
        "imageHStepSize": 20,
        "imageVStepSize": 24,
        "pixelFormatBitField": 28,
        "vendorPixelFormatBitField": 32,
        "packetSize": 36,
        "minPacketSize": 40,
        "maxPacketSize": 44,
        "percentage": 48,
        "reserved": 52,
    }

    assert ctypes.sizeof(fc2Format7Info) == 116
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2Format7Info, field_name).offset == offset


def test_fc2_format7_packet_info_layout() -> None:
    expected_offsets = {
        "recommendedBytesPerPacket": 0,
        "maxBytesPerPacket": 4,
        "unitBytesPerPacket": 8,
        "reserved": 12,
    }

    assert ctypes.sizeof(fc2Format7PacketInfo) == 44
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2Format7PacketInfo, field_name).offset == offset


def test_fc2_config_layout() -> None:
    expected_offsets = {
        "numBuffers": 0,
        "numImageNotifications": 4,
        "minNumImageNotifications": 8,
        "grabTimeout": 12,
        "grabMode": 16,
        "highPerformanceRetrieveBuffer": 20,
        "isochBusSpeed": 24,
        "asyncBusSpeed": 28,
        "bandwidthAllocation": 32,
        "registerTimeoutRetries": 36,
        "registerTimeout": 40,
        "reserved": 44,
    }

    assert ctypes.sizeof(fc2Config) == 108
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2Config, field_name).offset == offset


def test_fc2_embedded_image_info_property_layout() -> None:
    assert ctypes.sizeof(fc2EmbeddedImageInfoProperty) == 8
    assert fc2EmbeddedImageInfoProperty.available.offset == 0
    assert fc2EmbeddedImageInfoProperty.onOff.offset == 4


def test_fc2_embedded_image_info_layout() -> None:
    expected_offsets = {
        "timestamp": 0,
        "gain": 8,
        "shutter": 16,
        "brightness": 24,
        "exposure": 32,
        "whiteBalance": 40,
        "frameCounter": 48,
        "strobePattern": 56,
        "GPIOPinState": 64,
        "ROIPosition": 72,
    }

    assert ctypes.sizeof(fc2EmbeddedImageInfo) == 80
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2EmbeddedImageInfo, field_name).offset == offset


def test_fc2_image_metadata_layout() -> None:
    expected_offsets = {
        "embeddedTimeStamp": 0,
        "embeddedGain": 4,
        "embeddedShutter": 8,
        "embeddedBrightness": 12,
        "embeddedExposure": 16,
        "embeddedWhiteBalance": 20,
        "embeddedFrameCounter": 24,
        "embeddedStrobePattern": 28,
        "embeddedGPIOPinState": 32,
        "embeddedROIPosition": 36,
        "reserved": 40,
    }

    assert ctypes.sizeof(fc2ImageMetadata) == 164
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2ImageMetadata, field_name).offset == offset


def test_fc2_camera_stats_layout() -> None:
    expected_offsets = {
        "imageDropped": 0,
        "imageCorrupt": 4,
        "imageXmitFailed": 8,
        "imageDriverDropped": 12,
        "regReadFailed": 16,
        "regWriteFailed": 20,
        "portErrors": 24,
        "cameraPowerUp": 28,
        "cameraVoltages": 32,
        "numVoltages": 64,
        "cameraCurrents": 68,
        "numCurrents": 100,
        "temperature": 104,
        "timeSinceInitialization": 108,
        "timeSinceBusReset": 112,
        "timeStamp": 120,
        "numResendPacketsRequested": 176,
        "numResendPacketsReceived": 180,
        "reserved": 184,
    }

    assert ctypes.sizeof(fc2CameraStats) == 248
    for field_name, offset in expected_offsets.items():
        assert getattr(fc2CameraStats, field_name).offset == offset
