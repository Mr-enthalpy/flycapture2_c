# API Mapping

This project wraps the FlyCapture2 C API incrementally. It currently covers
lifecycle, acquisition, trigger mode, Format7/ROI/pixel format, SDK capture
configuration, the generic property system, embedded metadata, strobe/GPIO,
software trigger firing, and GigE-specific camera controls. It does not claim
full SDK coverage.

Stage 6.9 is explicit pixel-format support-matrix and RGB decode hardening.
GPIO scope is limited to direct C API pin-direction
helpers plus metadata-level GPIO pin-state observation; no register-level GPIO
control is wrapped.

Top-level public exports are classified in `docs/public_api.md`. Stable
ordinary use should go through `Camera`, `enumerate_cameras`, and the value
dataclasses/enums returned by those methods. `flycapture2_c.raw` and
`flycapture2_c.api.FlyCapture2CAPI` are advanced interfaces for ctypes-oriented
callers.

## Raw binding infrastructure

- current function signatures are registered in `flycapture2_c.raw.specs`
- `FunctionSpec` records the C function name, `argtypes`, `restype`, and category
- the existing checked `FlyCapture2CAPI` remains the compatibility wrapper and binds DLL functions through that registry
- future SDK expansion should add signatures to `raw/specs.py` rather than growing a monolithic binding block in `api.py`

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
- `fc2GetImageMetadata()` -> `Camera.read_frame_with_info().metadata`
- `fc2GetImageTimeStamp()` -> `Camera.read_frame_with_info()`

`Camera.read_frame()` still returns only the owned NumPy array. Use
`Camera.read_frame_with_info()` when timestamp and embedded frame metadata are
needed.

Pixel-format decode support is intentionally narrower than SDK enum knowledge
and camera-side configuration support. The current structured decoder covers
`MONO8`, `MONO16`, `RAW8`, `RAW16`, and 24-bit interleaved `RGB8`/`RGB`.
Other known formats continue to raise `UnsupportedPixelFormatError` unless a
future milestone adds an explicit decoder. See `docs/pixel_formats.md`.

## Properties

- `fc2GetPropertyInfo()` -> `Camera.get_property_info()`
- `fc2GetPropertyInfo()` for all known property types -> `Camera.list_property_infos()`, `Camera.snapshot_properties()`
- `fc2GetProperty()` -> `Camera.get_property()`, `Camera.get_property_raw()`, `Camera.list_properties()`
- `fc2GetProperty()` + `fc2GetPropertyInfo()` -> `Camera.get_property_display_value()`, `Camera.get_property_display_range()`, `Camera.get_property_abs_readback()`
- `fc2SetProperty()` -> advanced `Camera.set_property()`, `Camera.set_property_raw()`
- `fc2SetProperty()` with strict validation -> `Camera.set_property_abs()`, `Camera.set_property_integer()`, `Camera.set_property_on_off()`, `Camera.set_property_auto()`, `Camera.set_property_one_push()`

Display readback policy:

- if `CameraPropertyInfo.abs_val_supported` is true, `CameraPropertyValue.abs_value` is the preferred display readback and should be paired with `abs_min` / `abs_max`
- `CameraPropertyValue.abs_control` indicates whether SDK absolute control is enabled for writes; it is not a reason to display `value_a` when `abs_val_supported` is true
- if absolute values are not supported, display helpers fall back to `value_a` with `min_value` / `max_value`
- `CameraPropertySnapshot.display_value` and `display_range` apply the same policy for snapshot-style UIs

High-level convenience mapping:

