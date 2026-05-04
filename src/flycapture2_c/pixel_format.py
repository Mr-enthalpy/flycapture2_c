from __future__ import annotations

from enum import IntEnum

import numpy as np

from .errors import UnsupportedPixelFormatError


class PixelFormat(IntEnum):
    MONO8 = 0x80000000
    MONO16 = 0x04000000
    RAW8 = 0x00400000
    RAW16 = 0x00200000


SUPPORTED_PIXEL_FORMATS = frozenset(PixelFormat)


def from_sdk_value(value: int) -> PixelFormat:
    try:
        pixel_format = PixelFormat(value)
    except ValueError as exc:
        raise UnsupportedPixelFormatError(f"Unsupported pixel format value: 0x{value:08X}") from exc
    if pixel_format not in SUPPORTED_PIXEL_FORMATS:
        raise UnsupportedPixelFormatError(f"Unsupported pixel format value: 0x{value:08X}")
    return pixel_format


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
