from __future__ import annotations

from enum import IntEnum

import numpy as np

from .errors import UnsupportedPixelFormatError


class PixelFormat(IntEnum):
    MONO8 = 0x80000000
    YUV411 = 0x40000000
    YUV422 = 0x20000000
    YUV444 = 0x10000000
    RGB8 = 0x08000000
    MONO16 = 0x04000000
    RGB16 = 0x02000000
    S_MONO16 = 0x01000000
    S_RGB16 = 0x00800000
    RAW8 = 0x00400000
    RAW16 = 0x00200000
    MONO12 = 0x00100000
    RAW12 = 0x00080000
    BGR = 0x80000008
    BGRU = 0x40000008
    RGB = RGB8
    RGBU = 0x40000002
    BGR16 = 0x02000001
    BGRU16 = 0x02000002
    YUV422_JPEG = 0x40000001
    UNSPECIFIED = 0


DECODABLE_PIXEL_FORMATS = frozenset(
    {
        PixelFormat.MONO8,
        PixelFormat.MONO16,
        PixelFormat.RAW8,
        PixelFormat.RAW16,
    }
)
SUPPORTED_PIXEL_FORMATS = DECODABLE_PIXEL_FORMATS
CONFIGURABLE_PIXEL_FORMATS = frozenset(pixel_format for pixel_format in PixelFormat if pixel_format != PixelFormat.UNSPECIFIED)


def from_sdk_value(value: int) -> PixelFormat:
    pixel_format = configurable_from_sdk_value(value)
    if pixel_format not in DECODABLE_PIXEL_FORMATS:
        raise UnsupportedPixelFormatError(
            f"Pixel format {pixel_format.name} (0x{value:08X}) is not currently decodable by read_frame()."
        )
    return pixel_format


def configurable_from_sdk_value(value: int) -> PixelFormat:
    try:
        pixel_format = PixelFormat(value)
    except ValueError as exc:
        raise UnsupportedPixelFormatError(f"Unsupported pixel format value: 0x{value:08X}") from exc
    if pixel_format not in CONFIGURABLE_PIXEL_FORMATS:
        raise UnsupportedPixelFormatError(f"Unsupported pixel format value: 0x{value:08X}")
    return pixel_format


def normalize_pixel_format(value: PixelFormat | str | int) -> PixelFormat:
    if isinstance(value, PixelFormat):
        pixel_format = value
    elif isinstance(value, str):
        normalized = value.strip().upper().replace(" ", "_").replace("-", "_")
        pixel_format = PixelFormat[normalized]
    else:
        pixel_format = configurable_from_sdk_value(int(value))
    if pixel_format not in CONFIGURABLE_PIXEL_FORMATS:
        raise UnsupportedPixelFormatError(f"Unsupported configurable pixel format: {pixel_format!r}")
    return pixel_format


def is_decodable(pixel_format: PixelFormat | int) -> bool:
    try:
        normalized = configurable_from_sdk_value(int(pixel_format))
    except UnsupportedPixelFormatError:
        return False
    return normalized in DECODABLE_PIXEL_FORMATS


def bytes_per_pixel(pixel_format: PixelFormat) -> int:
    if pixel_format in {PixelFormat.MONO8, PixelFormat.RAW8}:
        return 1
    if pixel_format in {PixelFormat.MONO16, PixelFormat.RAW16}:
        return 2
    raise UnsupportedPixelFormatError(f"Unsupported pixel format: {pixel_format!r}")


def numpy_dtype(pixel_format: PixelFormat) -> np.dtype:
    if pixel_format in {PixelFormat.MONO8, PixelFormat.RAW8}:
        return np.dtype(np.uint8)
    if pixel_format in {PixelFormat.MONO16, PixelFormat.RAW16}:
        return np.dtype(np.uint16)
    raise UnsupportedPixelFormatError(f"Unsupported pixel format: {pixel_format!r}")


def is_raw(pixel_format: PixelFormat) -> bool:
    return pixel_format in {PixelFormat.RAW8, PixelFormat.RAW16}