- `fc2GetProperty(FC2_AUTO_EXPOSURE)` -> `Camera.get_exposure()`
- `fc2SetProperty(FC2_AUTO_EXPOSURE)` -> `Camera.set_exposure()`
- `fc2GetProperty(FC2_SHUTTER)` -> `Camera.get_shutter()`
- `fc2SetProperty(FC2_SHUTTER)` -> `Camera.set_shutter()`
- `fc2GetProperty(FC2_GAIN)` -> `Camera.get_gain()`
- `fc2SetProperty(FC2_GAIN)` -> `Camera.set_gain()`
- `fc2GetProperty(FC2_FRAME_RATE)` -> `Camera.get_frame_rate()`
- `fc2SetProperty(FC2_FRAME_RATE)` -> `Camera.set_frame_rate()`
- `fc2GetProperty(FC2_BRIGHTNESS)` -> `Camera.get_brightness()`
- `fc2SetProperty(FC2_BRIGHTNESS)` -> `Camera.set_brightness()`
- `fc2GetProperty(FC2_GAMMA)` -> `Camera.get_gamma()`
- `fc2SetProperty(FC2_GAMMA)` -> `Camera.set_gamma()`
- `fc2GetProperty(FC2_WHITE_BALANCE)` -> `Camera.get_white_balance()`
- `fc2SetProperty(FC2_WHITE_BALANCE)` -> `Camera.set_white_balance()`
- `fc2GetProperty(FC2_TRIGGER_DELAY)` -> `Camera.get_trigger_delay()`
- `fc2SetProperty(FC2_TRIGGER_DELAY)` -> `Camera.set_trigger_delay()`
- `fc2GetProperty(FC2_TEMPERATURE)` -> `Camera.get_temperature()`

Property write policy:

- generic safe writes are available for all known `PropertyType` values when the camera reports support
- safe writes run present, capability, mode, and range checks before calling the SDK
- `Camera.set_property(..., policy="raw")` and `Camera.set_property_raw()` are retained for advanced low-policy writes
- `TRIGGER_MODE` has a dedicated trigger API; `TRIGGER_DELAY` remains part of the property API

## Trigger

- `fc2GetTriggerModeInfo()` -> `Camera.get_trigger_mode_info()`
- `fc2GetTriggerMode()` -> `Camera.get_trigger_mode()`
- `fc2SetTriggerMode()` -> `Camera.set_trigger_mode()`, `Camera.enable_trigger()`, `Camera.disable_trigger()`
- `fc2SetTriggerModeBroadcast()` -> `Camera.set_trigger_mode(..., broadcast=True)`, `Camera.enable_trigger(..., broadcast=True)`, `Camera.disable_trigger(broadcast=True)`
- `fc2FireSoftwareTrigger()` -> `Camera.fire_software_trigger()`
- `fc2FireSoftwareTriggerBroadcast()` -> `Camera.fire_software_trigger(broadcast=True)`

Trigger mode is exposed through dedicated `TriggerModeInfo` and `TriggerMode` dataclasses, not through the generic property API.
This is intentional because FlyCapture2 uses dedicated trigger structures and functions for trigger configuration.

Software trigger firing is a camera-local SDK primitive. It does not configure
trigger mode, start capture, retrieve a frame, sleep, poll, schedule repeated
triggers, or coordinate external devices.

## Format7, ROI, and Pixel Format

- `fc2GetFormat7Info()` -> `Camera.get_format7_info()`
- `fc2ValidateFormat7Settings()` -> `Camera.validate_format7()`
- `fc2GetFormat7Configuration()` -> `Camera.get_format7_configuration()`
- `fc2SetFormat7ConfigurationPacket()` -> `Camera.set_format7()`, `Camera.set_roi()`, `Camera.set_pixel_format()`
- `fc2SetFormat7Configuration()` -> raw `FlyCapture2CAPI.set_format7_configuration()`

High-level ROI is camera-side Format7 configuration, not Python-side image cropping.
`PixelFormat` distinguishes SDK-configurable formats from formats that `read_frame()` can currently decode.
`flycapture2_c.pixel_format.PIXEL_FORMAT_SUPPORT` records the machine-readable
support matrix used by tests and capability reports.

## SDK Capture Configuration

- `fc2GetConfiguration()` -> `Camera.get_configuration()`
- `fc2SetConfiguration()` -> `Camera.set_configuration()`, `Camera.set_grab_timeout()`, `Camera.set_grab_mode()`

`Camera.set_grab_timeout(ms)` sets the SDK-level `RetrieveBuffer()` timeout. It is separate from `FLYCAPTURE2_CAPTURE_TIMEOUT_MS`, which remains a Python-side smoke-test guard.

## Embedded Image Metadata and Diagnostics

- `fc2GetEmbeddedImageInfo()` -> `Camera.get_embedded_image_info()`
- `fc2SetEmbeddedImageInfo()` -> `Camera.set_embedded_image_info(...)`
- `fc2GetImageMetadata()` -> `ImageFrame.metadata`
- `fc2GetStats()` -> `Camera.get_camera_stats()`
- `ResetStats()` -> `Camera.reset_camera_stats()`

