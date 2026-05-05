from __future__ import annotations

from dataclasses import dataclass

from .ctypes_defs import fc2TriggerMode, fc2TriggerModeInfo
from .errors import TriggerModeError, UnsupportedTriggerError

SOFTWARE_TRIGGER_SOURCE = 7
_TRIGGER_MODE_COUNT = 16


@dataclass(frozen=True)
class TriggerModeInfo:
    present: bool
    read_out_supported: bool
    on_off_supported: bool
    polarity_supported: bool
    value_readable: bool
    source_mask: int
    software_trigger_supported: bool
    mode_mask: int

    @classmethod
    def from_c(cls, struct: fc2TriggerModeInfo) -> "TriggerModeInfo":
        return cls(
            present=bool(struct.present),
            read_out_supported=bool(struct.readOutSupported),
            on_off_supported=bool(struct.onOffSupported),
            polarity_supported=bool(struct.polaritySupported),
            value_readable=bool(struct.valueReadable),
            source_mask=int(struct.sourceMask),
            software_trigger_supported=bool(struct.softwareTriggerSupported),
            mode_mask=int(struct.modeMask),
        )

    @property
    def supported_modes(self) -> tuple[int, ...]:
        return tuple(mode for mode in range(_TRIGGER_MODE_COUNT) if self.supports_mode(mode))

    @property
    def supported_sources(self) -> tuple[int, ...]:
        sources = [source for source in range(32) if self.source_mask & (1 << source)]
        if self.software_trigger_supported and SOFTWARE_TRIGGER_SOURCE not in sources:
            sources.append(SOFTWARE_TRIGGER_SOURCE)
        return tuple(sorted(sources))

    def supports_mode(self, mode: int) -> bool:
        """Return whether an IIDC trigger mode is advertised by the SDK mask.

        The FlyCapture2 GUI samples map trigger mode 0 to bit 15, mode 1 to bit 14,
        and so on. Keep that convention here instead of guessing a new mapping.
        """
        if mode < 0 or mode >= _TRIGGER_MODE_COUNT:
            return False
        return bool(self.mode_mask & (1 << (_TRIGGER_MODE_COUNT - mode - 1)))

    def supports_source(self, source: int) -> bool:
        if source == SOFTWARE_TRIGGER_SOURCE and self.software_trigger_supported:
            return True
        if source < 0 or source >= 32:
            return False
        return bool(self.source_mask & (1 << source))


@dataclass(frozen=True)
class TriggerMode:
    on_off: bool
    polarity: int = 0
    source: int = 0
    mode: int = 0
    parameter: int = 0

    @classmethod
    def from_c(cls, struct: fc2TriggerMode) -> "TriggerMode":
        return cls(
            on_off=bool(struct.onOff),
            polarity=int(struct.polarity),
            source=int(struct.source),
            mode=int(struct.mode),
            parameter=int(struct.parameter),
        )

    def to_c(self) -> fc2TriggerMode:
        struct = fc2TriggerMode()
        struct.onOff = int(self.on_off)
        struct.polarity = int(self.polarity)
        struct.source = int(self.source)
        struct.mode = int(self.mode)
        struct.parameter = int(self.parameter)
        return struct

    def with_updates(
        self,
        *,
        on_off: bool | None = None,
        polarity: int | None = None,
        source: int | None = None,
        mode: int | None = None,
        parameter: int | None = None,
    ) -> "TriggerMode":
        return TriggerMode(
            on_off=self.on_off if on_off is None else bool(on_off),
            polarity=self.polarity if polarity is None else int(polarity),
            source=self.source if source is None else int(source),
            mode=self.mode if mode is None else int(mode),
            parameter=self.parameter if parameter is None else int(parameter),
        )


def validate_trigger_mode_request(
    info: TriggerModeInfo,
    trigger_mode: TriggerMode,
    *,
    changed_fields: set[str],
) -> None:
    if not info.present:
        raise UnsupportedTriggerError("Trigger mode is not present on this camera.")
    if "on_off" in changed_fields and not info.on_off_supported:
        raise TriggerModeError("Trigger on/off control is not supported by this camera.")
    if "polarity" in changed_fields and not info.polarity_supported:
        raise TriggerModeError("Trigger polarity control is not supported by this camera.")
    if "mode" in changed_fields and not info.supports_mode(trigger_mode.mode):
        raise TriggerModeError(f"Trigger mode {trigger_mode.mode} is not advertised by modeMask=0x{info.mode_mask:08x}.")
    if "source" in changed_fields and not info.supports_source(trigger_mode.source):
        raise TriggerModeError(
            f"Trigger source {trigger_mode.source} is not advertised by sourceMask=0x{info.source_mask:08x}."
        )


__all__ = [
    "SOFTWARE_TRIGGER_SOURCE",
    "TriggerMode",
    "TriggerModeInfo",
    "validate_trigger_mode_request",
]
