from __future__ import annotations

from dataclasses import dataclass

from .ctypes_defs import fc2Format7ImageSettings, fc2Format7Info, fc2Format7PacketInfo
from .errors import UnsupportedFormat7Error, UnsupportedPixelFormatError
from .pixel_format import (
    CONFIGURABLE_PIXEL_FORMATS,
    PixelFormat,
    configurable_from_sdk_value,
    normalize_pixel_format,
    pixel_format_in_bitfield,
)

PREFERRED_DECODABLE_PIXEL_FORMATS = (
    PixelFormat.MONO8,
    PixelFormat.MONO16,
    PixelFormat.RAW8,
    PixelFormat.RAW16,
)


@dataclass(frozen=True)
class Format7ImageSettings:
    mode: int
    offset_x: int
    offset_y: int
    width: int
    height: int
    pixel_format: PixelFormat

    @classmethod
    def from_c(cls, struct: fc2Format7ImageSettings) -> "Format7ImageSettings":
        return cls(
            mode=int(struct.mode),
            offset_x=int(struct.offsetX),
            offset_y=int(struct.offsetY),
            width=int(struct.width),
            height=int(struct.height),
            pixel_format=configurable_from_sdk_value(int(struct.pixelFormat)),
        )

    def to_c(self) -> fc2Format7ImageSettings:
        struct = fc2Format7ImageSettings()
        struct.mode = int(self.mode)
        struct.offsetX = int(self.offset_x)
        struct.offsetY = int(self.offset_y)
        struct.width = int(self.width)
        struct.height = int(self.height)
        struct.pixelFormat = int(self.pixel_format)
        return struct


@dataclass(frozen=True)
class Format7Info:
    mode: int
    supported: bool
    max_width: int
    max_height: int
    offset_h_step_size: int
    offset_v_step_size: int
    image_h_step_size: int
    image_v_step_size: int
    pixel_format_bit_field: int
    vendor_pixel_format_bit_field: int
    packet_size: int
    min_packet_size: int
    max_packet_size: int
    percentage: float

    @classmethod
    def from_c(cls, struct: fc2Format7Info, *, supported: bool) -> "Format7Info":
        return cls(
            mode=int(struct.mode),
            supported=bool(supported),
            max_width=int(struct.maxWidth),
            max_height=int(struct.maxHeight),
            offset_h_step_size=int(struct.offsetHStepSize),
            offset_v_step_size=int(struct.offsetVStepSize),
            image_h_step_size=int(struct.imageHStepSize),
            image_v_step_size=int(struct.imageVStepSize),
            pixel_format_bit_field=int(struct.pixelFormatBitField),
            vendor_pixel_format_bit_field=int(struct.vendorPixelFormatBitField),
            packet_size=int(struct.packetSize),
            min_packet_size=int(struct.minPacketSize),
            max_packet_size=int(struct.maxPacketSize),
            percentage=float(struct.percentage),
        )

    @property
    def supported_pixel_formats(self) -> tuple[PixelFormat, ...]:
        return tuple(
            pixel_format
            for pixel_format in CONFIGURABLE_PIXEL_FORMATS
            if self.supports_pixel_format(pixel_format)
        )

    def supports_pixel_format(self, pixel_format: PixelFormat | str | int) -> bool:
        normalized = normalize_pixel_format(pixel_format)
        return pixel_format_in_bitfield(self.pixel_format_bit_field, normalized)


@dataclass(frozen=True)
class Format7PacketInfo:
    recommended_bytes_per_packet: int
    max_bytes_per_packet: int
    unit_bytes_per_packet: int

    @classmethod
    def from_c(cls, struct: fc2Format7PacketInfo) -> "Format7PacketInfo":
        return cls(
            recommended_bytes_per_packet=int(struct.recommendedBytesPerPacket),
            max_bytes_per_packet=int(struct.maxBytesPerPacket),
            unit_bytes_per_packet=int(struct.unitBytesPerPacket),
        )


@dataclass(frozen=True)
class Format7Configuration:
    settings: Format7ImageSettings
    packet_size: int
    percentage: float


@dataclass(frozen=True)
class Format7Validation:
    settings_are_valid: bool
    packet_info: Format7PacketInfo
    settings: Format7ImageSettings


def normalize_format7_mode(mode: int) -> int:
    normalized = int(mode)
    if normalized < 0 or normalized > 31:
        raise UnsupportedFormat7Error(f"Format7 mode must be in [0, 31], got {mode!r}.")
    return normalized


def build_format7_image_settings(
    info: Format7Info,
    *,
    offset_x: int = 0,
    offset_y: int = 0,
    width: int | None = None,
    height: int | None = None,
    pixel_format: PixelFormat | str | int = PixelFormat.MONO8,
) -> Format7ImageSettings:
    if not info.supported:
        raise UnsupportedFormat7Error(f"Format7 mode {info.mode} is not supported by this camera.")

    normalized_pixel_format = normalize_pixel_format(pixel_format)
    if not info.supports_pixel_format(normalized_pixel_format):
        raise UnsupportedPixelFormatError(
            f"Pixel format {normalized_pixel_format.name} is not supported by Format7 mode {info.mode}."
        )

    normalized_offset_x = int(offset_x)
    normalized_offset_y = int(offset_y)
    normalized_width = info.max_width - normalized_offset_x if width is None else int(width)
    normalized_height = info.max_height - normalized_offset_y if height is None else int(height)
    return Format7ImageSettings(
        mode=info.mode,
        offset_x=normalized_offset_x,
        offset_y=normalized_offset_y,
        width=normalized_width,
        height=normalized_height,
        pixel_format=normalized_pixel_format,
    )


def choose_preferred_pixel_format(
    info: Format7Info,
    *,
    current: PixelFormat | None = None,
) -> PixelFormat:
    if current is not None and info.supports_pixel_format(current):
        return current
    for pixel_format in PREFERRED_DECODABLE_PIXEL_FORMATS:
        if info.supports_pixel_format(pixel_format):
            return pixel_format
    supported = info.supported_pixel_formats
    if supported:
        return supported[0]
    raise UnsupportedPixelFormatError(f"Format7 mode {info.mode} reports no supported pixel formats.")


__all__ = [
    "Format7Configuration",
    "Format7ImageSettings",
    "Format7Info",
    "Format7PacketInfo",
    "Format7Validation",
    "PREFERRED_DECODABLE_PIXEL_FORMATS",
    "build_format7_image_settings",
    "choose_preferred_pixel_format",
    "normalize_format7_mode",
]