Embedded image info exposes both field availability and on/off state. Enabling a
field is camera-model-dependent; the high-level API raises a typed error if a
caller explicitly enables or disables an unavailable field.

`ResetStats()` is declared by this SDK without an `fc2` prefix or camera context.
The raw binding treats it as optional, and the high-level reset method is a
write-like diagnostic operation. Hardware tests for it require
`FLYCAPTURE2_HARDWARE_WRITE_TEST=1`.

## Strobe and GPIO

- `fc2GetStrobeInfo()` -> `Camera.get_strobe_info(source)`
- `fc2GetStrobe()` -> `Camera.get_strobe(source)`
- `fc2SetStrobe()` -> `Camera.set_strobe(source, ...)`
- `fc2SetStrobeBroadcast()` -> `Camera.set_strobe(source, ..., broadcast=True)`
- `fc2GetGPIOPinDirection()` -> `Camera.get_gpio_pin_direction(pin)`
- `fc2SetGPIOPinDirection()` -> `Camera.set_gpio_pin_direction(pin, direction)`
- `fc2SetGPIOPinDirectionBroadcast()` -> `Camera.set_gpio_pin_direction(pin, direction, broadcast=True)`

`Camera.set_strobe()` reads the current SDK state, applies only explicitly
provided fields, validates support and delay/duration ranges against
`StrobeInfo`, writes the result, then reads back the current state.

GPIO support in this stage is intentionally narrow. The FlyCapture2 C API
exposes pin direction helpers, and the embedded metadata API can observe
`gpio_pin_state` when the camera supports that field. This project does not
infer GPIO output behavior from registers or unrelated SDK concepts.

## GigE-Specific Controls

- `fc2GetGigEConfig()` -> `Camera.get_gige_config()`
- `fc2SetGigEConfig()` -> `Camera.set_gige_config(...)`
- `fc2GetGigEProperty()` -> `Camera.get_gige_property(...)`
- `fc2SetGigEProperty()` -> `Camera.set_gige_property(...)`
- `fc2DiscoverGigEPacketSize()` -> `Camera.discover_gige_packet_size()`
- `fc2QueryGigEImagingMode()` -> `Camera.query_gige_imaging_mode(...)`
- `fc2GetGigEImagingMode()` -> `Camera.get_gige_imaging_mode()`
- `fc2SetGigEImagingMode()` -> `Camera.set_gige_imaging_mode(...)`
- `fc2GetGigEImageSettingsInfo()` -> `Camera.get_gige_image_settings_info()`
- `fc2GetGigEImageSettings()` -> `Camera.get_gige_image_settings()`
- `fc2SetGigEImageSettings()` -> `Camera.set_gige_image_settings(...)`
- `fc2GetGigEImageBinningSettings()` -> `Camera.get_gige_image_binning_settings()`
- `fc2SetGigEImageBinningSettings()` -> `Camera.set_gige_image_binning_settings(...)`
- `fc2GetNumStreamChannels()` -> `Camera.get_num_gige_stream_channels()`
- `fc2GetGigEStreamChannelInfo()` -> `Camera.get_gige_stream_channel_info(...)`

GigE support is camera-model-dependent and SDK/DLL-symbol-dependent. These APIs
remain camera-local SDK primitives. They do not implement a network service,
packet streaming service, discovery daemon, sidecar process, shared memory, ZMQ,
IPC, or `optic_system` integration.

The raw layer also binds `fc2SetGigEStreamChannelInfo()` as an optional SDK
function, but no high-level stream-channel setter is exposed in this milestone
because stream channel writes can disconnect or disrupt transport. Hardware
write tests use same-value smoke checks and avoid active packet size, packet
delay, IP address, subnet mask, gateway, and stream channel changes.

## Error handling

Every wrapped FlyCapture2 return code is checked and converted into a typed Python exception from `flycapture2_c.errors`.

## Intentionally not wrapped in this project

- GUI APIs
- network service, packet streaming service, or discovery daemon
- sidecar / IPC / shared memory / ZMQ
- `optic_system` backend code
- LCD/projector synchronization
- experiment automation, acquisition workflow orchestration, calibration
  workflows, or reconstruction workflows
