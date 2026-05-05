from __future__ import annotations

from dataclasses import dataclass

from .api import FlyCapture2CAPI, get_api
from .bus import CameraDescriptor, guid_to_tuple
from .ctypes_defs import fc2CameraInfo, fc2Context, fc2Image, fc2Property
from .errors import (
    CameraStateError,
    FC2ErrorCode,
    FlyCapture2Error,
    PropertyModeError,
    PropertyNotWritableError,
    PropertyOutOfRangeError,
    UnsupportedPropertyError,
)
from .image import ImageFrame, image_to_frame
from .properties import (
    CameraPropertyInfo,
    CameraPropertyValue,
    PropertyType,
    PropertyWritePolicy,
    SUPPORTED_HIGH_LEVEL_WRITE_PROPERTIES,
    normalize_property_type,
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
        frame = image_to_frame(self._image, timestamp=self._api.get_image_timestamp(self._image))
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

        High-level callers should prefer `set_exposure()`, `set_shutter()`, `set_gain()`,
        and `set_frame_rate()`. `policy="raw"` bypasses high-level safety checks.
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
                require_whitelist=False,
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

    def _set_supported_absolute_property(
        self,
        property_type: PropertyType,
        value: float,
        *,
        auto: bool = False,
    ) -> CameraPropertyValue:
        self._require_open()
        assert self._context is not None
        prop_info = self.get_property_info(property_type)
        self._validate_property_write_request(
            property_type,
            prop_info,
            auto_manual_mode=auto,
            on_off=None,
            abs_control=True,
            one_push=None,
            value_a=None,
            value_b=None,
            abs_value=value,
            require_whitelist=True,
        )
        prop = self._api.get_property(self._context, int(property_type))
        prop.onOff = 1 if prop_info.on_off_supported else prop.onOff
        prop.onePush = 0
        prop.absControl = 1
        prop.autoManualMode = 1 if auto else 0
        prop.absValue = float(value)
        self._api.set_property(self._context, prop)
        return CameraPropertyValue.from_c(self._api.get_property(self._context, int(property_type)))

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
        require_whitelist: bool,
    ) -> None:
        if require_whitelist and property_type not in SUPPORTED_HIGH_LEVEL_WRITE_PROPERTIES:
            raise UnsupportedPropertyError(
                f"Property {property_type.name} is not supported by the high-level write API."
            )
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
        if one_push is not None and not prop_info.one_push_supported:
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
            if not prop_info.one_push_supported:
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
