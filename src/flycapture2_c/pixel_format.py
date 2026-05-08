from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class PixelFormatSupport:
    name: str
    sdk_value: int
    sdk_known: bool
    camera_configurable_candidate: bool
    read_frame_decodable: bool
    raw_copy_only: bool
    compressed_or_unsupported: bool
    numpy_shape_kind: str | None
    numpy_dtype: str | None
    bytes_per_pixel: int | None
    channel_count: int | None
    notes: str


_MONO_8BIT_DECODABLE = {PixelFormat.MONO8, PixelFormat.RAW8}
_MONO_16BIT_DECODABLE = {PixelFormat.MONO16, PixelFormat.RAW16}
_RGB_8BIT_DECODABLE = {PixelFormat.RGB8}
_COMPRESSED_OR_UNSUPPORTED = {PixelFormat.YUV422_JPEG, PixelFormat.UNSPECIFIED}


def _support_for_member(name: str, pixel_format: PixelFormat) -> PixelFormatSupport:
    read_frame_decodable = pixel_format in _MONO_8BIT_DECODABLE | _MONO_16BIT_DECODABLE | _RGB_8BIT_DECODABLE
    compressed_or_unsupported = pixel_format in _COMPRESSED_OR_UNSUPPORTED
    raw_copy_only = not read_frame_decodable and not compressed_or_unsupported
    numpy_shape_kind: str | None = None
    numpy_dtype_name: str | None = None
    bpp: int | None = None
    channels: int | None = None
    notes = "Known SDK enum; not decoded by read_frame()."
    if pixel_format in _MONO_8BIT_DECODABLE:
        numpy_shape_kind = "mono2d"
        numpy_dtype_name = "uint8"
        bpp = 1
        channels = 1
        notes = "Decoded as an owned 2-D uint8 NumPy array."
    elif pixel_format in _MONO_16BIT_DECODABLE:
        numpy_shape_kind = "mono2d"
        numpy_dtype_name = "uint16"
        bpp = 2
        channels = 1
        notes = "Decoded as an owned 2-D uint16 NumPy array."
    elif pixel_format in _RGB_8BIT_DECODABLE:
        numpy_shape_kind = "rgb_interleaved_hwc"
        numpy_dtype_name = "uint8"
        bpp = 3
        channels = 3
        notes = "Decoded as owned interleaved RGB with shape (height, width, 3)."
    elif pixel_format is PixelFormat.YUV422_JPEG:
        notes = "Compressed JPEG stream; not decoded or reinterpreted."
    elif pixel_format is PixelFormat.UNSPECIFIED:
        notes = "SDK unspecified pixel format; not configurable or decodable."
    elif pixel_format in {PixelFormat.RGB16, PixelFormat.S_RGB16, PixelFormat.BGR16}:
        notes = "Known uncompressed 16-bit color format; high-level structured decode is not implemented."
    elif pixel_format in {PixelFormat.BGR, PixelFormat.BGRU, PixelFormat.RGBU, PixelFormat.BGRU16}:
        notes = "Known interleaved color format; high-level structured decode is not implemented."
    elif pixel_format in {PixelFormat.YUV411, PixelFormat.YUV422, PixelFormat.YUV444}:
        notes = "Known YUV format; color conversion is intentionally not implemented."
    elif pixel_format in {PixelFormat.MONO12, PixelFormat.RAW12, PixelFormat.S_MONO16}:
        notes = "Known non-default mono/raw format; high-level structured decode is not implemented."

    return PixelFormatSupport(
        name=name,
        sdk_value=int(pixel_format),
        sdk_known=True,
        camera_configurable_candidate=pixel_format is not PixelFormat.UNSPECIFIED,
        read_frame_decodable=read_frame_decodable,
        raw_copy_only=raw_copy_only,
        compressed_or_unsupported=compressed_or_unsupported,
        numpy_shape_kind=numpy_shape_kind,
        numpy_dtype=numpy_dtype_name,
        bytes_per_pixel=bpp,
        channel_count=channels,
        notes=notes,
    )


PIXEL_FORMAT_SUPPORT = {
    name: _support_for_member(name, pixel_format)
    for name, pixel_format in PixelFormat.__members__.items()
}
PIXEL_FORMAT_SUPPORT_BY_VALUE = {
    int(pixel_format): _support_for_member(pixel_format.name, pixel_format)
    for pixel_format in PixelFormat
}
DECODABLE_PIXEL_FORMATS = frozenset(
    {
        PixelFormat.MONO8,
        PixelFormat.MONO16,
        PixelFormat.RGB8,
        PixelFormat.RAW8,
        PixelFormat.RAW16,
    }
)
SUPPORTED_PIXEL_FORMATS = DECODABLE_PIXEL_FORMATS
CONFIGURABLE_PIXEL_FORMATS = frozenset(pixel_format for pixel_format in PixelFormat if pixel_format != PixelFormat.UNSPECIFIED)


