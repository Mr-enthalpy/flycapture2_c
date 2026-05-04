from __future__ import annotations

from dataclasses import dataclass

from .api import FlyCapture2CAPI, get_api
from .ctypes_defs import fc2PGRGuid


@dataclass(frozen=True)
class CameraDescriptor:
    index: int
    guid: tuple[int, int, int, int]


def guid_to_tuple(guid: fc2PGRGuid) -> tuple[int, int, int, int]:
    return tuple(int(value) for value in guid.value)


def enumerate_cameras(api: FlyCapture2CAPI | None = None) -> list[CameraDescriptor]:
    runtime = api or get_api()
    context = runtime.create_context()
    try:
        count = runtime.get_num_cameras(context)
        return [
            CameraDescriptor(index=index, guid=guid_to_tuple(runtime.get_camera_from_index(context, index)))
            for index in range(count)
        ]
    finally:
        runtime.destroy_context(context)
