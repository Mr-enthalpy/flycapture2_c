from __future__ import annotations

import ctypes

import numpy as np

from flycapture2_c.ctypes_defs import fc2Image
from flycapture2_c.errors import UnsupportedPixelFormatError
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
    payload = (
        (1).to_bytes(2, "little")
        + (2).to_bytes(2, "little")
        + (555).to_bytes(2, "little")
        + (3).to_bytes(2, "little")
        + (4).to_bytes(2, "little")
        + (777).to_bytes(2, "little")
    )
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


def test_image_to_frame_copies_rgb8_data_without_row_padding() -> None:
    image, backing = _make_image(
        rows=2,
        cols=2,
        stride=6,
        pixel_format=PixelFormat.RGB8,
        payload=bytes(
            [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
            ]
        ),
    )
    frame = image_to_frame(image)

    assert frame.pixel_format == PixelFormat.RGB8
    assert frame.array.shape == (2, 2, 3)
    assert frame.array.dtype == np.uint8
    assert frame.array.flags["OWNDATA"]
    assert frame.array.tolist() == [
        [[1, 2, 3], [4, 5, 6]],
        [[7, 8, 9], [10, 11, 12]],
    ]

    backing[0] = 42
    assert frame.array[0, 0, 0] == 1


def test_image_to_frame_copies_rgb8_data_with_row_padding() -> None:
    image, _ = _make_image(
        rows=2,
        cols=2,
        stride=8,
        pixel_format=PixelFormat.RGB8,
        payload=bytes(
            [
                1,
                2,
                3,
                4,
                5,
                6,
                99,
                100,
                7,
                8,
                9,
                10,
                11,
                12,
                101,
                102,
            ]
        ),
    )
    frame = image_to_frame(image)

    assert frame.array.shape == (2, 2, 3)
    assert frame.array.dtype == np.uint8
    assert frame.array.flags["OWNDATA"]
    assert frame.array.tolist() == [
        [[1, 2, 3], [4, 5, 6]],
        [[7, 8, 9], [10, 11, 12]],
    ]


def test_image_to_frame_rejects_known_but_undecoded_pixel_format() -> None:
    image, _ = _make_image(
        rows=1,
        cols=1,
        stride=3,
        pixel_format=PixelFormat.BGR,
        payload=bytes([1, 2, 3]),
    )

    try:
        image_to_frame(image)
        assert False, "expected UnsupportedPixelFormatError"
    except UnsupportedPixelFormatError as exc:
        message = str(exc)
        assert "BGR" in message
        assert "0x80000008" in message
        assert "known but not decodable" in message


def test_image_to_frame_rejects_unknown_pixel_format_value() -> None:
    image, _ = _make_image(
        rows=1,
        cols=1,
        stride=1,
        pixel_format=PixelFormat.MONO8,
        payload=bytes([1]),
    )
    image.format = 0x12345678

    try:
        image_to_frame(image)
        assert False, "expected UnsupportedPixelFormatError"
    except UnsupportedPixelFormatError as exc:
        message = str(exc)
        assert "0x12345678" in message
        assert "not known" in message


def test_pixel_format_helpers_cover_first_phase_formats() -> None:
    assert bytes_per_pixel(PixelFormat.MONO8) == 1
    assert bytes_per_pixel(PixelFormat.RGB8) == 3
    assert bytes_per_pixel(PixelFormat.RAW16) == 2
    assert is_raw(PixelFormat.RAW8) is True
    assert is_raw(PixelFormat.MONO16) is False
