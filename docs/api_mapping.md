# API Mapping

This project intentionally wraps only a narrow subset of the FlyCapture2 C API.

## Context and bus

- `fc2CreateContext()` -> internal `FlyCapture2CAPI.create_context()`
- `fc2DestroyContext()` -> internal `FlyCapture2CAPI.destroy_context()`
- `fc2GetNumOfCameras()` -> `enumerate_cameras()`, `Camera.open()`
- `fc2GetCameraFromIndex()` -> `enumerate_cameras()`, `Camera.open()`

## Camera connection

- `fc2Connect()` -> `Camera.open()`
- `fc2Disconnect()` -> `Camera.close()`
- `fc2IsConnected()` -> internal `FlyCapture2CAPI.is_connected()`
- `fc2GetCameraInfo()` -> `Camera.get_camera_info()`
- `fc2GetVideoModeAndFrameRate()` -> `Camera.get_video_mode_and_frame_rate()`

## Capture

- `fc2CreateImage()` -> internal image handle allocation during `Camera.open()`
- `fc2DestroyImage()` -> internal cleanup during `Camera.close()`
- `fc2StartCapture()` -> `Camera.start()`
- `fc2StopCapture()` -> `Camera.stop()`
- `fc2RetrieveBuffer()` -> `Camera.read_frame()`, `Camera.read_frame_with_info()`
- `fc2GetImageTimeStamp()` -> `Camera.read_frame_with_info()`

## Properties

- `fc2GetPropertyInfo()` -> `Camera.get_property_info()`
- `fc2GetProperty()` -> `Camera.get_property()`
- `fc2SetProperty()` -> advanced `Camera.set_property()`

High-level convenience mapping:

- `fc2GetProperty(FC2_AUTO_EXPOSURE)` -> `Camera.get_exposure()`
- `fc2SetProperty(FC2_AUTO_EXPOSURE)` -> `Camera.set_exposure()`
- `fc2GetProperty(FC2_SHUTTER)` -> `Camera.get_shutter()`
- `fc2SetProperty(FC2_SHUTTER)` -> `Camera.set_shutter()`
- `fc2GetProperty(FC2_GAIN)` -> `Camera.get_gain()`
- `fc2SetProperty(FC2_GAIN)` -> `Camera.set_gain()`
- `fc2GetProperty(FC2_FRAME_RATE)` -> `Camera.get_frame_rate()`
- `fc2SetProperty(FC2_FRAME_RATE)` -> `Camera.set_frame_rate()`

Property write policy:

- high-level writes are intentionally limited to `AUTO_EXPOSURE`, `SHUTTER`, `GAIN`, and `FRAME_RATE`
- high-level writes run strict support, range, and mode checks before calling the SDK
- `Camera.set_property()` is retained as an advanced low-level API
- low-level `policy="raw"` is available for advanced callers; convenience APIs do not expose it

## Trigger

- `fc2GetTriggerModeInfo()` -> `Camera.get_trigger_mode_info()`
- `fc2GetTriggerMode()` -> `Camera.get_trigger_mode()`
- `fc2SetTriggerMode()` -> `Camera.set_trigger_mode()`, `Camera.enable_trigger()`, `Camera.disable_trigger()`
- `fc2SetTriggerModeBroadcast()` -> `Camera.set_trigger_mode(..., broadcast=True)`, `Camera.enable_trigger(..., broadcast=True)`, `Camera.disable_trigger(broadcast=True)`

Trigger mode is exposed through dedicated `TriggerModeInfo` and `TriggerMode` dataclasses, not through the generic property API.
This is intentional because FlyCapture2 uses dedicated trigger structures and functions for trigger configuration.

## Format7, ROI, and Pixel Format

- `fc2GetFormat7Info()` -> `Camera.get_format7_info()`
- `fc2ValidateFormat7Settings()` -> `Camera.validate_format7()`
- `fc2GetFormat7Configuration()` -> `Camera.get_format7_configuration()`
- `fc2SetFormat7ConfigurationPacket()` -> `Camera.set_format7()`, `Camera.set_roi()`, `Camera.set_pixel_format()`
- `fc2SetFormat7Configuration()` -> raw `FlyCapture2CAPI.set_format7_configuration()`

High-level ROI is camera-side Format7 configuration, not Python-side image cropping.
`PixelFormat` distinguishes SDK-configurable formats from formats that `read_frame()` can currently decode.

## SDK Capture Configuration

- `fc2GetConfiguration()` -> `Camera.get_configuration()`
- `fc2SetConfiguration()` -> `Camera.set_configuration()`, `Camera.set_grab_timeout()`, `Camera.set_grab_mode()`

`Camera.set_grab_timeout(ms)` sets the SDK-level `RetrieveBuffer()` timeout. It is separate from `FLYCAPTURE2_CAPTURE_TIMEOUT_MS`, which remains a Python-side smoke-test guard.

## Error handling

Every wrapped FlyCapture2 return code is checked and converted into a typed Python exception from `flycapture2_c.errors`.

## Intentionally not wrapped in this project

- GUI APIs
- sidecar / IPC / shared memory / ZMQ
- `optic_system` backend code
- experiment automation or calibration workflows
