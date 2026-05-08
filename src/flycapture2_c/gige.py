from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .errors import GigEConfigurationError, UnsupportedGigEError
from .pixel_format import (
    CONFIGURABLE_PIXEL_FORMATS,
    PixelFormat,
    configurable_from_sdk_value,
    normalize_pixel_format,
    pixel_format_in_bitfield,
)
from .raw.structs import (
    fc2GigEConfig,
    fc2GigEImageSettings,
    fc2GigEImageSettingsInfo,
    fc2GigEProperty,
    fc2GigEStreamChannel,
)


class GigEPropertyType(IntEnum):
    HEARTBEAT = 0
    HEARTBEAT_TIMEOUT = 1
    PACKET_SIZE = 2
    PACKET_DELAY = 3


def normalize_gige_property_type(value: GigEPropertyType | str | int) -> GigEPropertyType:
    if isinstance(value, GigEPropertyType):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper().replace(" ", "_").replace("-", "_")
        return GigEPropertyType[normalized]
    return GigEPropertyType(int(value))


def _ip_address_to_tuple(address) -> tuple[int, int, int, int]:
    return tuple(int(value) for value in address.octets)  # type: ignore[return-value]


def _tuple_to_ip_address(values: tuple[int, int, int, int]):
    from .raw.structs import fc2IPAddress

    if len(values) != 4:
        raise GigEConfigurationError(f"IPv4 address must contain 4 octets, got {values!r}.")
    address = fc2IPAddress()
    octets = [int(value) for value in values]
    if any(value < 0 or value > 255 for value in octets):
        raise GigEConfigurationError(f"IPv4 octets must be in [0, 255], got {values!r}.")
    address.octets[:] = octets
    return address


@dataclass(frozen=True)
class GigEProperty:
    property_type: GigEPropertyType
    readable: bool
    writable: bool
    min_value: int
    max_value: int
    value: int

    @classmethod
    def from_c(cls, prop: fc2GigEProperty) -> "GigEProperty":
        return cls(
            property_type=GigEPropertyType(int(prop.propType)),
            readable=bool(prop.isReadable),
            writable=bool(prop.isWritable),
            min_value=int(prop.min),
            max_value=int(prop.max),
            value=int(prop.value),
        )

    def to_c(self) -> fc2GigEProperty:
        prop = fc2GigEProperty()
        prop.propType = int(self.property_type)
        prop.isReadable = int(self.readable)
        prop.isWritable = int(self.writable)
        prop.min = int(self.min_value)
        prop.max = int(self.max_value)
        prop.value = int(self.value)
        return prop

    def with_updates(self, *, value: int | None = None) -> "GigEProperty":
        return GigEProperty(
            property_type=self.property_type,
            readable=self.readable,
            writable=self.writable,
            min_value=self.min_value,
            max_value=self.max_value,
            value=self.value if value is None else int(value),
        )


@dataclass(frozen=True)
class GigEConfig:
    enable_packet_resend: bool
    register_timeout_retries: int
    register_timeout: int

    @classmethod
    def from_c(cls, config: fc2GigEConfig) -> "GigEConfig":
        return cls(
            enable_packet_resend=bool(config.enablePacketResend),
            register_timeout_retries=int(config.registerTimeoutRetries),
            register_timeout=int(config.registerTimeout),
        )

    def to_c(self) -> fc2GigEConfig:
        config = fc2GigEConfig()
        config.enablePacketResend = int(self.enable_packet_resend)
        config.registerTimeoutRetries = int(self.register_timeout_retries)
        config.registerTimeout = int(self.register_timeout)
        return config

    def with_updates(
        self,
        *,
        enable_packet_resend: bool | None = None,
        register_timeout_retries: int | None = None,
        register_timeout: int | None = None,
    ) -> "GigEConfig":
        return GigEConfig(
            enable_packet_resend=(
                self.enable_packet_resend if enable_packet_resend is None else bool(enable_packet_resend)
            ),
            register_timeout_retries=(
                self.register_timeout_retries
                if register_timeout_retries is None
                else int(register_timeout_retries)
            ),
            register_timeout=self.register_timeout if register_timeout is None else int(register_timeout),
        )


