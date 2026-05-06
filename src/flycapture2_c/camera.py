from __future__ import annotations

from dataclasses import dataclass

from .api import FlyCapture2CAPI, get_api
from .bus import CameraDescriptor, guid_to_tuple
from .config import BandwidthAllocation, CameraConfiguration, GrabMode
from .ctypes_defs import fc2CameraInfo, fc2Context, fc2Image, fc2Property
from .errors import (
    CameraStateError,
    FC2ErrorCode,
    FlyCapture2Error,
    Format7ValidationError,
    PropertyModeError,
    PropertyNotWritableError,
    PropertyOutOfRangeError,
    UnsupportedFormat7Error,
    UnsupportedPropertyError,
)
from .format7 import (
    Format7Configuration,
    Format7ImageSettings,
    Format7Info,
    Format7PacketInfo,
    Format7Validation,
    build_format7_image_settings,
    choose_preferred_pixel_format,
    normalize_format7_mode,
)
from .gige import (
    GigEConfig,
    GigEImageBinningSettings,
    GigEImageSettings,
    GigEImageSettingsInfo,
    GigEProperty,
    GigEPropertyType,
    GigEStreamChannelInfo,
    normalize_gige_property_type,
    validate_gige_property_write,
)
from .image import ImageFrame, image_to_frame
from .metadata import (
    CameraStats,
    EmbeddedImageInfo,
    ImageMetadata,
    validate_embedded_image_info_updates,
)
from .pixel_format import PixelFormat, normalize_pixel_format
from .properties import (
    CameraPropertyInfo,
    CameraPropertySnapshot,
    CameraPropertyValue,
    KNOWN_PROPERTY_TYPES,
    PropertyType,
    PropertyWritePolicy,
    normalize_property_type,
)
from .strobe import (
    StrobeControl,
    StrobeInfo,
    normalize_gpio_direction,
    normalize_gpio_pin,
    validate_strobe_read,
    validate_strobe_write,
)
from .trigger import TriggerMode, TriggerModeInfo, validate_trigger_mode_request
from .typing import FrameArray


