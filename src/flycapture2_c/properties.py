from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

from .ctypes_defs import fc2Property, fc2PropertyInfo


class PropertyType(IntEnum):
    BRIGHTNESS = 0
    AUTO_EXPOSURE = 1
    SHARPNESS = 2
    WHITE_BALANCE = 3
    HUE = 4
    SATURATION = 5
    GAMMA = 6
    IRIS = 7
    FOCUS = 8
    ZOOM = 9
    PAN = 10
    TILT = 11
    SHUTTER = 12
    GAIN = 13
    TRIGGER_MODE = 14
    TRIGGER_DELAY = 15
    FRAME_RATE = 16
    TEMPERATURE = 17
    UNSPECIFIED = 18


SUPPORTED_HIGH_LEVEL_WRITE_PROPERTIES = frozenset(
    {
        PropertyType.AUTO_EXPOSURE,
        PropertyType.SHUTTER,
        PropertyType.GAIN,
        PropertyType.FRAME_RATE,
    }
)
KNOWN_PROPERTY_TYPES = tuple(property_type for property_type in PropertyType if property_type != PropertyType.UNSPECIFIED)


class PropertyWritePolicy(str, Enum):
    STRICT = "strict"
    RAW = "raw"


def normalize_property_type(value: PropertyType | str | int) -> PropertyType:
    if isinstance(value, PropertyType):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper().replace(" ", "_")
        return PropertyType[normalized]
    return PropertyType(int(value))


def _decode(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace")


@dataclass(frozen=True)
class CameraPropertyInfo:
    property_type: PropertyType
    present: bool
    auto_supported: bool
    manual_supported: bool
    on_off_supported: bool
    one_push_supported: bool
    abs_val_supported: bool
    read_out_supported: bool
    min_value: int
    max_value: int
    abs_min: float
    abs_max: float
    units: str
    unit_abbr: str

    @classmethod
    def from_c(cls, struct: fc2PropertyInfo) -> "CameraPropertyInfo":
        return cls(
            property_type=PropertyType(int(struct.type)),
            present=bool(struct.present),
            auto_supported=bool(struct.autoSupported),
            manual_supported=bool(struct.manualSupported),
            on_off_supported=bool(struct.onOffSupported),
            one_push_supported=bool(struct.onePushSupported),
            abs_val_supported=bool(struct.absValSupported),
            read_out_supported=bool(struct.readOutSupported),
            min_value=int(struct.min),
            max_value=int(struct.max),
            abs_min=float(struct.absMin),
            abs_max=float(struct.absMax),
            units=_decode(bytes(struct.pUnits)),
            unit_abbr=_decode(bytes(struct.pUnitAbbr)),
        )

    @property
    def writable(self) -> bool:
        return any(
            (
                self.manual_supported,
                self.auto_supported,
                self.on_off_supported,
                self.one_push_supported,
                self.abs_val_supported,
            )
        )


@dataclass(frozen=True)
class CameraPropertyValue:
    property_type: PropertyType
    present: bool
    abs_control: bool
    one_push: bool
    on_off: bool
    auto_manual_mode: bool
    value_a: int
    value_b: int
    abs_value: float

    @classmethod
    def from_c(cls, struct: fc2Property) -> "CameraPropertyValue":
        return cls(
            property_type=PropertyType(int(struct.type)),
            present=bool(struct.present),
            abs_control=bool(struct.absControl),
            one_push=bool(struct.onePush),
            on_off=bool(struct.onOff),
            auto_manual_mode=bool(struct.autoManualMode),
            value_a=int(struct.valueA),
            value_b=int(struct.valueB),
            abs_value=float(struct.absValue),
        )


@dataclass(frozen=True)
class CameraPropertySnapshot:
    property_type: PropertyType
    info: CameraPropertyInfo | None
    value: CameraPropertyValue | None
    error: str | None = None

    @property
    def present(self) -> bool:
        return bool(self.info.present) if self.info is not None else False


__all__ = [
    "CameraPropertyInfo",
    "CameraPropertySnapshot",
    "CameraPropertyValue",
    "KNOWN_PROPERTY_TYPES",
    "PropertyWritePolicy",
    "PropertyType",
    "SUPPORTED_HIGH_LEVEL_WRITE_PROPERTIES",
    "normalize_property_type",
]
