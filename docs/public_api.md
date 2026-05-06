# Public API

This document classifies the names exported from `flycapture2_c.__all__` for
the `0.6.x` public API baseline. Stage 6.7 hardens release candidate
reproducibility without changing these exports. The package remains a FlyCapture2 C
SDK wrapper: no GUI, preview UI, sidecar, shared memory, ZMQ/IPC,
`optic_system`, LCD/projector synchronization, experiment scheduling,
acquisition workflow orchestration, calibration workflow, or reconstruction
workflow is part of this public API.

Importing these names must remain SDK-free and hardware-free. The vendor DLL is
loaded only by explicit camera operations.

The no-hardware drift test compares `flycapture2_c.__all__` with the frozen
`0.6.x` baseline and verifies that every top-level export is classified here.

## Stable High-Level API

Use these names for ordinary scripts:

- `Camera`
- `enumerate_cameras`

The stable `Camera` surface is task-oriented: lifecycle, capture, trigger mode,
software trigger firing, Format7/ROI/pixel format, SDK capture configuration,
properties, embedded metadata, diagnostics, strobe/GPIO, and GigE camera-local
SDK primitives.

## Value Dataclasses And Enums

These names are public containers or enums returned by the high-level API or
accepted by configuration helpers:

- `CameraConfiguration`
- `CameraDescriptor`
- `CameraInfo`
- `CameraStats`
- `CameraPropertyInfo`
- `CameraPropertySnapshot`
- `CameraPropertyValue`
- `EmbeddedImageField`
- `EmbeddedImageInfo`
- `Format7Configuration`
- `Format7ImageSettings`
- `Format7Info`
- `Format7PacketInfo`
- `Format7Validation`
- `GigEConfig`
- `GigEImageBinningSettings`
- `GigEImageSettings`
- `GigEImageSettingsInfo`
- `GigEProperty`
- `GigEPropertyType`
- `GigEStreamChannelInfo`
- `GrabMode`
- `ImageMetadata`
- `PixelFormat`
- `PropertyType`
- `PropertyWritePolicy`
- `StrobeControl`
- `StrobeInfo`
- `TriggerMode`
- `TriggerModeInfo`

These types are intentionally explicit so callers can save, compare, and
restore camera-local SDK state without using a GUI.

## Error Types

Top-level error exports are part of the supported API for high-level callers:

- `CameraConfigurationError`
- `CameraStateError`
- `DLLLoadError`
- `FlyCapture2Error`
- `Format7ValidationError`
- `GigEConfigurationError`
- `GPIOConfigurationError`
- `PropertyModeError`
- `PropertyNotWritableError`
- `PropertyOutOfRangeError`
- `SDKNotFoundError`
- `StrobeConfigurationError`
- `TriggerModeError`
- `UnsupportedFormat7Error`
- `UnsupportedGigEError`
- `UnsupportedMetadataError`
- `UnsupportedPixelFormatError`
- `UnsupportedPropertyError`
- `UnsupportedStrobeError`
- `UnsupportedTriggerError`

Lower-level typed SDK exceptions also remain available from
`flycapture2_c.errors`.

## Advanced And Raw API

The `flycapture2_c.raw` package and `flycapture2_c.api.FlyCapture2CAPI` are
advanced interfaces. They expose ctypes-oriented structures, function specs,
and checked SDK calls for users who need to reason about the C API directly.

The raw layer is not a claim of full FlyCapture2 SDK coverage. Deferred areas
include register access, callbacks/events, broader raw SDK coverage, and broad
camera-model validation.

## Compatibility Exports

These names are kept for no-hardware tests and compatibility with the existing
test/support surface:

- `MockCamera`
- `open_mock_camera`

They do not open hardware and do not require the FlyCapture2 SDK.
