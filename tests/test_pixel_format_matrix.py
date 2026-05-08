from __future__ import annotations

from flycapture2_c.pixel_format import (
    DECODABLE_PIXEL_FORMATS,
    PIXEL_FORMAT_SUPPORT,
    PixelFormat,
    interpret_pixel_format_bitfield,
    support_for_pixel_format,
)


def test_every_pixel_format_member_is_in_support_matrix() -> None:
    assert set(PIXEL_FORMAT_SUPPORT) == set(PixelFormat.__members__)


def test_current_decodable_formats_are_marked_decodable() -> None:
    for name in ("MONO8", "MONO16", "RAW8", "RAW16", "RGB8", "RGB"):
        support = PIXEL_FORMAT_SUPPORT[name]
        assert support.sdk_known is True
        assert support.read_frame_decodable is True
        assert support.raw_copy_only is False
        assert support.compressed_or_unsupported is False


def test_decodable_formats_have_dtype_and_shape_semantics() -> None:
    expected = {
        "MONO8": ("mono2d", "uint8", 1),
        "MONO16": ("mono2d", "uint16", 1),
        "RAW8": ("mono2d", "uint8", 1),
        "RAW16": ("mono2d", "uint16", 1),
        "RGB8": ("rgb_interleaved_hwc", "uint8", 3),
        "RGB": ("rgb_interleaved_hwc", "uint8", 3),
    }
    for name, (shape_kind, dtype, channels) in expected.items():
        support = PIXEL_FORMAT_SUPPORT[name]
        assert support.numpy_shape_kind == shape_kind
        assert support.numpy_dtype == dtype
        assert support.channel_count == channels


def test_non_decoded_known_formats_are_not_marked_decodable() -> None:
    decoded_values = {int(pixel_format) for pixel_format in DECODABLE_PIXEL_FORMATS}
    for name, support in PIXEL_FORMAT_SUPPORT.items():
        if support.sdk_value in decoded_values:
            continue
        assert support.read_frame_decodable is False, name


def test_compressed_and_unspecified_formats_are_explicitly_classified() -> None:
    jpeg = PIXEL_FORMAT_SUPPORT["YUV422_JPEG"]
    unspecified = PIXEL_FORMAT_SUPPORT["UNSPECIFIED"]

    assert jpeg.compressed_or_unsupported is True
    assert jpeg.raw_copy_only is False
    assert unspecified.compressed_or_unsupported is True
    assert unspecified.camera_configurable_candidate is False


def test_camera_configurable_candidate_is_distinct_from_decode_support() -> None:
    yuv = PIXEL_FORMAT_SUPPORT["YUV422"]
    rgb = PIXEL_FORMAT_SUPPORT["RGB8"]

    assert yuv.camera_configurable_candidate is True
    assert yuv.read_frame_decodable is False
    assert yuv.raw_copy_only is True
    assert rgb.camera_configurable_candidate is True
    assert rgb.read_frame_decodable is True


def test_support_lookup_handles_aliases() -> None:
    assert support_for_pixel_format("RGB").read_frame_decodable is True  # type: ignore[union-attr]
    assert support_for_pixel_format(PixelFormat.RGB8).name == "RGB8"  # type: ignore[union-attr]


def test_bitfield_interpretation_separates_supported_decode_and_raw_copy() -> None:
    summary = interpret_pixel_format_bitfield(int(PixelFormat.MONO8) | int(PixelFormat.RGB8) | int(PixelFormat.BGR))

    assert summary["supported_by_camera"] == ["MONO8", "RGB8", "BGR"]
    assert summary["read_frame_decodable"] == ["MONO8", "RGB8"]
    assert summary["raw_copy_only"] == ["BGR"]
    assert summary["unsupported_or_compressed"] == []

    compressed_summary = interpret_pixel_format_bitfield(int(PixelFormat.YUV422_JPEG))
    assert "YUV422_JPEG" in compressed_summary["unsupported_or_compressed"]