@dataclass(frozen=True)
class GigEImageSettingsInfo:
    max_width: int
    max_height: int
    offset_h_step_size: int
    offset_v_step_size: int
    image_h_step_size: int
    image_v_step_size: int
    pixel_format_bit_field: int
    vendor_pixel_format_bit_field: int

    @classmethod
    def from_c(cls, info: fc2GigEImageSettingsInfo) -> "GigEImageSettingsInfo":
        return cls(
            max_width=int(info.maxWidth),
            max_height=int(info.maxHeight),
            offset_h_step_size=int(info.offsetHStepSize),
            offset_v_step_size=int(info.offsetVStepSize),
            image_h_step_size=int(info.imageHStepSize),
            image_v_step_size=int(info.imageVStepSize),
            pixel_format_bit_field=int(info.pixelFormatBitField),
            vendor_pixel_format_bit_field=int(info.vendorPixelFormatBitField),
        )

    @property
    def supported_pixel_formats(self) -> tuple[PixelFormat, ...]:
        return tuple(
            pixel_format for pixel_format in CONFIGURABLE_PIXEL_FORMATS if self.supports_pixel_format(pixel_format)
        )

    def supports_pixel_format(self, pixel_format: PixelFormat | str | int) -> bool:
        normalized = normalize_pixel_format(pixel_format)
        return pixel_format_in_bitfield(self.pixel_format_bit_field, normalized)


@dataclass(frozen=True)
class GigEImageSettings:
    offset_x: int
    offset_y: int
    width: int
    height: int
    pixel_format: PixelFormat

    @classmethod
    def from_c(cls, settings: fc2GigEImageSettings) -> "GigEImageSettings":
        return cls(
            offset_x=int(settings.offsetX),
            offset_y=int(settings.offsetY),
            width=int(settings.width),
            height=int(settings.height),
            pixel_format=configurable_from_sdk_value(int(settings.pixelFormat)),
        )

    def to_c(self) -> fc2GigEImageSettings:
        settings = fc2GigEImageSettings()
        settings.offsetX = int(self.offset_x)
        settings.offsetY = int(self.offset_y)
        settings.width = int(self.width)
        settings.height = int(self.height)
        settings.pixelFormat = int(self.pixel_format)
        return settings

    def with_updates(
        self,
        *,
        offset_x: int | None = None,
        offset_y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        pixel_format: PixelFormat | str | int | None = None,
    ) -> "GigEImageSettings":
        return GigEImageSettings(
            offset_x=self.offset_x if offset_x is None else int(offset_x),
            offset_y=self.offset_y if offset_y is None else int(offset_y),
            width=self.width if width is None else int(width),
            height=self.height if height is None else int(height),
            pixel_format=self.pixel_format if pixel_format is None else normalize_pixel_format(pixel_format),
        )


@dataclass(frozen=True)
class GigEImageBinningSettings:
    horizontal: int
    vertical: int

    def with_updates(
        self,
        *,
        horizontal: int | None = None,
        vertical: int | None = None,
    ) -> "GigEImageBinningSettings":
        return GigEImageBinningSettings(
            horizontal=self.horizontal if horizontal is None else int(horizontal),
            vertical=self.vertical if vertical is None else int(vertical),
        )


@dataclass(frozen=True)
class GigEStreamChannelInfo:
    network_interface_index: int
    host_port: int
    do_not_fragment: bool
    packet_size: int
    inter_packet_delay: int
    destination_ip_address: tuple[int, int, int, int]
    source_port: int

    @classmethod
    def from_c(cls, channel: fc2GigEStreamChannel) -> "GigEStreamChannelInfo":
        return cls(
            network_interface_index=int(channel.networkInterfaceIndex),
            host_port=int(channel.hostPort),
            do_not_fragment=bool(channel.doNotFragment),
            packet_size=int(channel.packetSize),
            inter_packet_delay=int(channel.interPacketDelay),
            destination_ip_address=_ip_address_to_tuple(channel.destinationIpAddress),
            source_port=int(channel.sourcePort),
        )

    def to_c(self) -> fc2GigEStreamChannel:
        channel = fc2GigEStreamChannel()
        channel.networkInterfaceIndex = int(self.network_interface_index)
        channel.hostPort = int(self.host_port)
        channel.doNotFragment = int(self.do_not_fragment)
        channel.packetSize = int(self.packet_size)
        channel.interPacketDelay = int(self.inter_packet_delay)
        channel.destinationIpAddress = _tuple_to_ip_address(self.destination_ip_address)
        channel.sourcePort = int(self.source_port)
        return channel


def validate_gige_property_write(prop: GigEProperty, *, value: int | None) -> None:
    if value is None:
        return
    if not prop.readable:
        raise UnsupportedGigEError(f"GigE property {prop.property_type.name} is not readable.")
    if not prop.writable:
        raise GigEConfigurationError(f"GigE property {prop.property_type.name} is not writable.")
    if not (prop.min_value <= int(value) <= prop.max_value):
        raise GigEConfigurationError(
            f"GigE property {prop.property_type.name} value {value} is outside "
            f"[{prop.min_value}, {prop.max_value}]."
        )


__all__ = [
    "GigEConfig",
    "GigEImageBinningSettings",
    "GigEImageSettings",
    "GigEImageSettingsInfo",
    "GigEProperty",
    "GigEPropertyType",
    "GigEStreamChannelInfo",
    "normalize_gige_property_type",
    "validate_gige_property_write",
]
