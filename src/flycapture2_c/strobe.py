from __future__ import annotations

from dataclasses import dataclass

from .errors import GPIOConfigurationError, StrobeConfigurationError, UnsupportedStrobeError
from .raw.structs import fc2StrobeControl, fc2StrobeInfo


def normalize_gpio_direction(direction: bool | int | str) -> int:
    if isinstance(direction, str):
        normalized = direction.strip().lower()
        if normalized in {"input", "in", "0"}:
            return 0
        if normalized in {"output", "out", "1"}:
            return 1
        raise GPIOConfigurationError(f"Unknown GPIO direction {direction!r}; expected input or output.")
    value = int(direction)
    if value not in {0, 1}:
        raise GPIOConfigurationError(f"GPIO direction must be 0/input or 1/output, got {direction!r}.")
    return value


@dataclass(frozen=True)
class StrobeInfo:
    source: int
    present: bool
    read_out_supported: bool
    on_off_supported: bool
    polarity_supported: bool
    min_value: float
    max_value: float

    @classmethod
    def from_c(cls, info: fc2StrobeInfo) -> "StrobeInfo":
        return cls(
            source=int(info.source),
            present=bool(info.present),
            read_out_supported=bool(info.readOutSupported),
            on_off_supported=bool(info.onOffSupported),
            polarity_supported=bool(info.polaritySupported),
            min_value=float(info.minValue),
            max_value=float(info.maxValue),
        )


@dataclass(frozen=True)
class StrobeControl:
    source: int
    on_off: bool
    polarity: int
    delay: float
    duration: float

    @classmethod
    def from_c(cls, control: fc2StrobeControl) -> "StrobeControl":
        return cls(
            source=int(control.source),
            on_off=bool(control.onOff),
            polarity=int(control.polarity),
            delay=float(control.delay),
            duration=float(control.duration),
        )

    def to_c(self) -> fc2StrobeControl:
        control = fc2StrobeControl()
        control.source = int(self.source)
        control.onOff = int(self.on_off)
        control.polarity = int(self.polarity)
        control.delay = float(self.delay)
        control.duration = float(self.duration)
        return control

    def with_updates(
        self,
        *,
        on: bool | None = None,
        polarity: int | None = None,
        delay: float | None = None,
        duration: float | None = None,
    ) -> "StrobeControl":
        return StrobeControl(
            source=self.source,
            on_off=self.on_off if on is None else bool(on),
            polarity=self.polarity if polarity is None else int(polarity),
            delay=self.delay if delay is None else float(delay),
            duration=self.duration if duration is None else float(duration),
        )


def validate_strobe_read(info: StrobeInfo) -> None:
    if not info.present:
        raise UnsupportedStrobeError(f"Strobe source {info.source} is not present on this camera.")
    if not info.read_out_supported:
        raise UnsupportedStrobeError(f"Strobe source {info.source} does not support readout.")


def validate_strobe_write(
    info: StrobeInfo,
    *,
    on: bool | None = None,
    polarity: int | None = None,
    delay: float | None = None,
    duration: float | None = None,
) -> None:
    if not info.present:
        raise UnsupportedStrobeError(f"Strobe source {info.source} is not present on this camera.")
    if on is not None and not info.on_off_supported:
        raise StrobeConfigurationError(f"Strobe source {info.source} does not support on/off control.")
    if polarity is not None:
        if not info.polarity_supported:
            raise StrobeConfigurationError(f"Strobe source {info.source} does not support polarity control.")
        if int(polarity) not in {0, 1}:
            raise StrobeConfigurationError(f"Strobe polarity must be 0 or 1, got {polarity!r}.")
    for field_name, value in (("delay", delay), ("duration", duration)):
        if value is None:
            continue
        numeric = float(value)
        if not (info.min_value <= numeric <= info.max_value):
            raise StrobeConfigurationError(
                f"Strobe source {info.source} {field_name} {numeric} is outside "
                f"[{info.min_value}, {info.max_value}]."
            )


__all__ = [
    "StrobeControl",
    "StrobeInfo",
    "normalize_gpio_direction",
    "validate_strobe_read",
    "validate_strobe_write",
]
