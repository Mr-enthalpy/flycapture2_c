from __future__ import annotations

import re
from pathlib import Path

import flycapture2_c


EXPECTED_PUBLIC_EXPORTS_0_6 = {
    "Camera",
    "CameraConfiguration",
    "CameraConfigurationError",
    "CameraDescriptor",
    "CameraInfo",
    "CameraPropertyInfo",
    "CameraPropertySnapshot",
    "CameraPropertyValue",
    "CameraStateError",
    "CameraStats",
    "DLLLoadError",
    "EmbeddedImageField",
    "EmbeddedImageInfo",
    "FlyCapture2Error",
    "Format7Configuration",
    "Format7ImageSettings",
    "Format7Info",
    "Format7PacketInfo",
    "Format7Validation",
    "Format7ValidationError",
    "GigEConfig",
    "GigEConfigurationError",
    "GigEImageBinningSettings",
    "GigEImageSettings",
    "GigEImageSettingsInfo",
    "GigEProperty",
    "GigEPropertyType",
    "GigEStreamChannelInfo",
    "GPIOConfigurationError",
    "GrabMode",
    "ImageMetadata",
    "MockCamera",
    "PixelFormat",
    "PropertyModeError",
    "PropertyNotWritableError",
    "PropertyOutOfRangeError",
    "PropertyType",
    "PropertyWritePolicy",
    "SDKNotFoundError",
    "StrobeConfigurationError",
    "StrobeControl",
    "StrobeInfo",
    "TriggerMode",
    "TriggerModeError",
    "TriggerModeInfo",
    "UnsupportedFormat7Error",
    "UnsupportedGigEError",
    "UnsupportedMetadataError",
    "UnsupportedPixelFormatError",
    "UnsupportedPropertyError",
    "UnsupportedStrobeError",
    "UnsupportedTriggerError",
    "enumerate_cameras",
    "open_mock_camera",
}


def test_top_level_exports_match_0_6_public_api_baseline() -> None:
    assert set(flycapture2_c.__all__) == EXPECTED_PUBLIC_EXPORTS_0_6


def test_all_top_level_exports_are_classified_in_public_api_doc() -> None:
    root = Path(__file__).resolve().parents[1]
    public_api = (root / "docs" / "public_api.md").read_text(encoding="utf-8")
    documented_exports = set(re.findall(r"^- `([^`]+)`", public_api, re.MULTILINE))

    missing = sorted(set(flycapture2_c.__all__) - documented_exports)

    assert missing == []