def from_sdk_value(value: int) -> PixelFormat:
    try:
        pixel_format = configurable_from_sdk_value(value)
    except UnsupportedPixelFormatError as exc:
        raise UnsupportedPixelFormatError(
            f"Unsupported pixel format value 0x{value:08X}; SDK value is not known by this wrapper."
        ) from exc
    if pixel_format not in DECODABLE_PIXEL_FORMATS:
        support = support_for_value(value)
        known_name = support.name if support is not None else pixel_format.name
        raise UnsupportedPixelFormatError(
            f"Pixel format {known_name} (0x{value:08X}) is known but not decodable by read_frame(). "
            f"Classification: raw_copy_only={support.raw_copy_only if support else False}, "
            f"compressed_or_unsupported={support.compressed_or_unsupported if support else False}."
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


def support_for_pixel_format(pixel_format: PixelFormat | str | int) -> PixelFormatSupport | None:
    try:
        if isinstance(pixel_format, str):
            return PIXEL_FORMAT_SUPPORT[pixel_format.strip().upper().replace(" ", "_").replace("-", "_")]
        return support_for_value(int(pixel_format))
    except (KeyError, ValueError):
        return None


def support_for_value(value: int) -> PixelFormatSupport | None:
    return PIXEL_FORMAT_SUPPORT_BY_VALUE.get(int(value))


def supported_formats_from_bitfield(bitfield: int) -> tuple[PixelFormat, ...]:
    return tuple(
        pixel_format
        for pixel_format in PixelFormat
        if pixel_format in CONFIGURABLE_PIXEL_FORMATS
        if pixel_format_in_bitfield(bitfield, pixel_format)
    )


def pixel_format_in_bitfield(bitfield: int, pixel_format: PixelFormat | str | int) -> bool:
    normalized = normalize_pixel_format(pixel_format)
    value = int(normalized)
    if value == 0:
        return False
    return (int(bitfield) & value) == value


def interpret_pixel_format_bitfield(bitfield: int) -> dict[str, list[str]]:
    supported = supported_formats_from_bitfield(bitfield)
    decodable: list[str] = []
    raw_copy_only: list[str] = []
    unsupported_or_compressed: list[str] = []
    for pixel_format in supported:
        support = support_for_value(int(pixel_format))
        if support is None:
            continue
        if support.read_frame_decodable:
            decodable.append(pixel_format.name)
        elif support.raw_copy_only:
            raw_copy_only.append(pixel_format.name)
        elif support.compressed_or_unsupported:
            unsupported_or_compressed.append(pixel_format.name)
    return {
        "supported_by_camera": [pixel_format.name for pixel_format in supported],
        "read_frame_decodable": decodable,
        "raw_copy_only": raw_copy_only,
        "unsupported_or_compressed": unsupported_or_compressed,
    }


def bytes_per_pixel(pixel_format: PixelFormat) -> int:
    if pixel_format in {PixelFormat.MONO8, PixelFormat.RAW8}:
        return 1
    if pixel_format in {PixelFormat.MONO16, PixelFormat.RAW16}:
        return 2
    if pixel_format in {PixelFormat.RGB8}:
        return 3
    raise UnsupportedPixelFormatError(f"Unsupported pixel format: {pixel_format!r}")


def numpy_dtype(pixel_format: PixelFormat) -> np.dtype:
    if pixel_format in {PixelFormat.MONO8, PixelFormat.RAW8}:
        return np.dtype(np.uint8)
    if pixel_format in {PixelFormat.MONO16, PixelFormat.RAW16}:
        return np.dtype(np.uint16)
    if pixel_format in {PixelFormat.RGB8}:
        return np.dtype(np.uint8)
    raise UnsupportedPixelFormatError(f"Unsupported pixel format: {pixel_format!r}")


def channel_count(pixel_format: PixelFormat) -> int:
    if pixel_format in {PixelFormat.MONO8, PixelFormat.MONO16, PixelFormat.RAW8, PixelFormat.RAW16}:
        return 1
    if pixel_format in {PixelFormat.RGB8}:
        return 3
    raise UnsupportedPixelFormatError(f"Unsupported pixel format: {pixel_format!r}")


def numpy_shape_kind(pixel_format: PixelFormat) -> str:
    support = support_for_value(int(pixel_format))
    if support is None or not support.read_frame_decodable or support.numpy_shape_kind is None:
        raise UnsupportedPixelFormatError(f"Unsupported pixel format: {pixel_format!r}")
    return support.numpy_shape_kind


def is_raw(pixel_format: PixelFormat) -> bool:
    return pixel_format in {PixelFormat.RAW8, PixelFormat.RAW16}