def _decode_c_string(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace")


def _octets_to_tuple(octets) -> tuple[int, ...]:
    return tuple(int(value) for value in octets)


@dataclass(frozen=True)
class CameraInfo:
    serial_number: int
    interface_type: int
    driver_type: int
    is_color_camera: bool
    model_name: str
    vendor_name: str
    sensor_info: str
    sensor_resolution: str
    driver_name: str
    firmware_version: str
    firmware_build_time: str
    maximum_bus_speed: int
    bayer_tile_format: int
    pcie_bus_speed: int
    node_number: int
    bus_number: int
    iidc_version: int
    config_rom_keyword: str
    gige_major_version: int
    gige_minor_version: int
    user_defined_name: str
    xml_url_1: str
    xml_url_2: str
    mac_address: tuple[int, ...]
    ip_address: tuple[int, ...]
    subnet_mask: tuple[int, ...]
    default_gateway: tuple[int, ...]
    ccp_status: int
    application_ip_address: int
    application_port: int

    @classmethod
    def from_c(cls, info: fc2CameraInfo) -> "CameraInfo":
        return cls(
            serial_number=int(info.serialNumber),
            interface_type=int(info.interfaceType),
            driver_type=int(info.driverType),
            is_color_camera=bool(info.isColorCamera),
            model_name=_decode_c_string(bytes(info.modelName)),
            vendor_name=_decode_c_string(bytes(info.vendorName)),
            sensor_info=_decode_c_string(bytes(info.sensorInfo)),
            sensor_resolution=_decode_c_string(bytes(info.sensorResolution)),
            driver_name=_decode_c_string(bytes(info.driverName)),
            firmware_version=_decode_c_string(bytes(info.firmwareVersion)),
            firmware_build_time=_decode_c_string(bytes(info.firmwareBuildTime)),
            maximum_bus_speed=int(info.maximumBusSpeed),
            bayer_tile_format=int(info.bayerTileFormat),
            pcie_bus_speed=int(info.pcieBusSpeed),
            node_number=int(info.nodeNumber),
            bus_number=int(info.busNumber),
            iidc_version=int(info.iidcVer),
            config_rom_keyword=_decode_c_string(bytes(info.configROM.pszKeyword)),
            gige_major_version=int(info.gigEMajorVersion),
            gige_minor_version=int(info.gigEMinorVersion),
            user_defined_name=_decode_c_string(bytes(info.userDefinedName)),
            xml_url_1=_decode_c_string(bytes(info.xmlURL1)),
            xml_url_2=_decode_c_string(bytes(info.xmlURL2)),
            mac_address=_octets_to_tuple(info.macAddress.octets),
            ip_address=_octets_to_tuple(info.ipAddress.octets),
            subnet_mask=_octets_to_tuple(info.subnetMask.octets),
            default_gateway=_octets_to_tuple(info.defaultGateway.octets),
            ccp_status=int(info.ccpStatus),
            application_ip_address=int(info.applicationIPAddress),
            application_port=int(info.applicationPort),
        )


class Camera:
    def __init__(self, api: FlyCapture2CAPI | None = None) -> None:
        self._api = api or get_api()
        self._context: fc2Context | None = None
        self._image: fc2Image | None = None
        self._capturing = False
        self._connected = False
        self._closed = True
        self._descriptor: CameraDescriptor | None = None
        self._camera_info: CameraInfo | None = None
        self._last_frame: ImageFrame | None = None

    @classmethod
    def open(cls, index: int = 0, api: FlyCapture2CAPI | None = None) -> "Camera":
        camera = cls(api=api)
        camera._open(index=index)
        return camera

    @property
    def is_open(self) -> bool:
        return not self._closed and self._connected

    @property
    def is_capturing(self) -> bool:
        return self._capturing

    @property
    def descriptor(self) -> CameraDescriptor | None:
        return self._descriptor

    @property
    def last_frame(self) -> ImageFrame | None:
        return self._last_frame

    @property
    def camera_info(self) -> CameraInfo | None:
        return self._camera_info

    def _open(self, index: int) -> None:
        if self.is_open:
            raise CameraStateError("Camera is already open.")

        context = self._api.create_context()
        image = None
        connected = False
        try:
            count = self._api.get_num_cameras(context)
            if index < 0 or index >= count:
                raise CameraStateError(f"Camera index {index} is out of range. Found {count} camera(s).")
            guid = self._api.get_camera_from_index(context, index)
            self._api.connect(context, guid)
            connected = True
            image = self._api.create_image()
            self._context = context
            self._image = image
            self._descriptor = CameraDescriptor(index=index, guid=guid_to_tuple(guid))
            self._camera_info = CameraInfo.from_c(self._api.get_camera_info(context))
            self._connected = True
            self._closed = False
        except Exception:
            if image is not None:
                self._suppress_cleanup(self._api.destroy_image, image)
            if connected:
                self._suppress_cleanup(self._api.disconnect, context)
            self._suppress_cleanup(self._api.destroy_context, context)
            raise

    def start(self) -> None:
        self._require_open()
        if self._capturing:
            return
        assert self._context is not None
        self._api.start_capture(self._context)
        self._capturing = True

    def stop(self) -> None:
        if not self._context or not self._connected or not self._capturing:
            self._capturing = False
            return
        self._suppress_cleanup(self._api.stop_capture, self._context)
        self._capturing = False

    def read_frame(self) -> FrameArray:
        """Read one frame and return an owned NumPy array copied out of the SDK buffer."""
        frame = self.read_frame_with_info()
        return frame.array

    def read_frame_with_info(self) -> ImageFrame:
        """Read one frame and return copied pixel data plus metadata.

        The returned array always owns its memory and does not expose the FlyCapture2 SDK buffer.
        """
        self._require_open()
        if not self._capturing:
            raise CameraStateError("Camera capture has not been started.")
        assert self._context is not None
        assert self._image is not None
        self._api.retrieve_buffer(self._context, self._image)
        try:
            metadata = ImageMetadata.from_c(self._api.get_image_metadata(self._image))
        except FlyCapture2Error as exc:
            if exc.code not in {FC2ErrorCode.NOT_IMPLEMENTED, FC2ErrorCode.NOT_SUPPORTED}:
                raise
            metadata = None
        frame = image_to_frame(
            self._image,
            timestamp=self._api.get_image_timestamp(self._image),
            metadata=metadata,
        )
        self._last_frame = frame
        return frame

    def get_camera_info(self, *, refresh: bool = False) -> CameraInfo:
        self._require_open()
        if self._camera_info is None or refresh:
            assert self._context is not None
            self._camera_info = CameraInfo.from_c(self._api.get_camera_info(self._context))
        return self._camera_info

    def get_video_mode_and_frame_rate(self) -> tuple[int, int]:
        self._require_open()
        assert self._context is not None
        return self._api.get_video_mode_and_frame_rate(self._context)

    def get_embedded_image_info(self) -> EmbeddedImageInfo:
        self._require_open()
        assert self._context is not None
        return EmbeddedImageInfo.from_c(self._api.get_embedded_image_info(self._context))

    def set_embedded_image_info(
        self,
        info: EmbeddedImageInfo | None = None,
        *,
        timestamp: bool | None = None,
        gain: bool | None = None,
        shutter: bool | None = None,
        brightness: bool | None = None,
        exposure: bool | None = None,
        white_balance: bool | None = None,
        frame_counter: bool | None = None,
        strobe_pattern: bool | None = None,
        gpio_pin_state: bool | None = None,
        roi_position: bool | None = None,
    ) -> EmbeddedImageInfo:
        self._require_open()
        assert self._context is not None
        base = info or self.get_embedded_image_info()
        updates = {
            "timestamp": timestamp,
            "gain": gain,
            "shutter": shutter,
            "brightness": brightness,
            "exposure": exposure,
            "white_balance": white_balance,
            "frame_counter": frame_counter,
            "strobe_pattern": strobe_pattern,
            "gpio_pin_state": gpio_pin_state,
            "roi_position": roi_position,
        }
        validate_embedded_image_info_updates(base, updates)
        desired = base.with_updates(**updates)
        self._api.set_embedded_image_info(self._context, desired.to_c())
        return self.get_embedded_image_info()

    def get_camera_stats(self) -> CameraStats:
        self._require_open()
        assert self._context is not None
        return CameraStats.from_c(self._api.get_camera_stats(self._context))

    def reset_camera_stats(self) -> None:
        """Reset FlyCapture2 diagnostic counters.

        This is a write-like diagnostic operation and should be used deliberately.
        """
        self._require_open()
        self._api.reset_camera_stats()

    def get_gpio_pin_direction(self, pin: int) -> int:
        """Return GPIO pin direction: 0 for input, 1 for output."""
        self._require_open()
        assert self._context is not None
        normalized_pin = normalize_gpio_pin(pin)
        return self._api.get_gpio_pin_direction(self._context, normalized_pin)

    def set_gpio_pin_direction(
        self,
        pin: int,
        direction: bool | int | str,
        *,
        broadcast: bool = False,
    ) -> int:
        """Set GPIO pin direction and return the read-back direction.

        Direction is 0/input or 1/output. The SDK sets pin direction internally
        for trigger and strobe operations; this method is only for explicit GPIO
        direction control exposed by the FlyCapture2 C API.
        """
        self._require_open()
        assert self._context is not None
        normalized_pin = normalize_gpio_pin(pin)
        normalized = normalize_gpio_direction(direction)
        self._api.set_gpio_pin_direction(self._context, normalized_pin, normalized, broadcast=broadcast)
        return self.get_gpio_pin_direction(normalized_pin)

    def get_strobe_info(self, source: int) -> StrobeInfo:
        self._require_open()
        assert self._context is not None
        return StrobeInfo.from_c(self._api.get_strobe_info(self._context, int(source)))

    def get_strobe(self, source: int) -> StrobeControl:
        self._require_open()
        assert self._context is not None
        info = self.get_strobe_info(source)
        validate_strobe_read(info)
        return StrobeControl.from_c(self._api.get_strobe(self._context, int(source)))

    def set_strobe(
        self,
        source: int | StrobeControl,
        *,
        on: bool | None = None,
        polarity: int | None = None,
        delay: float | None = None,
        duration: float | None = None,
        broadcast: bool = False,
    ) -> StrobeControl:
        self._require_open()
        assert self._context is not None

        if isinstance(source, StrobeControl):
            base = source
            source_id = base.source
        else:
            source_id = int(source)
            base = self.get_strobe(source_id)

        info = self.get_strobe_info(source_id)
        validate_strobe_write(
            info,
            on=on,
            polarity=polarity,
            delay=delay,
            duration=duration,
        )
        desired = base.with_updates(on=on, polarity=polarity, delay=delay, duration=duration)
        self._api.set_strobe(self._context, desired.to_c(), broadcast=broadcast)
        return self.get_strobe(source_id)

    def get_gige_config(self) -> GigEConfig:
        self._require_open()
        assert self._context is not None
        return GigEConfig.from_c(self._api.get_gige_config(self._context))

    def set_gige_config(
        self,
        config: GigEConfig | None = None,
        *,
        enable_packet_resend: bool | None = None,
        register_timeout_retries: int | None = None,
        register_timeout: int | None = None,
    ) -> GigEConfig:
        self._require_open()
        assert self._context is not None
        base = config or self.get_gige_config()
        desired = base.with_updates(
            enable_packet_resend=enable_packet_resend,
            register_timeout_retries=register_timeout_retries,
            register_timeout=register_timeout,
        )
        self._api.set_gige_config(self._context, desired.to_c())
        return self.get_gige_config()

    def get_gige_property(self, property_type: GigEPropertyType | str | int) -> GigEProperty:
        self._require_open()
        assert self._context is not None
        normalized = normalize_gige_property_type(property_type)
        return GigEProperty.from_c(self._api.get_gige_property(self._context, int(normalized)))

    def set_gige_property(
        self,
        property_type: GigEPropertyType | str | int | GigEProperty,
        *,
        value: int | None = None,
    ) -> GigEProperty:
        self._require_open()
        assert self._context is not None
        if isinstance(property_type, GigEProperty):
            base = property_type
        else:
            base = self.get_gige_property(property_type)
        validate_gige_property_write(base, value=value if value is not None else base.value)
        desired = base.with_updates(value=value)
        self._api.set_gige_property(self._context, desired.to_c())
        return self.get_gige_property(desired.property_type)

    def discover_gige_packet_size(self) -> int:
        self._require_open()
        assert self._context is not None
        return self._api.discover_gige_packet_size(self._context)

    def query_gige_imaging_mode(self, mode: int) -> bool:
        self._require_open()
        assert self._context is not None
        return self._api.query_gige_imaging_mode(self._context, int(mode))

    def get_gige_imaging_mode(self) -> int:
        self._require_open()
        assert self._context is not None
        return self._api.get_gige_imaging_mode(self._context)

    def set_gige_imaging_mode(self, mode: int) -> int:
        self._require_open()
        assert self._context is not None
        self._api.set_gige_imaging_mode(self._context, int(mode))
        return self.get_gige_imaging_mode()

    def get_gige_image_settings_info(self) -> GigEImageSettingsInfo:
        self._require_open()
        assert self._context is not None
        return GigEImageSettingsInfo.from_c(self._api.get_gige_image_settings_info(self._context))

    def get_gige_image_settings(self) -> GigEImageSettings:
        self._require_open()
        assert self._context is not None
        return GigEImageSettings.from_c(self._api.get_gige_image_settings(self._context))

    def set_gige_image_settings(
        self,
        settings: GigEImageSettings | None = None,
        *,
        offset_x: int | None = None,
        offset_y: int | None = None,
        width: int | None = None,
        height: int | None = None,
        pixel_format: PixelFormat | str | int | None = None,
    ) -> GigEImageSettings:
        self._require_open()
        assert self._context is not None
        base = settings or self.get_gige_image_settings()
        desired = base.with_updates(
            offset_x=offset_x,
            offset_y=offset_y,
            width=width,
            height=height,
            pixel_format=pixel_format,
        )
        self._api.set_gige_image_settings(self._context, desired.to_c())
        return self.get_gige_image_settings()

    def get_gige_image_binning_settings(self) -> GigEImageBinningSettings:
        self._require_open()
        assert self._context is not None
        horizontal, vertical = self._api.get_gige_image_binning_settings(self._context)
        return GigEImageBinningSettings(horizontal=horizontal, vertical=vertical)

    def set_gige_image_binning_settings(
        self,
        settings: GigEImageBinningSettings | None = None,
        *,
        horizontal: int | None = None,
        vertical: int | None = None,
    ) -> GigEImageBinningSettings:
        self._require_open()
        assert self._context is not None
        base = settings or self.get_gige_image_binning_settings()
        desired = base.with_updates(horizontal=horizontal, vertical=vertical)
        self._api.set_gige_image_binning_settings(self._context, desired.horizontal, desired.vertical)
        return self.get_gige_image_binning_settings()

    def get_num_gige_stream_channels(self) -> int:
        self._require_open()
        assert self._context is not None
        return self._api.get_num_gige_stream_channels(self._context)

    def get_gige_stream_channel_info(self, channel: int = 0) -> GigEStreamChannelInfo:
        self._require_open()
        assert self._context is not None
        return GigEStreamChannelInfo.from_c(self._api.get_gige_stream_channel_info(self._context, int(channel)))

    def get_configuration(self) -> CameraConfiguration:
        self._require_open()
        assert self._context is not None
        return CameraConfiguration.from_c(self._api.get_configuration(self._context))

    def set_configuration(
        self,
        configuration: CameraConfiguration | None = None,
        *,
        num_buffers: int | None = None,
        num_image_notifications: int | None = None,
        grab_timeout: int | None = None,
        grab_mode: GrabMode | str | int | None = None,
        high_performance_retrieve_buffer: bool | None = None,
        isoch_bus_speed: int | None = None,
        async_bus_speed: int | None = None,
        bandwidth_allocation: BandwidthAllocation | str | int | None = None,
        register_timeout_retries: int | None = None,
        register_timeout: int | None = None,
    ) -> CameraConfiguration:
        self._require_open()
        assert self._context is not None
        base = configuration or self.get_configuration()
        updated = base.with_updates(
            num_buffers=num_buffers,
            num_image_notifications=num_image_notifications,
            grab_timeout=grab_timeout,
            grab_mode=grab_mode,
            high_performance_retrieve_buffer=high_performance_retrieve_buffer,
            isoch_bus_speed=isoch_bus_speed,
            async_bus_speed=async_bus_speed,
            bandwidth_allocation=bandwidth_allocation,
            register_timeout_retries=register_timeout_retries,
            register_timeout=register_timeout,
        )
        self._api.set_configuration(self._context, updated.to_c())
        return self.get_configuration()

    def set_grab_timeout(self, ms: int) -> CameraConfiguration:
        """Set the SDK-level RetrieveBuffer grab timeout in milliseconds."""
        return self.set_configuration(grab_timeout=int(ms))

    def set_grab_mode(self, mode: GrabMode | str | int) -> CameraConfiguration:
        return self.set_configuration(grab_mode=mode)

    def get_format7_info(self, mode: int = 0) -> Format7Info:
        self._require_open()
        assert self._context is not None
        info, supported = self._api.get_format7_info(self._context, normalize_format7_mode(mode))
        return Format7Info.from_c(info, supported=supported)

    def get_format7_configuration(self) -> Format7Configuration:
        self._require_open()
        assert self._context is not None
        settings, packet_size, percentage = self._api.get_format7_configuration(self._context)
        return Format7Configuration(
            settings=Format7ImageSettings.from_c(settings),
            packet_size=packet_size,
            percentage=percentage,
        )

    def validate_format7(
        self,
        *,
        mode: int = 0,
        offset_x: int = 0,
        offset_y: int = 0,
        width: int | None = None,
        height: int | None = None,
        pixel_format: PixelFormat | str | int = "MONO8",
    ) -> Format7Validation:
        self._require_open()
        assert self._context is not None
        info = self.get_format7_info(mode=mode)
        settings = build_format7_image_settings(
            info,
            offset_x=offset_x,
            offset_y=offset_y,
            width=width,
            height=height,
            pixel_format=pixel_format,
        )
        settings_are_valid, packet_info = self._api.validate_format7_settings(self._context, settings.to_c())
        return Format7Validation(
            settings_are_valid=settings_are_valid,
            packet_info=Format7PacketInfo.from_c(packet_info),
            settings=settings,
        )

    def set_format7(
        self,
        *,
        mode: int = 0,
        offset_x: int = 0,
        offset_y: int = 0,
        width: int | None = None,
        height: int | None = None,
        pixel_format: PixelFormat | str | int = "MONO8",
        packet_size: int | None = None,
    ) -> Format7Configuration:
        validation = self.validate_format7(
            mode=mode,
            offset_x=offset_x,
            offset_y=offset_y,
            width=width,
            height=height,
            pixel_format=pixel_format,
        )
        if not validation.settings_are_valid:
            raise Format7ValidationError(f"Format7 settings are not valid: {validation.settings!r}")
        assert self._context is not None
        selected_packet_size = (
            validation.packet_info.recommended_bytes_per_packet if packet_size is None else int(packet_size)
        )
        self._api.set_format7_configuration_packet(self._context, validation.settings.to_c(), selected_packet_size)
        return self.get_format7_configuration()

    def set_roi(
        self,
        *,
        offset_x: int = 0,
        offset_y: int = 0,
        width: int | None = None,
        height: int | None = None,
        mode: int = 0,
    ) -> Format7Configuration:
        info = self.get_format7_info(mode=mode)
        pixel_format = self._choose_format7_pixel_format_for_mode(info)
        return self.set_format7(
            mode=mode,
            offset_x=offset_x,
            offset_y=offset_y,
            width=width,
            height=height,
            pixel_format=pixel_format,
        )

    def set_pixel_format(self, pixel_format: PixelFormat | str | int, *, mode: int = 0) -> Format7Configuration:
        info = self.get_format7_info(mode=mode)
        normalized = normalize_pixel_format(pixel_format)
        settings = self._format7_base_settings_for_mode(info, pixel_format=normalized)
        return self.set_format7(
            mode=mode,
            offset_x=settings.offset_x,
            offset_y=settings.offset_y,
            width=settings.width,
            height=settings.height,
            pixel_format=settings.pixel_format,
        )

    def get_trigger_mode_info(self) -> TriggerModeInfo:
        self._require_open()
        assert self._context is not None
        return TriggerModeInfo.from_c(self._api.get_trigger_mode_info(self._context))

    def get_trigger_mode(self) -> TriggerMode:
        self._require_open()
        assert self._context is not None
        return TriggerMode.from_c(self._api.get_trigger_mode(self._context))

    def set_trigger_mode(
        self,
        trigger_mode: TriggerMode | None = None,
        *,
        on_off: bool | None = None,
        polarity: int | None = None,
        source: int | None = None,
        mode: int | None = None,
        parameter: int | None = None,
        broadcast: bool = False,
    ) -> TriggerMode:
        self._require_open()
        assert self._context is not None

        changed_fields = {
            field_name
            for field_name, value in (
                ("on_off", on_off),
                ("polarity", polarity),
                ("source", source),
                ("mode", mode),
                ("parameter", parameter),
            )
            if value is not None
        }
        if trigger_mode is None:
            desired = self.get_trigger_mode().with_updates(
                on_off=on_off,
                polarity=polarity,
                source=source,
                mode=mode,
                parameter=parameter,
            )
        else:
            # A TriggerMode captured from the SDK must remain restorable even if a
            # camera reports incomplete masks. Explicit keyword overrides are still checked.
            desired = trigger_mode.with_updates(
                on_off=on_off,
                polarity=polarity,
                source=source,
                mode=mode,
                parameter=parameter,
            )

        info = self.get_trigger_mode_info()
        validate_trigger_mode_request(info, desired, changed_fields=changed_fields)
        if broadcast:
            self._api.set_trigger_mode_broadcast(self._context, desired.to_c())
        else:
            self._api.set_trigger_mode(self._context, desired.to_c())
        return self.get_trigger_mode()

    def enable_trigger(
        self,
        *,
        source: int = 0,
        mode: int = 0,
        parameter: int = 0,
        polarity: int | None = None,
        broadcast: bool = False,
    ) -> TriggerMode:
        updates: dict[str, int | bool] = {
            "on_off": True,
            "source": int(source),
            "mode": int(mode),
            "parameter": int(parameter),
        }
        if polarity is not None:
            updates["polarity"] = int(polarity)
        return self.set_trigger_mode(broadcast=broadcast, **updates)

    def disable_trigger(self, *, broadcast: bool = False) -> TriggerMode:
        return self.set_trigger_mode(on_off=False, broadcast=broadcast)

    def fire_software_trigger(self, *, broadcast: bool = False) -> None:
        """Fire the SDK software trigger primitive.

        This does not configure trigger mode, start capture, retrieve a frame,
        sleep, or poll. Callers are responsible for the surrounding camera
        state and timing.
        """
        self._require_open()
        assert self._context is not None
        self._api.fire_software_trigger(self._context, broadcast=broadcast)

    def get_property_info(self, property_type: PropertyType | str | int) -> CameraPropertyInfo:
        self._require_open()
        assert self._context is not None
        normalized = normalize_property_type(property_type)
        return CameraPropertyInfo.from_c(self._api.get_property_info(self._context, int(normalized)))

    def get_property(self, property_type: PropertyType | str | int) -> CameraPropertyValue:
        self._require_open()
        assert self._context is not None
        normalized = normalize_property_type(property_type)
        return CameraPropertyValue.from_c(self._api.get_property(self._context, int(normalized)))

    def get_property_raw(self, property_type: PropertyType | str | int) -> fc2Property:
        """Return the raw `fc2Property` structure for advanced callers."""
        self._require_open()
        assert self._context is not None
        normalized = normalize_property_type(property_type)
        return self._api.get_property(self._context, int(normalized))

    def set_property(
        self,
        property_type: PropertyType | str | int,
        *,
        auto_manual_mode: bool | None = None,
        on_off: bool | None = None,
        abs_control: bool | None = None,
        one_push: bool | None = None,
        value_a: int | None = None,
        value_b: int | None = None,
        abs_value: float | None = None,
        policy: PropertyWritePolicy = PropertyWritePolicy.STRICT,
    ) -> CameraPropertyValue:
        """Advanced API.

        Generic callers should prefer `set_property_abs()`, `set_property_integer()`,
        `set_property_on_off()`, `set_property_auto()`, or `set_property_one_push()`.
        `policy="raw"` bypasses high-level capability and range checks but still checks
        SDK return codes.
        """
        self._require_open()
        assert self._context is not None
        normalized = normalize_property_type(property_type)
        prop_info = self.get_property_info(normalized)
        if policy == PropertyWritePolicy.STRICT:
            self._validate_property_write_request(
                normalized,
                prop_info,
                auto_manual_mode=auto_manual_mode,
                on_off=on_off,
                abs_control=abs_control,
                one_push=one_push,
                value_a=value_a,
                value_b=value_b,
                abs_value=abs_value,
            )

        prop = self._api.get_property(self._context, int(normalized))
        self._apply_property_update(
            prop,
            prop_info,
            auto_manual_mode=auto_manual_mode,
            on_off=on_off,
            abs_control=abs_control,
            one_push=one_push,
            value_a=value_a,
            value_b=value_b,
            abs_value=abs_value,
        )
        self._api.set_property(self._context, prop)
        return CameraPropertyValue.from_c(self._api.get_property(self._context, int(normalized)))

    def set_property_raw(
        self,
        property_type: PropertyType | str | int,
        *,
        auto_manual_mode: bool | None = None,
        on_off: bool | None = None,
        abs_control: bool | None = None,
        one_push: bool | None = None,
        value_a: int | None = None,
        value_b: int | None = None,
        abs_value: float | None = None,
    ) -> CameraPropertyValue:
        """Low-policy property write close to `fc2Property`.

        This is intended for advanced callers. It bypasses high-level range and capability checks,
        but all SDK return codes are still checked.
        """
        return self.set_property(
            property_type,
            auto_manual_mode=auto_manual_mode,
            on_off=on_off,
            abs_control=abs_control,
            one_push=one_push,
            value_a=value_a,
            value_b=value_b,
            abs_value=abs_value,
            policy=PropertyWritePolicy.RAW,
        )

    def set_property_abs(
        self,
        property_type: PropertyType | str | int,
        value: float,
        *,
        auto: bool = False,
        on: bool | None = True,
    ) -> CameraPropertyValue:
        return self.set_property(
            property_type,
            auto_manual_mode=auto,
            on_off=on,
            abs_control=True,
            abs_value=float(value),
            policy=PropertyWritePolicy.STRICT,
        )

    def set_property_integer(
        self,
        property_type: PropertyType | str | int,
        *,
        value_a: int | None = None,
        value_b: int | None = None,
        auto: bool = False,
        on: bool | None = True,
    ) -> CameraPropertyValue:
        if value_a is None and value_b is None:
            raise ValueError("At least one of value_a or value_b must be provided.")
        return self.set_property(
            property_type,
            auto_manual_mode=auto,
            on_off=on,
            abs_control=False,
            value_a=value_a,
            value_b=value_b,
            policy=PropertyWritePolicy.STRICT,
        )

    def set_property_on_off(self, property_type: PropertyType | str | int, *, on: bool = True) -> CameraPropertyValue:
        return self.set_property(
            property_type,
            on_off=on,
            policy=PropertyWritePolicy.STRICT,
        )

    def set_property_auto(self, property_type: PropertyType | str | int, *, auto: bool = True) -> CameraPropertyValue:
        return self.set_property(
            property_type,
            auto_manual_mode=auto,
            policy=PropertyWritePolicy.STRICT,
        )

    def set_property_one_push(self, property_type: PropertyType | str | int) -> CameraPropertyValue:
        return self.set_property(
            property_type,
            one_push=True,
            policy=PropertyWritePolicy.STRICT,
        )

    def list_property_infos(self) -> tuple[CameraPropertyInfo, ...]:
        return tuple(self.get_property_info(property_type) for property_type in KNOWN_PROPERTY_TYPES)

    def list_properties(self) -> tuple[CameraPropertyValue, ...]:
        values: list[CameraPropertyValue] = []
        for info in self.list_property_infos():
            if info.present and info.read_out_supported:
                values.append(self.get_property(info.property_type))
        return tuple(values)

    def snapshot_properties(self) -> tuple[CameraPropertySnapshot, ...]:
        snapshots: list[CameraPropertySnapshot] = []
        for property_type in KNOWN_PROPERTY_TYPES:
            try:
                info = self.get_property_info(property_type)
                value = self.get_property(property_type) if info.present and info.read_out_supported else None
                snapshots.append(CameraPropertySnapshot(property_type=property_type, info=info, value=value))
            except FlyCapture2Error as exc:
                snapshots.append(
                    CameraPropertySnapshot(
                        property_type=property_type,
                        info=None,
                        value=None,
                        error=str(exc),
                    )
                )
        return tuple(snapshots)

    def get_exposure(self) -> CameraPropertyValue:
        """Return FlyCapture2 `AUTO_EXPOSURE` property state.

        This is the SDK's exposure-related property, not a synonym for shutter.
        """
        return self.get_property(PropertyType.AUTO_EXPOSURE)

    def set_exposure(self, value: float, *, auto: bool = False) -> CameraPropertyValue:
        """Set FlyCapture2 `AUTO_EXPOSURE`.

        This controls the SDK's auto-exposure property. It is distinct from shutter and gain.
        """
        return self._set_supported_absolute_property(PropertyType.AUTO_EXPOSURE, value, auto=auto)

    def get_shutter(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.SHUTTER)

    def set_shutter(self, value: float, *, auto: bool = False) -> CameraPropertyValue:
        return self._set_supported_absolute_property(PropertyType.SHUTTER, value, auto=auto)

    def get_gain(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.GAIN)

    def set_gain(self, value: float, *, auto: bool = False) -> CameraPropertyValue:
        return self._set_supported_absolute_property(PropertyType.GAIN, value, auto=auto)

    def get_frame_rate(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.FRAME_RATE)

    def set_frame_rate(self, value: float, *, auto: bool = False) -> CameraPropertyValue:
        return self._set_supported_absolute_property(PropertyType.FRAME_RATE, value, auto=auto)

    def get_brightness(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.BRIGHTNESS)

    def set_brightness(self, value: float, *, auto: bool = False) -> CameraPropertyValue:
        return self._set_supported_absolute_property(PropertyType.BRIGHTNESS, value, auto=auto)

    def get_gamma(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.GAMMA)

    def set_gamma(self, value: float, *, auto: bool = False) -> CameraPropertyValue:
        return self._set_supported_absolute_property(PropertyType.GAMMA, value, auto=auto)

    def get_white_balance(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.WHITE_BALANCE)

    def set_white_balance(
        self,
        value_a: int,
        value_b: int,
        *,
        auto: bool = False,
        on: bool | None = True,
    ) -> CameraPropertyValue:
        return self.set_property_integer(
            PropertyType.WHITE_BALANCE,
            value_a=value_a,
            value_b=value_b,
            auto=auto,
            on=on,
        )

    def get_trigger_delay(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.TRIGGER_DELAY)

    def set_trigger_delay(self, value: float, *, auto: bool = False) -> CameraPropertyValue:
        return self._set_supported_absolute_property(PropertyType.TRIGGER_DELAY, value, auto=auto)

    def get_temperature(self) -> CameraPropertyValue:
        return self.get_property(PropertyType.TEMPERATURE)

    def _set_supported_absolute_property(
        self,
        property_type: PropertyType,
        value: float,
        *,
        auto: bool = False,
    ) -> CameraPropertyValue:
        prop_info = self.get_property_info(property_type)
        return self.set_property_abs(
            property_type,
            value,
            auto=auto,
            on=True if prop_info.on_off_supported else None,
        )

    def _format7_base_settings_for_mode(
        self,
        info: Format7Info,
        *,
        pixel_format: PixelFormat,
    ) -> Format7ImageSettings:
        if not info.supported:
            raise UnsupportedFormat7Error(f"Format7 mode {info.mode} is not supported by this camera.")
        try:
            current = self.get_format7_configuration()
            if current.settings.mode == info.mode:
                return Format7ImageSettings(
                    mode=info.mode,
                    offset_x=current.settings.offset_x,
                    offset_y=current.settings.offset_y,
                    width=current.settings.width,
                    height=current.settings.height,
                    pixel_format=pixel_format,
                )
        except FlyCapture2Error:
            pass
        return build_format7_image_settings(info, pixel_format=pixel_format)

    def _choose_format7_pixel_format_for_mode(self, info: Format7Info) -> PixelFormat:
        try:
            current = self.get_format7_configuration()
            if current.settings.mode == info.mode:
                return choose_preferred_pixel_format(info, current=current.settings.pixel_format)
        except FlyCapture2Error:
            pass
        return choose_preferred_pixel_format(info)

    @staticmethod
    def _validate_property_write_request(
        property_type: PropertyType,
        prop_info: CameraPropertyInfo,
        *,
        auto_manual_mode: bool | None,
        on_off: bool | None,
        abs_control: bool | None,
        one_push: bool | None,
        value_a: int | None,
        value_b: int | None,
        abs_value: float | None,
    ) -> None:
        if not prop_info.present:
            raise UnsupportedPropertyError(f"Property {property_type.name} is not present on this camera.")
        if not prop_info.writable:
            raise PropertyNotWritableError(f"Property {property_type.name} is present but not writable.")

        if auto_manual_mode is True and not prop_info.auto_supported:
            raise PropertyModeError(f"Property {property_type.name} does not support auto mode.")
        if auto_manual_mode is False and (
            abs_value is not None or value_a is not None or value_b is not None
        ) and not prop_info.manual_supported:
            raise PropertyNotWritableError(f"Property {property_type.name} does not support manual writes.")
        if on_off is not None and not prop_info.on_off_supported:
            raise PropertyModeError(f"Property {property_type.name} does not support on/off control.")
        if one_push is True and not prop_info.one_push_supported:
            raise PropertyModeError(f"Property {property_type.name} does not support one-push control.")
        if abs_control is True and not prop_info.abs_val_supported:
            raise PropertyModeError(f"Property {property_type.name} does not support absolute control.")
        if abs_value is not None:
            if not prop_info.abs_val_supported:
                raise PropertyModeError(f"Property {property_type.name} does not support absolute values.")
            if not (prop_info.abs_min <= float(abs_value) <= prop_info.abs_max):
                raise PropertyOutOfRangeError(
                    f"Property {property_type.name} absolute value {abs_value} is outside "
                    f"[{prop_info.abs_min}, {prop_info.abs_max}]."
                )
        for field_name, value in (("valueA", value_a), ("valueB", value_b)):
            if value is None:
                continue
            if not (prop_info.min_value <= int(value) <= prop_info.max_value):
                raise PropertyOutOfRangeError(
                    f"Property {property_type.name} {field_name} {value} is outside "
                    f"[{prop_info.min_value}, {prop_info.max_value}]."
                )

    @staticmethod
    def _apply_property_update(
        prop: fc2Property,
        prop_info: CameraPropertyInfo,
        *,
        auto_manual_mode: bool | None,
        on_off: bool | None,
        abs_control: bool | None,
        one_push: bool | None,
        value_a: int | None,
        value_b: int | None,
        abs_value: float | None,
    ) -> None:
        if auto_manual_mode is not None:
            if auto_manual_mode and not prop_info.auto_supported:
                raise PropertyModeError(f"Property {prop_info.property_type.name} does not support auto mode.")
            if not auto_manual_mode and not prop_info.manual_supported:
                raise PropertyNotWritableError(f"Property {prop_info.property_type.name} does not support manual mode.")
            prop.autoManualMode = int(auto_manual_mode)
        if on_off is not None:
            if not prop_info.on_off_supported:
                raise PropertyModeError(f"Property {prop_info.property_type.name} does not support on/off control.")
            prop.onOff = int(on_off)
        if one_push is not None:
            if one_push and not prop_info.one_push_supported:
                raise PropertyModeError(f"Property {prop_info.property_type.name} does not support one-push control.")
            prop.onePush = int(one_push)
        if abs_control is not None:
            if abs_control and not prop_info.abs_val_supported:
                raise PropertyModeError(f"Property {prop_info.property_type.name} does not support absolute control.")
            prop.absControl = int(abs_control)
        if value_a is not None:
            prop.valueA = int(value_a)
        if value_b is not None:
            prop.valueB = int(value_b)
        if abs_value is not None:
            if not prop_info.abs_val_supported:
                raise PropertyModeError(f"Property {prop_info.property_type.name} does not support absolute values.")
            prop.absControl = 1
            prop.absValue = float(abs_value)

    def close(self) -> None:
        if self._closed:
            return

        self.stop()
        if self._context is not None and self._connected:
            self._suppress_cleanup(self._api.disconnect, self._context)
            self._connected = False
        if self._image is not None:
            self._suppress_cleanup(self._api.destroy_image, self._image)
            self._image = None
        if self._context is not None:
            self._suppress_cleanup(self._api.destroy_context, self._context)
            self._context = None
        self._camera_info = None
        self._closed = True

    def _require_open(self) -> None:
        if not self.is_open or self._context is None:
            raise CameraStateError("Camera is not open.")

    @staticmethod
    def _suppress_cleanup(func, *args) -> None:
        try:
            func(*args)
        except FlyCapture2Error as exc:
            if exc.code in {
                FC2ErrorCode.NOT_CONNECTED,
                FC2ErrorCode.ISOCH_NOT_STARTED,
                FC2ErrorCode.ISOCH_ALREADY_STARTED,
            }:
                return
            raise

    def __enter__(self) -> "Camera":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
