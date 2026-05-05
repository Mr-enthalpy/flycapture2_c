# API Coverage

This table tracks the FlyCapture2 C API surface wrapped by this project. It is not a full SDK coverage claim.

| Category | Function | Structs required | Raw binding status | High-level API status | No-hardware test status | Hardware readonly test status | Hardware write test status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Raw infrastructure | current wrapped function signatures | `FunctionSpec` registry | `raw/specs.py` introduced | used by existing `FlyCapture2CAPI` binding path | covered | not-applicable | not-applicable | Stage 4.5 bridge; checked calls still live in top-level `api.py` for compatibility. |
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
| Properties | `fc2GetPropertyInfo` | `fc2PropertyInfo` | raw-bound | `Camera.get_property_info`, `Camera.list_property_infos`, `Camera.snapshot_properties` | covered | covered by opt-in property readonly test | covered through opt-in reversible property test | All known `PropertyType` values are discoverable. |
| Properties | `fc2GetProperty` | `fc2Property` | raw-bound | `Camera.get_property`, `Camera.get_property_raw`, `Camera.list_properties`, convenience getters | covered | covered by opt-in property readonly test | covered through opt-in reversible property test | Typed dataclass result for safe API, raw ctypes for advanced API. |
| Properties | `fc2SetProperty` | `fc2Property` | raw-bound | `Camera.set_property`, `set_property_raw`, `set_property_abs`, `set_property_integer`, `set_property_on_off`, `set_property_auto`, `set_property_one_push`, convenience setters | covered | not-applicable | covered through opt-in reversible property test | Strict generic helpers check present, mode support, write support, and ranges. |
| Trigger | `fc2GetTriggerModeInfo` | `fc2TriggerModeInfo` | raw-bound | `Camera.get_trigger_mode_info` | covered | covered by opt-in trigger readonly test | not-applicable | Dedicated trigger API, no GUI. |
| Trigger | `fc2GetTriggerMode` | `fc2TriggerMode` | raw-bound | `Camera.get_trigger_mode` | covered | covered by opt-in trigger readonly test | covered by opt-in reversible trigger write test | Dedicated trigger API, no GUI. |
| Trigger | `fc2SetTriggerMode` | `fc2TriggerMode` | raw-bound | `Camera.set_trigger_mode`, `Camera.enable_trigger`, `Camera.disable_trigger` | covered with fake API | not-applicable | covered by opt-in reversible trigger write test | Writes save and restore old trigger state in hardware test. |
| Trigger | `fc2SetTriggerModeBroadcast` | `fc2TriggerMode` | raw-bound | explicit `broadcast=True` | covered with fake API | not-applicable | not-run-by-default | Bound because the C header exposes it and the signature is straightforward. |
| Format7 | `fc2GetFormat7Info` | `fc2Format7Info` | raw-bound | `Camera.get_format7_info` | covered | opt-in readonly test added | not-applicable | Queries mode support and pixel format mask. |
| Format7 | `fc2ValidateFormat7Settings` | `fc2Format7ImageSettings`, `fc2Format7PacketInfo` | raw-bound | `Camera.validate_format7` | covered | not-applicable | used by opt-in reversible Format7 write test | Validation does not apply settings. |
| Format7 | `fc2GetFormat7Configuration` | `fc2Format7ImageSettings` | raw-bound | `Camera.get_format7_configuration` | covered | opt-in readonly test added when camera is already in Format7 | used by opt-in reversible Format7 write test | SDK call only succeeds when camera is in Format7. |
| Format7 | `fc2SetFormat7ConfigurationPacket` | `fc2Format7ImageSettings` | raw-bound | `Camera.set_format7`, `Camera.set_roi`, `Camera.set_pixel_format` | covered | not-applicable | opt-in reversible write test added | High-level API uses validated packet size. |
| Format7 | `fc2SetFormat7Configuration` | `fc2Format7ImageSettings` | raw-bound | raw-level method only | covered | not-applicable | not-run-by-default | Percent-speed variant is bound but not used by default high-level helpers. |
| Configuration | `fc2GetConfiguration` | `fc2Config` | raw-bound | `Camera.get_configuration` | covered | opt-in readonly test added | used by opt-in reversible config write test | SDK-level config, distinct from smoke-test wall-clock timeout. |
| Configuration | `fc2SetConfiguration` | `fc2Config` | raw-bound | `Camera.set_configuration`, `Camera.set_grab_timeout`, `Camera.set_grab_mode` | covered | not-applicable | opt-in reversible grab-timeout write test added | Saves and restores previous config in hardware test. |

Deferred in this milestone:

- GigE
- strobe / GPIO
- register access
- software trigger firing
- embedded metadata API
- callbacks / events
