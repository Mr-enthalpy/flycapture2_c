from __future__ import annotations

import ctypes

import numpy as np

from flycapture2_c.ctypes_defs import fc2Image
from flycapture2_c.image import image_to_frame
from flycapture2_c.pixel_format import PixelFormat, bytes_per_pixel, is_raw


def _make_image(rows: int, cols: int, stride: int, pixel_format: PixelFormat, payload: bytes) -> tuple[fc2Image, object]:
    buffer = (ctypes.c_ubyte * len(payload))(*payload)
    image = fc2Image()
    image.rows = rows
    image.cols = cols
    image.stride = stride
    image.pData = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
    image.dataSize = len(payload)
    image.receivedDataSize = len(payload)
    image.format = int(pixel_format)
    return image, buffer


def test_image_to_frame_copies_mono8_data() -> None:
    image, backing = _make_image(
        rows=2,
        cols=3,
        stride=4,
        pixel_format=PixelFormat.MONO8,
        payload=bytes([1, 2, 3, 99, 4, 5, 6, 77]),
    )
    frame = image_to_frame(image)

    assert frame.pixel_format == PixelFormat.MONO8
    assert frame.array.dtype == np.uint8
    assert frame.array.flags["OWNDATA"]
    assert frame.array.tolist() == [[1, 2, 3], [4, 5, 6]]

    backing[0] = 42
    assert frame.array[0, 0] == 1


def test_image_to_frame_copies_mono16_data() -> None:
    payload = (1).to_bytes(2, "little") + (2).to_bytes(2, "little") + (555).to_bytes(2, "little") + (3).to_bytes(2, "little") + (4).to_bytes(2, "little") + (777).to_bytes(2, "little")
    image, _ = _make_image(
        rows=2,
        cols=2,
        stride=6,
        pixel_format=PixelFormat.MONO16,
        payload=payload,
    )
    frame = image_to_frame(image)

    assert frame.array.dtype == np.uint16
    assert frame.array.tolist() == [[1, 2], [3, 4]]


def test_pixel_format_helpers_cover_first_phase_formats() -> None:
    assert bytes_per_pixel(PixelFormat.MONO8) == 1
    assert bytes_per_pixel(PixelFormat.RAW16) == 2
    assert is_raw(PixelFormat.RAW8) is True
    assert is_raw(PixelFormat.MONO16) is False
