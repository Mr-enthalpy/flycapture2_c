from __future__ import annotations

import ctypes

from flycapture2_c.ctypes_defs import fc2Image, fc2PGRGuid, fc2TriggerMode, fc2TriggerModeInfo


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
