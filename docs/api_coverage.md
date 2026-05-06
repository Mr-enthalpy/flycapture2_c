# API Coverage

This table tracks the FlyCapture2 C API surface wrapped by this project. The
current wrapped SDK surface is broad but not complete. Stage 6.5 is focused on
validation and stabilization of the existing wrapper, not new SDK feature
surface.

Deferred areas include register access, callbacks/events, and broader raw SDK
coverage. Multi-camera compatibility evidence is limited to the currently
available hardware. Do not read this table as a claim of full SDK coverage or
broad hardware compatibility.

| Category | Function | Structs required | Raw binding status | High-level API status | No-hardware test status | Hardware readonly test status | Hardware write test status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Raw infrastructure | current wrapped function signatures | `FunctionSpec` registry | `raw/specs.py` introduced | used by existing `FlyCapture2CAPI` binding path | covered | not-applicable | not-applicable | Stage 4.5 bridge; checked calls still live in top-level `api.py` for compatibility. |
| Validation tooling | current wrapped capability surface | existing high-level wrappers | not-applicable | scripts only | covered by no-hardware script tests | `scripts/hardware_capability_report.py` and `scripts/run_hardware_validation.py` | write groups require `--include-write` and `FLYCAPTURE2_HARDWARE_WRITE_TEST=1` | No new SDK function surface; diagnostic and pytest orchestration only. |
| Context | `fc2CreateContext` | `fc2Context` | raw-bound | internal lifecycle | covered | covered through opt-in enumerate/open tests | not-applicable | Lazy loaded. |
| Context | `fc2DestroyContext` | `fc2Context` | raw-bound | internal lifecycle | covered | covered through opt-in enumerate/open tests | not-applicable | Cleanup path. |
| Bus | `fc2GetNumOfCameras` | `fc2Context` | raw-bound | `enumerate_cameras`, `Camera.open` | covered | covered | not-applicable | Hardware tests remain opt-in. |
| Bus | `fc2GetCameraFromIndex` | `fc2PGRGuid` | raw-bound | `enumerate_cameras`, `Camera.open` | covered | covered | not-applicable | GUID is copied into `CameraDescriptor`. |
| Camera | `fc2Connect` | `fc2PGRGuid` | raw-bound | `Camera.open` | covered with fake API | covered | not-applicable | No constructor-side hardware access. |
| Camera | `fc2Disconnect` | `fc2Context` | raw-bound | `Camera.close` | covered with fake API | covered | not-applicable | Idempotent high-level cleanup. |
| Camera | `fc2GetCameraInfo` | `fc2CameraInfo` | raw-bound | `Camera.get_camera_info` | covered | covered | not-applicable | Metadata only. |
| Camera | `fc2GetVideoModeAndFrameRate` | `fc2VideoMode`, `fc2FrameRate` | raw-bound | `Camera.get_video_mode_and_frame_rate` | covered | covered | not-applicable | Metadata only. |
| Capture | `fc2StartCapture` | `fc2Context` | raw-bound | `Camera.start` | covered with mock/fake API | covered | not-applicable | No default hardware access. |
| Capture | `fc2RetrieveBuffer` | `fc2Image` | raw-bound | `Camera.read_frame`, `Camera.read_frame_with_info` | covered with mock/image tests | covered | not-applicable | Public array is owned NumPy memory. |
| Capture | `fc2StopCapture` | `fc2Context` | raw-bound | `Camera.stop` | covered with mock/fake API | covered | not-applicable | Idempotent high-level cleanup. |
| Image | `fc2GetImageDimensions` | `fc2Image` | raw-bound | internal frame conversion | covered | covered through opt-in capture tests | not-applicable | Supports initial mono/raw formats. |
| Image | `fc2GetImageData` | `fc2Image` | raw-bound | internal frame copy | covered | covered through opt-in capture tests | not-applicable | Does not expose SDK pointer. |
| Image | `fc2GetImageMetadata` | `fc2ImageMetadata` | raw-bound | `ImageFrame.metadata` via `Camera.read_frame_with_info` | covered | covered through opt-in grab-one and metadata tests | not-applicable | Metadata values are copied into `ImageMetadata`; support depends on enabled embedded fields. |
| Metadata | `fc2GetEmbeddedImageInfo` | `fc2EmbeddedImageInfo` | raw-bound | `Camera.get_embedded_image_info` | covered | covered by opt-in metadata readonly test | used by opt-in reversible metadata write test | Exposes availability and enabled state for each embedded field. |
| Metadata | `fc2SetEmbeddedImageInfo` | `fc2EmbeddedImageInfo` | raw-bound | `Camera.set_embedded_image_info` | covered | not-applicable | covered by opt-in reversible metadata write test | High-level API rejects explicit writes to unavailable fields. |
| Diagnostics | `fc2GetStats` | `fc2CameraStats` | raw-bound | `Camera.get_camera_stats` | covered | covered by opt-in metadata readonly test | not-applicable | Readonly diagnostic counters and sensor values. |
| Diagnostics | `ResetStats` | none | optional raw-bound | `Camera.reset_camera_stats` | covered | not-applicable | write-gated test added | Header exposes `ResetStats()` without an `fc2` prefix or context; binding is optional to tolerate DLL differences. |
| Strobe | `fc2GetStrobeInfo` | `fc2StrobeInfo` | raw-bound | `Camera.get_strobe_info` | covered | opt-in readonly test added | not-applicable | Source/channel support is camera-model-dependent. |
| Strobe | `fc2GetStrobe` | `fc2StrobeControl` | raw-bound | `Camera.get_strobe` | covered | opt-in readonly test added when readout is supported | used by opt-in reversible strobe write test | High-level read validates source presence and readout support. |
| Strobe | `fc2SetStrobe` | `fc2StrobeControl` | raw-bound | `Camera.set_strobe` | covered | not-applicable | same-value write smoke test added | High-level write starts from current state, applies explicit fields, validates capabilities/ranges, and reads back. The hardware test does not actively toggle external strobe output. |
| Strobe | `fc2SetStrobeBroadcast` | `fc2StrobeControl` | optional raw-bound | `Camera.set_strobe(..., broadcast=True)` | covered with fake API | not-applicable | not-run-by-default | Optional symbol; calling broadcast on a DLL that lacks it raises `FlyCapture2NotSupportedError`. |
| GPIO | `fc2GetGPIOPinDirection` | none | optional raw-bound | `Camera.get_gpio_pin_direction` | covered | opt-in readonly test added | not-applicable | Optional symbol. Direct C API pin-direction read only; GPIO pin-state frame readback is embedded metadata. |
| GPIO | `fc2SetGPIOPinDirection` | none | optional raw-bound | `Camera.set_gpio_pin_direction` | covered | not-applicable | opt-in same-value write test added | Optional symbol. Write is explicit and opt-in for hardware tests. No register-level GPIO control is implemented. |
| GPIO | `fc2SetGPIOPinDirectionBroadcast` | none | optional raw-bound | `Camera.set_gpio_pin_direction(..., broadcast=True)` | covered with fake API | not-applicable | not-run-by-default | Optional symbol. Direct C API broadcast direction write only. |
| Properties | `fc2GetPropertyInfo` | `fc2PropertyInfo` | raw-bound | `Camera.get_property_info`, `Camera.list_property_infos`, `Camera.snapshot_properties` | covered | covered by opt-in property readonly test | covered through opt-in reversible property test | All known `PropertyType` values are discoverable. |
| Properties | `fc2GetProperty` | `fc2Property` | raw-bound | `Camera.get_property`, `Camera.get_property_raw`, `Camera.list_properties`, convenience getters | covered | covered by opt-in property readonly test | covered through opt-in reversible property test | Typed dataclass result for safe API, raw ctypes for advanced API. |
| Properties | `fc2SetProperty` | `fc2Property` | raw-bound | `Camera.set_property`, `set_property_raw`, `set_property_abs`, `set_property_integer`, `set_property_on_off`, `set_property_auto`, `set_property_one_push`, convenience setters | covered | not-applicable | covered through opt-in reversible property test | Strict generic helpers check present, mode support, write support, and ranges. |
| Trigger | `fc2GetTriggerModeInfo` | `fc2TriggerModeInfo` | raw-bound | `Camera.get_trigger_mode_info` | covered | covered by opt-in trigger readonly test | not-applicable | Dedicated trigger API, no GUI. |
| Trigger | `fc2GetTriggerMode` | `fc2TriggerMode` | raw-bound | `Camera.get_trigger_mode` | covered | covered by opt-in trigger readonly test | covered by opt-in reversible trigger write test | Dedicated trigger API, no GUI. |
| Trigger | `fc2SetTriggerMode` | `fc2TriggerMode` | raw-bound | `Camera.set_trigger_mode`, `Camera.enable_trigger`, `Camera.disable_trigger` | covered with fake API | not-applicable | covered by opt-in reversible trigger write test | Writes save and restore old trigger state in hardware test. |
| Trigger | `fc2SetTriggerModeBroadcast` | `fc2TriggerMode` | raw-bound | explicit `broadcast=True` | covered with fake API | not-applicable | not-run-by-default | Bound because the C header exposes it and the signature is straightforward. |
| Trigger | `fc2FireSoftwareTrigger` | none | optional raw-bound | `Camera.fire_software_trigger` | covered | not-applicable | covered by opt-in software trigger fire-and-grab test | SDK-level primitive only. It does not configure trigger mode, start capture, retrieve a frame, sleep, poll, or schedule acquisition. |
| Trigger | `fc2FireSoftwareTriggerBroadcast` | none | optional raw-bound | `Camera.fire_software_trigger(broadcast=True)` | covered | not-applicable | not-run-by-default | Optional symbol; calling broadcast on a DLL that lacks it raises `FlyCapture2NotSupportedError`. |
| GigE | `fc2GetGigEConfig` | `fc2GigEConfig` | optional raw-bound | `Camera.get_gige_config` | covered | opt-in readonly test added | used by opt-in same-value write test | Camera-model-dependent. Raises `FlyCapture2NotSupportedError` if the DLL lacks the symbol. |
| GigE | `fc2SetGigEConfig` | `fc2GigEConfig` | optional raw-bound | `Camera.set_gige_config` | covered | not-applicable | opt-in same-value write test added | Starts from current/dataclass state, writes explicitly, and reads back. Does not alter capture state. |
| GigE | `fc2GetGigEProperty` | `fc2GigEProperty` | optional raw-bound | `Camera.get_gige_property` | covered | opt-in readonly test added | used by opt-in same-value write test | Covers heartbeat, heartbeat timeout, packet size, and packet delay property types from the C header. |
| GigE | `fc2SetGigEProperty` | `fc2GigEProperty` | optional raw-bound | `Camera.set_gige_property` | covered | not-applicable | opt-in same-value write test added for conservative writable properties | Validates writability and range. Tests avoid changing packet size or packet delay values. |
| GigE | `fc2DiscoverGigEPacketSize` | none | optional raw-bound | `Camera.discover_gige_packet_size` | covered | opt-in readonly helper test added | not-applicable | Discovery only; does not write packet size. |
| GigE | `fc2QueryGigEImagingMode` | `fc2Mode` | optional raw-bound | `Camera.query_gige_imaging_mode` | covered | opt-in readonly helper test added | not-applicable | Readonly support query. |
| GigE | `fc2GetGigEImagingMode` | `fc2Mode` | optional raw-bound | `Camera.get_gige_imaging_mode` | covered | opt-in readonly helper test added | not-applicable | Readonly mode readback. |
| GigE | `fc2SetGigEImagingMode` | `fc2Mode` | optional raw-bound | `Camera.set_gige_imaging_mode` | covered | not-applicable | not-run-by-default | Exposed as explicit SDK primitive; active write testing is deferred because mode changes can affect image settings. |
| GigE | `fc2GetGigEImageSettingsInfo` | `fc2GigEImageSettingsInfo` | optional raw-bound | `Camera.get_gige_image_settings_info` | covered | opt-in readonly test added | not-applicable | Camera-model-dependent image constraints and pixel format mask. |
| GigE | `fc2GetGigEImageSettings` | `fc2GigEImageSettings` | optional raw-bound | `Camera.get_gige_image_settings` | covered | opt-in readonly test added | used by opt-in same-value write test | Camera-side GigE image settings, not Python-side crop. |
| GigE | `fc2SetGigEImageSettings` | `fc2GigEImageSettings` | optional raw-bound | `Camera.set_gige_image_settings` | covered | not-applicable | opt-in same-value write test added | Same-value write smoke only by default; active ROI/pixel changes are caller-controlled. |
| GigE | `fc2GetGigEImageBinningSettings` | none | optional raw-bound | `Camera.get_gige_image_binning_settings` | covered | opt-in readonly through write-test setup where available | used by opt-in same-value write test | Skips cleanly when unsupported. |
| GigE | `fc2SetGigEImageBinningSettings` | none | optional raw-bound | `Camera.set_gige_image_binning_settings` | covered | not-applicable | opt-in same-value write test added | Active binning changes are not part of default hardware validation. |
| GigE | `fc2GetNumStreamChannels` | none | optional raw-bound | `Camera.get_num_gige_stream_channels` | covered | opt-in readonly test added | not-applicable | Stream channel inspection only; no packet streaming service. |
| GigE | `fc2GetGigEStreamChannelInfo` | `fc2GigEStreamChannel` | optional raw-bound | `Camera.get_gige_stream_channel_info` | covered | opt-in readonly test added | not-applicable | Readonly high-level API. |
| GigE | `fc2SetGigEStreamChannelInfo` | `fc2GigEStreamChannel` | optional raw-bound | raw `FlyCapture2CAPI.set_gige_stream_channel_info` only | covered by spec | not-applicable | not-run-by-default | No high-level setter in this milestone; stream channel writes are risky and deferred. |
| Format7 | `fc2GetFormat7Info` | `fc2Format7Info` | raw-bound | `Camera.get_format7_info` | covered | opt-in readonly test added | not-applicable | Queries mode support and pixel format mask. |
| Format7 | `fc2ValidateFormat7Settings` | `fc2Format7ImageSettings`, `fc2Format7PacketInfo` | raw-bound | `Camera.validate_format7` | covered | not-applicable | used by opt-in reversible Format7 write test | Validation does not apply settings. |
| Format7 | `fc2GetFormat7Configuration` | `fc2Format7ImageSettings` | raw-bound | `Camera.get_format7_configuration` | covered | opt-in readonly test added when camera is already in Format7 | used by opt-in reversible Format7 write test | SDK call only succeeds when camera is in Format7. |
| Format7 | `fc2SetFormat7ConfigurationPacket` | `fc2Format7ImageSettings` | raw-bound | `Camera.set_format7`, `Camera.set_roi`, `Camera.set_pixel_format` | covered | not-applicable | opt-in reversible write test added | High-level API uses validated packet size. |
| Format7 | `fc2SetFormat7Configuration` | `fc2Format7ImageSettings` | raw-bound | raw-level method only | covered | not-applicable | not-run-by-default | Percent-speed variant is bound but not used by default high-level helpers. |
| Configuration | `fc2GetConfiguration` | `fc2Config` | raw-bound | `Camera.get_configuration` | covered | opt-in readonly test added | used by opt-in reversible config write test | SDK-level config, distinct from smoke-test wall-clock timeout. |
| Configuration | `fc2SetConfiguration` | `fc2Config` | raw-bound | `Camera.set_configuration`, `Camera.set_grab_timeout`, `Camera.set_grab_mode` | covered | not-applicable | opt-in reversible grab-timeout write test added | Saves and restores previous config in hardware test. |

Deferred in this milestone:

- bus-level GigE discovery and force-IP helpers
- high-level stream-channel writes and risky network-changing operations
- register access
- callbacks / events
