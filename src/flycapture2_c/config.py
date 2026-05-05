from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .ctypes_defs import fc2Config


class GrabMode(IntEnum):
    DROP_FRAMES = 0
    BUFFER_FRAMES = 1
    UNSPECIFIED = 2


class BandwidthAllocation(IntEnum):
    OFF = 0
    ON = 1
    UNSUPPORTED = 2
    UNSPECIFIED = 3


@dataclass(frozen=True)
class CameraConfiguration:
    num_buffers: int
    num_image_notifications: int
    min_num_image_notifications: int
    grab_timeout: int
    grab_mode: GrabMode
    high_performance_retrieve_buffer: bool
    isoch_bus_speed: int
    async_bus_speed: int
    bandwidth_allocation: BandwidthAllocation
    register_timeout_retries: int
    register_timeout: int

    @classmethod
    def from_c(cls, struct: fc2Config) -> "CameraConfiguration":
        return cls(
            num_buffers=int(struct.numBuffers),
            num_image_notifications=int(struct.numImageNotifications),
            min_num_image_notifications=int(struct.minNumImageNotifications),
            grab_timeout=int(struct.grabTimeout),
            grab_mode=GrabMode(int(struct.grabMode)),
            high_performance_retrieve_buffer=bool(struct.highPerformanceRetrieveBuffer),
            isoch_bus_speed=int(struct.isochBusSpeed),
            async_bus_speed=int(struct.asyncBusSpeed),
            bandwidth_allocation=BandwidthAllocation(int(struct.bandwidthAllocation)),
            register_timeout_retries=int(struct.registerTimeoutRetries),
            register_timeout=int(struct.registerTimeout),
        )

    def to_c(self) -> fc2Config:
        struct = fc2Config()
        struct.numBuffers = int(self.num_buffers)
        struct.numImageNotifications = int(self.num_image_notifications)
        struct.minNumImageNotifications = int(self.min_num_image_notifications)
        struct.grabTimeout = int(self.grab_timeout)
        struct.grabMode = int(self.grab_mode)
        struct.highPerformanceRetrieveBuffer = int(self.high_performance_retrieve_buffer)
        struct.isochBusSpeed = int(self.isoch_bus_speed)
        struct.asyncBusSpeed = int(self.async_bus_speed)
        struct.bandwidthAllocation = int(self.bandwidth_allocation)
        struct.registerTimeoutRetries = int(self.register_timeout_retries)
        struct.registerTimeout = int(self.register_timeout)
        return struct

    def with_updates(
        self,
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
    ) -> "CameraConfiguration":
        return CameraConfiguration(
            num_buffers=self.num_buffers if num_buffers is None else int(num_buffers),
            num_image_notifications=(
                self.num_image_notifications if num_image_notifications is None else int(num_image_notifications)
            ),
            min_num_image_notifications=self.min_num_image_notifications,
            grab_timeout=self.grab_timeout if grab_timeout is None else int(grab_timeout),
            grab_mode=self.grab_mode if grab_mode is None else normalize_grab_mode(grab_mode),
            high_performance_retrieve_buffer=(
                self.high_performance_retrieve_buffer
                if high_performance_retrieve_buffer is None
                else bool(high_performance_retrieve_buffer)
            ),
            isoch_bus_speed=self.isoch_bus_speed if isoch_bus_speed is None else int(isoch_bus_speed),
            async_bus_speed=self.async_bus_speed if async_bus_speed is None else int(async_bus_speed),
            bandwidth_allocation=(
                self.bandwidth_allocation
                if bandwidth_allocation is None
                else normalize_bandwidth_allocation(bandwidth_allocation)
            ),
            register_timeout_retries=(
                self.register_timeout_retries
                if register_timeout_retries is None
                else int(register_timeout_retries)
            ),
            register_timeout=self.register_timeout if register_timeout is None else int(register_timeout),
        )


def normalize_grab_mode(value: GrabMode | str | int) -> GrabMode:
    if isinstance(value, GrabMode):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper().replace(" ", "_").replace("-", "_")
        return GrabMode[normalized]
    return GrabMode(int(value))


def normalize_bandwidth_allocation(value: BandwidthAllocation | str | int) -> BandwidthAllocation:
    if isinstance(value, BandwidthAllocation):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper().replace(" ", "_").replace("-", "_")
        return BandwidthAllocation[normalized]
    return BandwidthAllocation(int(value))


__all__ = [
    "BandwidthAllocation",
    "CameraConfiguration",
    "GrabMode",
    "normalize_bandwidth_allocation",
    "normalize_grab_mode",
]
