from __future__ import annotations

from dataclasses import dataclass

from .ctypes_defs import fc2ImageMetadata
from .errors import UnsupportedMetadataError
from .raw.structs import fc2CameraStats, fc2EmbeddedImageInfo, fc2EmbeddedImageInfoProperty


EMBEDDED_IMAGE_FIELDS = (
    "timestamp",
    "gain",
    "shutter",
    "brightness",
    "exposure",
    "white_balance",
    "frame_counter",
    "strobe_pattern",
    "gpio_pin_state",
    "roi_position",
)

_C_FIELD_BY_NAME = {
    "timestamp": "timestamp",
    "gain": "gain",
    "shutter": "shutter",
    "brightness": "brightness",
    "exposure": "exposure",
    "white_balance": "whiteBalance",
    "frame_counter": "frameCounter",
    "strobe_pattern": "strobePattern",
    "gpio_pin_state": "GPIOPinState",
    "roi_position": "ROIPosition",
}


@dataclass(frozen=True)
class EmbeddedImageField:
    available: bool
    on_off: bool

    @classmethod
    def from_c(cls, field: fc2EmbeddedImageInfoProperty) -> "EmbeddedImageField":
        return cls(available=bool(field.available), on_off=bool(field.onOff))

    def to_c(self) -> fc2EmbeddedImageInfoProperty:
        field = fc2EmbeddedImageInfoProperty()
        field.available = int(self.available)
        field.onOff = int(self.on_off)
        return field

    def with_on_off(self, on_off: bool) -> "EmbeddedImageField":
        return EmbeddedImageField(available=self.available, on_off=bool(on_off))


@dataclass(frozen=True)
class EmbeddedImageInfo:
    timestamp: EmbeddedImageField
    gain: EmbeddedImageField
    shutter: EmbeddedImageField
    brightness: EmbeddedImageField
    exposure: EmbeddedImageField
    white_balance: EmbeddedImageField
    frame_counter: EmbeddedImageField
    strobe_pattern: EmbeddedImageField
    gpio_pin_state: EmbeddedImageField
    roi_position: EmbeddedImageField

    @classmethod
    def from_c(cls, info: fc2EmbeddedImageInfo) -> "EmbeddedImageInfo":
        return cls(
            timestamp=EmbeddedImageField.from_c(info.timestamp),
            gain=EmbeddedImageField.from_c(info.gain),
            shutter=EmbeddedImageField.from_c(info.shutter),
            brightness=EmbeddedImageField.from_c(info.brightness),
            exposure=EmbeddedImageField.from_c(info.exposure),
            white_balance=EmbeddedImageField.from_c(info.whiteBalance),
            frame_counter=EmbeddedImageField.from_c(info.frameCounter),
            strobe_pattern=EmbeddedImageField.from_c(info.strobePattern),
            gpio_pin_state=EmbeddedImageField.from_c(info.GPIOPinState),
            roi_position=EmbeddedImageField.from_c(info.ROIPosition),
        )

    def to_c(self) -> fc2EmbeddedImageInfo:
        info = fc2EmbeddedImageInfo()
        for name in EMBEDDED_IMAGE_FIELDS:
            setattr(info, _C_FIELD_BY_NAME[name], getattr(self, name).to_c())
        return info

    def with_updates(
        self,
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
    ) -> "EmbeddedImageInfo":
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
        values = {}
        for name in EMBEDDED_IMAGE_FIELDS:
            field = getattr(self, name)
            update = updates[name]
            values[name] = field if update is None else field.with_on_off(update)
        return EmbeddedImageInfo(**values)

    def iter_fields(self) -> tuple[tuple[str, EmbeddedImageField], ...]:
        return tuple((name, getattr(self, name)) for name in EMBEDDED_IMAGE_FIELDS)


@dataclass(frozen=True)
class ImageMetadata:
    timestamp: int
    gain: int
    shutter: int
    brightness: int
    exposure: int
    white_balance: int
    frame_counter: int
    strobe_pattern: int
    gpio_pin_state: int
    roi_position: int

    @classmethod
    def from_c(cls, metadata: fc2ImageMetadata) -> "ImageMetadata":
        return cls(
            timestamp=int(metadata.embeddedTimeStamp),
            gain=int(metadata.embeddedGain),
            shutter=int(metadata.embeddedShutter),
            brightness=int(metadata.embeddedBrightness),
            exposure=int(metadata.embeddedExposure),
            white_balance=int(metadata.embeddedWhiteBalance),
            frame_counter=int(metadata.embeddedFrameCounter),
            strobe_pattern=int(metadata.embeddedStrobePattern),
            gpio_pin_state=int(metadata.embeddedGPIOPinState),
            roi_position=int(metadata.embeddedROIPosition),
        )


@dataclass(frozen=True)
class CameraStats:
    image_dropped: int
    image_corrupt: int
    image_xmit_failed: int
    image_driver_dropped: int
    register_read_failed: int
    register_write_failed: int
    port_errors: int
    camera_power_up: bool
    camera_voltages: tuple[float, ...]
    camera_currents: tuple[float, ...]
    temperature: int
    time_since_initialization: int
    time_since_bus_reset: int
    timestamp_seconds: int
    timestamp_micro_seconds: int
    timestamp_cycle_seconds: int
    timestamp_cycle_count: int
    timestamp_cycle_offset: int
    num_resend_packets_requested: int
    num_resend_packets_received: int

    @classmethod
    def from_c(cls, stats: fc2CameraStats) -> "CameraStats":
        num_voltages = min(max(int(stats.numVoltages), 0), 8)
        num_currents = min(max(int(stats.numCurrents), 0), 8)
        return cls(
            image_dropped=int(stats.imageDropped),
            image_corrupt=int(stats.imageCorrupt),
            image_xmit_failed=int(stats.imageXmitFailed),
            image_driver_dropped=int(stats.imageDriverDropped),
            register_read_failed=int(stats.regReadFailed),
            register_write_failed=int(stats.regWriteFailed),
            port_errors=int(stats.portErrors),
            camera_power_up=bool(stats.cameraPowerUp),
            camera_voltages=tuple(float(stats.cameraVoltages[index]) for index in range(num_voltages)),
            camera_currents=tuple(float(stats.cameraCurrents[index]) for index in range(num_currents)),
            temperature=int(stats.temperature),
            time_since_initialization=int(stats.timeSinceInitialization),
            time_since_bus_reset=int(stats.timeSinceBusReset),
            timestamp_seconds=int(stats.timeStamp.seconds),
            timestamp_micro_seconds=int(stats.timeStamp.microSeconds),
            timestamp_cycle_seconds=int(stats.timeStamp.cycleSeconds),
            timestamp_cycle_count=int(stats.timeStamp.cycleCount),
            timestamp_cycle_offset=int(stats.timeStamp.cycleOffset),
            num_resend_packets_requested=int(stats.numResendPacketsRequested),
            num_resend_packets_received=int(stats.numResendPacketsReceived),
        )

    @property
    def temperature_kelvin(self) -> float:
        return self.temperature / 10.0


def validate_embedded_image_info_updates(base: EmbeddedImageInfo, updates: dict[str, bool | None]) -> None:
    for field_name, requested in updates.items():
        if requested is None:
            continue
        field = getattr(base, field_name)
        if not field.available:
            raise UnsupportedMetadataError(f"Embedded image metadata field {field_name!r} is not available.")
