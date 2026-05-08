from __future__ import annotations

import ctypes
from dataclasses import dataclass

import numpy as np

from .ctypes_defs import fc2Image, fc2TimeStamp
from .errors import FlyCapture2Error
from .metadata import ImageMetadata
from .pixel_format import PixelFormat, bytes_per_pixel, channel_count, from_sdk_value, numpy_dtype
from .typing import FrameArray


@dataclass(frozen=True)
class ImageFrame:
    array: FrameArray
    width: int
    height: int
    stride: int
    pixel_format: PixelFormat
    timestamp: fc2TimeStamp | None = None
    metadata: ImageMetadata | None = None


def image_to_array(image: fc2Image) -> FrameArray:
    frame = image_to_frame(image)
    return frame.array


def image_to_frame(
    image: fc2Image,
    timestamp: fc2TimeStamp | None = None,
    metadata: ImageMetadata | None = None,
) -> ImageFrame:
    pixel_format = from_sdk_value(int(image.format))
    height = int(image.rows)
    width = int(image.cols)
    stride = int(image.stride)
    bytes_per_px = bytes_per_pixel(pixel_format)
    channels = channel_count(pixel_format)
    row_bytes = width * bytes_per_px
    expected_bytes = height * stride
    available_bytes = int(image.receivedDataSize) or int(image.dataSize)
    if available_bytes < expected_bytes:
        raise FlyCapture2Error(
            f"Image buffer is smaller than expected: available={available_bytes}, expected={expected_bytes}"
        )
    raw_bytes = ctypes.string_at(image.pData, available_bytes)
    raw_matrix = np.frombuffer(raw_bytes, dtype=np.uint8, count=expected_bytes).reshape(height, stride)
    payload = raw_matrix[:, :row_bytes].copy()
    dtype = numpy_dtype(pixel_format)
    if channels == 1 and bytes_per_px == 1:
        array = np.array(payload.reshape(height, width), dtype=dtype, copy=True)
    elif channels == 3 and dtype == np.dtype(np.uint8):
        array = np.array(payload.reshape(height, width, channels), dtype=dtype, copy=True)
    else:
        array = np.array(payload.view(dtype).reshape(height, width), dtype=dtype, copy=True)
    return ImageFrame(
        array=array,
        width=width,
        height=height,
        stride=stride,
        pixel_format=pixel_format,
        timestamp=timestamp,
        metadata=metadata,
    )
