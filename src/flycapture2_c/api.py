from __future__ import annotations

import ctypes
from threading import Lock

from .ctypes_defs import (
    fc2CameraInfo,
    fc2Config,
    fc2Context,
    fc2Error,
    fc2Format7ImageSettings,
    fc2Format7Info,
    fc2Format7PacketInfo,
    fc2FrameRate,
    fc2Image,
    fc2Mode,
    fc2PGRGuid,
    fc2PixelFormat,
    fc2Property,
    fc2PropertyInfo,
    fc2TimeStamp,
    fc2TriggerMode,
    fc2TriggerModeInfo,
    fc2Version,
    fc2VideoMode,
)
from .dll import load_library
from .errors import FC2ErrorCode, raise_for_error
from .errors import FlyCapture2NotSupportedError
from .raw.specs import bind_function_specs
from .raw.structs import (
    fc2CameraStats,
    fc2EmbeddedImageInfo,
    fc2GigEConfig,
    fc2GigEImageSettings,
    fc2GigEImageSettingsInfo,
    fc2GigEProperty,
    fc2GigEStreamChannel,
    fc2ImageMetadata,
    fc2StrobeControl,
    fc2StrobeInfo,
)


class FlyCapture2CAPI:
    def __init__(self) -> None:
        self._dll: ctypes.CDLL | None = None
        self._lock = Lock()

    @property
    def dll(self) -> ctypes.CDLL:
        if self._dll is None:
            with self._lock:
                if self._dll is None:
                    self._dll = load_library()
                    self._bind(self._dll)
        return self._dll

    def _bind(self, dll: ctypes.CDLL) -> None:
        bind_function_specs(dll)

    def _error_description(self, code: int) -> str | None:
        raw = self.dll.fc2ErrorToDescription(code)
        if not raw:
            return None
        return raw.decode("utf-8", errors="replace")

    def _check(self, code: int, operation: str) -> None:
        if code == FC2ErrorCode.OK:
            return
        raise_for_error(code, description=self._error_description(code), operation=operation)

    def _require_function(self, name: str):
        try:
            return getattr(self.dll, name)
        except AttributeError as exc:
            raise FlyCapture2NotSupportedError(
                f"This FlyCapture2 C DLL does not export {name}()."
            ) from exc

    def create_context(self) -> fc2Context:
        context = fc2Context()
        self._check(self.dll.fc2CreateContext(ctypes.byref(context)), "fc2CreateContext")
        return context

    def destroy_context(self, context: fc2Context) -> None:
        self._check(self.dll.fc2DestroyContext(context), "fc2DestroyContext")

    def get_num_cameras(self, context: fc2Context) -> int:
        count = ctypes.c_uint32()
        self._check(self.dll.fc2GetNumOfCameras(context, ctypes.byref(count)), "fc2GetNumOfCameras")
        return int(count.value)

    def get_camera_from_index(self, context: fc2Context, index: int) -> fc2PGRGuid:
        guid = fc2PGRGuid()
        self._check(self.dll.fc2GetCameraFromIndex(context, index, ctypes.byref(guid)), "fc2GetCameraFromIndex")
        return guid

    def get_camera_info(self, context: fc2Context) -> fc2CameraInfo:
        info = fc2CameraInfo()
        self._check(self.dll.fc2GetCameraInfo(context, ctypes.byref(info)), "fc2GetCameraInfo")
        return info

    def get_property_info(self, context: fc2Context, property_type: int) -> fc2PropertyInfo:
        prop_info = fc2PropertyInfo()
        prop_info.type = property_type
        self._check(self.dll.fc2GetPropertyInfo(context, ctypes.byref(prop_info)), "fc2GetPropertyInfo")
        return prop_info

    def get_property(self, context: fc2Context, property_type: int) -> fc2Property:
        prop = fc2Property()
        prop.type = property_type
        self._check(self.dll.fc2GetProperty(context, ctypes.byref(prop)), "fc2GetProperty")
        return prop

    def set_property(self, context: fc2Context, prop: fc2Property) -> None:
        self._check(self.dll.fc2SetProperty(context, ctypes.byref(prop)), "fc2SetProperty")

    def get_embedded_image_info(self, context: fc2Context) -> fc2EmbeddedImageInfo:
        info = fc2EmbeddedImageInfo()
        self._check(
            self.dll.fc2GetEmbeddedImageInfo(context, ctypes.byref(info)),
            "fc2GetEmbeddedImageInfo",
        )
        return info

    def set_embedded_image_info(self, context: fc2Context, info: fc2EmbeddedImageInfo) -> None:
        self._check(
            self.dll.fc2SetEmbeddedImageInfo(context, ctypes.byref(info)),
            "fc2SetEmbeddedImageInfo",
        )

    def get_configuration(self, context: fc2Context) -> fc2Config:
        config = fc2Config()
        self._check(self.dll.fc2GetConfiguration(context, ctypes.byref(config)), "fc2GetConfiguration")
        return config

    def set_configuration(self, context: fc2Context, config: fc2Config) -> None:
        self._check(self.dll.fc2SetConfiguration(context, ctypes.byref(config)), "fc2SetConfiguration")

    def get_gpio_pin_direction(self, context: fc2Context, pin: int) -> int:
        get_gpio_pin_direction = self._require_function("fc2GetGPIOPinDirection")
        direction = ctypes.c_uint32()
        self._check(
            get_gpio_pin_direction(context, ctypes.c_uint32(pin), ctypes.byref(direction)),
            "fc2GetGPIOPinDirection",
        )
        return int(direction.value)

    def set_gpio_pin_direction(self, context: fc2Context, pin: int, direction: int, *, broadcast: bool = False) -> None:
        operation = "fc2SetGPIOPinDirectionBroadcast" if broadcast else "fc2SetGPIOPinDirection"
        function = self._require_function(operation)
        self._check(function(context, ctypes.c_uint32(pin), ctypes.c_uint32(direction)), operation)

    def get_camera_stats(self, context: fc2Context) -> fc2CameraStats:
        stats = fc2CameraStats()
        self._check(self.dll.fc2GetStats(context, ctypes.byref(stats)), "fc2GetStats")
        return stats

    def reset_camera_stats(self) -> None:
        try:
            reset_stats = self.dll.ResetStats
        except AttributeError as exc:
            raise FlyCapture2NotSupportedError(
                "This FlyCapture2 C DLL does not export ResetStats()."
            ) from exc
        self._check(reset_stats(), "ResetStats")

    def get_format7_info(self, context: fc2Context, mode: int) -> tuple[fc2Format7Info, bool]:
        info = fc2Format7Info()
        info.mode = fc2Mode(mode)
        supported = ctypes.c_int()
        self._check(
            self.dll.fc2GetFormat7Info(context, ctypes.byref(info), ctypes.byref(supported)),
            "fc2GetFormat7Info",
        )
        return info, bool(supported.value)

    def validate_format7_settings(
        self,
        context: fc2Context,
        settings: fc2Format7ImageSettings,
    ) -> tuple[bool, fc2Format7PacketInfo]:
        settings_are_valid = ctypes.c_int()
        packet_info = fc2Format7PacketInfo()
        self._check(
            self.dll.fc2ValidateFormat7Settings(
                context,
                ctypes.byref(settings),
                ctypes.byref(settings_are_valid),
                ctypes.byref(packet_info),
            ),
            "fc2ValidateFormat7Settings",
        )
        return bool(settings_are_valid.value), packet_info

    def get_format7_configuration(self, context: fc2Context) -> tuple[fc2Format7ImageSettings, int, float]:
        settings = fc2Format7ImageSettings()
        packet_size = ctypes.c_uint32()
        percentage = ctypes.c_float()
        self._check(
            self.dll.fc2GetFormat7Configuration(
                context,
                ctypes.byref(settings),
                ctypes.byref(packet_size),
                ctypes.byref(percentage),
            ),
            "fc2GetFormat7Configuration",
        )
        return settings, int(packet_size.value), float(percentage.value)

    def set_format7_configuration_packet(
        self,
        context: fc2Context,
        settings: fc2Format7ImageSettings,
        packet_size: int,
    ) -> None:
        self._check(
            self.dll.fc2SetFormat7ConfigurationPacket(context, ctypes.byref(settings), ctypes.c_uint32(packet_size)),
            "fc2SetFormat7ConfigurationPacket",
        )

    def set_format7_configuration(
        self,
        context: fc2Context,
        settings: fc2Format7ImageSettings,
        percent_speed: float,
    ) -> None:
        self._check(
            self.dll.fc2SetFormat7Configuration(context, ctypes.byref(settings), ctypes.c_float(percent_speed)),
            "fc2SetFormat7Configuration",
        )

    def get_trigger_mode_info(self, context: fc2Context) -> fc2TriggerModeInfo:
        trigger_mode_info = fc2TriggerModeInfo()
        self._check(
            self.dll.fc2GetTriggerModeInfo(context, ctypes.byref(trigger_mode_info)),
            "fc2GetTriggerModeInfo",
        )
        return trigger_mode_info

    def get_trigger_mode(self, context: fc2Context) -> fc2TriggerMode:
        trigger_mode = fc2TriggerMode()
        self._check(self.dll.fc2GetTriggerMode(context, ctypes.byref(trigger_mode)), "fc2GetTriggerMode")
        return trigger_mode

    def set_trigger_mode(self, context: fc2Context, trigger_mode: fc2TriggerMode) -> None:
        self._check(self.dll.fc2SetTriggerMode(context, ctypes.byref(trigger_mode)), "fc2SetTriggerMode")

    def set_trigger_mode_broadcast(self, context: fc2Context, trigger_mode: fc2TriggerMode) -> None:
        self._check(
            self.dll.fc2SetTriggerModeBroadcast(context, ctypes.byref(trigger_mode)),
            "fc2SetTriggerModeBroadcast",
        )

    def fire_software_trigger(self, context: fc2Context, *, broadcast: bool = False) -> None:
        operation = "fc2FireSoftwareTriggerBroadcast" if broadcast else "fc2FireSoftwareTrigger"
        function = self._require_function(operation)
        self._check(function(context), operation)

    def get_gige_property(self, context: fc2Context, property_type: int) -> fc2GigEProperty:
        function = self._require_function("fc2GetGigEProperty")
        prop = fc2GigEProperty()
        prop.propType = int(property_type)
        self._check(function(context, ctypes.byref(prop)), "fc2GetGigEProperty")
        return prop

    def set_gige_property(self, context: fc2Context, prop: fc2GigEProperty) -> None:
        function = self._require_function("fc2SetGigEProperty")
        self._check(function(context, ctypes.byref(prop)), "fc2SetGigEProperty")

    def discover_gige_packet_size(self, context: fc2Context) -> int:
        function = self._require_function("fc2DiscoverGigEPacketSize")
        packet_size = ctypes.c_uint32()
        self._check(function(context, ctypes.byref(packet_size)), "fc2DiscoverGigEPacketSize")
        return int(packet_size.value)

    def query_gige_imaging_mode(self, context: fc2Context, mode: int) -> bool:
        function = self._require_function("fc2QueryGigEImagingMode")
        supported = ctypes.c_int()
        self._check(function(context, fc2Mode(mode), ctypes.byref(supported)), "fc2QueryGigEImagingMode")
        return bool(supported.value)

    def get_gige_imaging_mode(self, context: fc2Context) -> int:
        function = self._require_function("fc2GetGigEImagingMode")
        mode = fc2Mode()
        self._check(function(context, ctypes.byref(mode)), "fc2GetGigEImagingMode")
        return int(mode.value)

    def set_gige_imaging_mode(self, context: fc2Context, mode: int) -> None:
        function = self._require_function("fc2SetGigEImagingMode")
        self._check(function(context, fc2Mode(mode)), "fc2SetGigEImagingMode")

    def get_gige_image_settings_info(self, context: fc2Context) -> fc2GigEImageSettingsInfo:
        function = self._require_function("fc2GetGigEImageSettingsInfo")
        info = fc2GigEImageSettingsInfo()
        self._check(function(context, ctypes.byref(info)), "fc2GetGigEImageSettingsInfo")
        return info

    def get_gige_image_settings(self, context: fc2Context) -> fc2GigEImageSettings:
        function = self._require_function("fc2GetGigEImageSettings")
        settings = fc2GigEImageSettings()
        self._check(function(context, ctypes.byref(settings)), "fc2GetGigEImageSettings")
        return settings

    def set_gige_image_settings(self, context: fc2Context, settings: fc2GigEImageSettings) -> None:
        function = self._require_function("fc2SetGigEImageSettings")
        self._check(function(context, ctypes.byref(settings)), "fc2SetGigEImageSettings")

    def get_gige_image_binning_settings(self, context: fc2Context) -> tuple[int, int]:
        function = self._require_function("fc2GetGigEImageBinningSettings")
        horizontal = ctypes.c_uint32()
        vertical = ctypes.c_uint32()
        self._check(
            function(context, ctypes.byref(horizontal), ctypes.byref(vertical)),
            "fc2GetGigEImageBinningSettings",
        )
        return int(horizontal.value), int(vertical.value)

    def set_gige_image_binning_settings(self, context: fc2Context, horizontal: int, vertical: int) -> None:
        function = self._require_function("fc2SetGigEImageBinningSettings")
        self._check(
            function(context, ctypes.c_uint32(horizontal), ctypes.c_uint32(vertical)),
            "fc2SetGigEImageBinningSettings",
        )

    def get_num_gige_stream_channels(self, context: fc2Context) -> int:
        function = self._require_function("fc2GetNumStreamChannels")
        count = ctypes.c_uint32()
        self._check(function(context, ctypes.byref(count)), "fc2GetNumStreamChannels")
        return int(count.value)

    def get_gige_stream_channel_info(self, context: fc2Context, channel: int) -> fc2GigEStreamChannel:
        function = self._require_function("fc2GetGigEStreamChannelInfo")
        stream_channel = fc2GigEStreamChannel()
        self._check(
            function(context, ctypes.c_uint32(channel), ctypes.byref(stream_channel)),
            "fc2GetGigEStreamChannelInfo",
        )
        return stream_channel

    def set_gige_stream_channel_info(
        self,
        context: fc2Context,
        channel: int,
        stream_channel: fc2GigEStreamChannel,
    ) -> None:
        function = self._require_function("fc2SetGigEStreamChannelInfo")
        self._check(
            function(context, ctypes.c_uint32(channel), ctypes.byref(stream_channel)),
            "fc2SetGigEStreamChannelInfo",
        )

    def get_gige_config(self, context: fc2Context) -> fc2GigEConfig:
        function = self._require_function("fc2GetGigEConfig")
        config = fc2GigEConfig()
        self._check(function(context, ctypes.byref(config)), "fc2GetGigEConfig")
        return config

    def set_gige_config(self, context: fc2Context, config: fc2GigEConfig) -> None:
        function = self._require_function("fc2SetGigEConfig")
        self._check(function(context, ctypes.byref(config)), "fc2SetGigEConfig")

    def get_strobe_info(self, context: fc2Context, source: int) -> fc2StrobeInfo:
        info = fc2StrobeInfo()
        info.source = int(source)
        self._check(self.dll.fc2GetStrobeInfo(context, ctypes.byref(info)), "fc2GetStrobeInfo")
        return info

    def get_strobe(self, context: fc2Context, source: int) -> fc2StrobeControl:
        control = fc2StrobeControl()
        control.source = int(source)
        self._check(self.dll.fc2GetStrobe(context, ctypes.byref(control)), "fc2GetStrobe")
        return control

    def set_strobe(self, context: fc2Context, control: fc2StrobeControl, *, broadcast: bool = False) -> None:
        if broadcast:
            set_strobe_broadcast = self._require_function("fc2SetStrobeBroadcast")
            self._check(
                set_strobe_broadcast(context, ctypes.byref(control)),
                "fc2SetStrobeBroadcast",
            )
        else:
            self._check(self.dll.fc2SetStrobe(context, ctypes.byref(control)), "fc2SetStrobe")

    def connect(self, context: fc2Context, guid: fc2PGRGuid) -> None:
        self._check(self.dll.fc2Connect(context, ctypes.byref(guid)), "fc2Connect")

    def disconnect(self, context: fc2Context) -> None:
        self._check(self.dll.fc2Disconnect(context), "fc2Disconnect")

    def is_connected(self, context: fc2Context) -> bool:
        return bool(self.dll.fc2IsConnected(context))

    def start_capture(self, context: fc2Context) -> None:
        self._check(self.dll.fc2StartCapture(context), "fc2StartCapture")

    def stop_capture(self, context: fc2Context) -> None:
        self._check(self.dll.fc2StopCapture(context), "fc2StopCapture")

    def create_image(self) -> fc2Image:
        image = fc2Image()
        self._check(self.dll.fc2CreateImage(ctypes.byref(image)), "fc2CreateImage")
        return image

    def destroy_image(self, image: fc2Image) -> None:
        self._check(self.dll.fc2DestroyImage(ctypes.byref(image)), "fc2DestroyImage")

    def retrieve_buffer(self, context: fc2Context, image: fc2Image) -> None:
        self._check(self.dll.fc2RetrieveBuffer(context, ctypes.byref(image)), "fc2RetrieveBuffer")

    def get_image_dimensions(self, image: fc2Image) -> tuple[int, int, int, int]:
        rows = ctypes.c_uint32()
        cols = ctypes.c_uint32()
        stride = ctypes.c_uint32()
        pixel_format = fc2PixelFormat()
        bayer_format = ctypes.c_uint32()
        self._check(
            self.dll.fc2GetImageDimensions(
                ctypes.byref(image),
                ctypes.byref(rows),
                ctypes.byref(cols),
                ctypes.byref(stride),
                ctypes.byref(pixel_format),
                ctypes.byref(bayer_format),
            ),
            "fc2GetImageDimensions",
        )
        return int(rows.value), int(cols.value), int(stride.value), int(pixel_format.value)

    def get_image_data_pointer(self, image: fc2Image) -> ctypes.POINTER(ctypes.c_ubyte):
        data_ptr = ctypes.POINTER(ctypes.c_ubyte)()
        self._check(self.dll.fc2GetImageData(ctypes.byref(image), ctypes.byref(data_ptr)), "fc2GetImageData")
        return data_ptr

    def get_image_metadata(self, image: fc2Image) -> fc2ImageMetadata:
        metadata = fc2ImageMetadata()
        self._check(
            self.dll.fc2GetImageMetadata(ctypes.byref(image), ctypes.byref(metadata)),
            "fc2GetImageMetadata",
        )
        return metadata

    def get_image_timestamp(self, image: fc2Image) -> fc2TimeStamp:
        return self.dll.fc2GetImageTimeStamp(ctypes.byref(image))

    def get_video_mode_and_frame_rate(self, context: fc2Context) -> tuple[int, int]:
        video_mode = fc2VideoMode()
        frame_rate = fc2FrameRate()
        self._check(
            self.dll.fc2GetVideoModeAndFrameRate(context, ctypes.byref(video_mode), ctypes.byref(frame_rate)),
            "fc2GetVideoModeAndFrameRate",
        )
        return int(video_mode.value), int(frame_rate.value)

    def get_library_version(self) -> tuple[int, int, int, int]:
        version = fc2Version()
        self._check(self.dll.fc2GetLibraryVersion(ctypes.byref(version)), "fc2GetLibraryVersion")
        return (int(version.major), int(version.minor), int(version.type), int(version.build))


_API: FlyCapture2CAPI | None = None


def get_api() -> FlyCapture2CAPI:
    global _API
    if _API is None:
        _API = FlyCapture2CAPI()
    return _API
