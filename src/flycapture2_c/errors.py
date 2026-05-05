from __future__ import annotations

from enum import IntEnum


class FC2ErrorCode(IntEnum):
    UNDEFINED = -1
    OK = 0
    FAILED = 1
    NOT_IMPLEMENTED = 2
    FAILED_BUS_MASTER_CONNECTION = 3
    NOT_CONNECTED = 4
    INIT_FAILED = 5
    NOT_INITIALIZED = 6
    INVALID_PARAMETER = 7
    INVALID_SETTINGS = 8
    INVALID_BUS_MANAGER = 9
    MEMORY_ALLOCATION_FAILED = 10
    LOW_LEVEL_FAILURE = 11
    NOT_FOUND = 12
    FAILED_GUID = 13
    INVALID_PACKET_SIZE = 14
    INVALID_MODE = 15
    NOT_IN_FORMAT7 = 16
    NOT_SUPPORTED = 17
    TIMEOUT = 18
    BUS_MASTER_FAILED = 19
    INVALID_GENERATION = 20
    LUT_FAILED = 21
    IIDC_FAILED = 22
    STROBE_FAILED = 23
    TRIGGER_FAILED = 24
    PROPERTY_FAILED = 25
    PROPERTY_NOT_PRESENT = 26
    REGISTER_FAILED = 27
    READ_REGISTER_FAILED = 28
    WRITE_REGISTER_FAILED = 29
    ISOCH_FAILED = 30
    ISOCH_ALREADY_STARTED = 31
    ISOCH_NOT_STARTED = 32
    ISOCH_START_FAILED = 33
    ISOCH_RETRIEVE_BUFFER_FAILED = 34
    ISOCH_STOP_FAILED = 35
    ISOCH_SYNC_FAILED = 36
    ISOCH_BANDWIDTH_EXCEEDED = 37
    IMAGE_CONVERSION_FAILED = 38
    IMAGE_LIBRARY_FAILURE = 39
    BUFFER_TOO_SMALL = 40
    IMAGE_CONSISTENCY_ERROR = 41
    INCOMPATIBLE_DRIVER = 42


class FlyCapture2Error(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: FC2ErrorCode | int | None = None,
        description: str | None = None,
        operation: str | None = None,
    ) -> None:
        self.code = _coerce_code(code)
        self.description = description
        self.operation = operation
        super().__init__(message)


class SDKNotFoundError(FlyCapture2Error):
    pass


class DLLLoadError(FlyCapture2Error):
    pass


class CameraStateError(FlyCapture2Error):
    pass


class UnsupportedPixelFormatError(FlyCapture2Error):
    pass


class UnsupportedPropertyError(FlyCapture2Error):
    pass


class PropertyNotWritableError(FlyCapture2Error):
    pass


class PropertyOutOfRangeError(FlyCapture2Error):
    pass


class PropertyModeError(FlyCapture2Error):
    pass


class UnsupportedTriggerError(FlyCapture2Error):
    pass


class TriggerModeError(FlyCapture2Error):
    pass


class UnsupportedFormat7Error(FlyCapture2Error):
    pass


class Format7ValidationError(FlyCapture2Error):
    pass


class CameraConfigurationError(FlyCapture2Error):
    pass


class UnsupportedMetadataError(FlyCapture2Error):
    pass


class FlyCapture2Failure(FlyCapture2Error):
    pass


class FlyCapture2NotConnectedError(FlyCapture2Error):
    pass


class FlyCapture2InvalidParameterError(FlyCapture2Error):
    pass


class FlyCapture2NotFoundError(FlyCapture2Error):
    pass


class FlyCapture2TimeoutError(FlyCapture2Error):
    pass


class FlyCapture2NotSupportedError(FlyCapture2Error):
    pass


class FlyCapture2CaptureStateError(FlyCapture2Error):
    pass


ERROR_CLASS_MAP: dict[FC2ErrorCode, type[FlyCapture2Error]] = {
    FC2ErrorCode.FAILED: FlyCapture2Failure,
    FC2ErrorCode.NOT_CONNECTED: FlyCapture2NotConnectedError,
    FC2ErrorCode.INVALID_PARAMETER: FlyCapture2InvalidParameterError,
    FC2ErrorCode.NOT_FOUND: FlyCapture2NotFoundError,
    FC2ErrorCode.TIMEOUT: FlyCapture2TimeoutError,
    FC2ErrorCode.NOT_SUPPORTED: FlyCapture2NotSupportedError,
    FC2ErrorCode.ISOCH_ALREADY_STARTED: FlyCapture2CaptureStateError,
    FC2ErrorCode.ISOCH_NOT_STARTED: FlyCapture2CaptureStateError,
    FC2ErrorCode.ISOCH_START_FAILED: FlyCapture2CaptureStateError,
    FC2ErrorCode.ISOCH_STOP_FAILED: FlyCapture2CaptureStateError,
    FC2ErrorCode.ISOCH_RETRIEVE_BUFFER_FAILED: FlyCapture2CaptureStateError,
}


def _coerce_code(code: FC2ErrorCode | int | None) -> FC2ErrorCode | int | None:
    if code is None:
        return None
    if isinstance(code, FC2ErrorCode):
        return code
    try:
        return FC2ErrorCode(code)
    except ValueError:
        return int(code)


def build_error_message(
    *,
    code: FC2ErrorCode | int,
    description: str | None = None,
    operation: str | None = None,
) -> str:
    typed_code = _coerce_code(code)
    if isinstance(typed_code, FC2ErrorCode):
        code_name = typed_code.name
        code_value = typed_code.value
    else:
        code_name = "UNKNOWN"
        code_value = typed_code

    prefix = f"{operation} failed" if operation else "FlyCapture2 call failed"
    if description:
        return f"{prefix}: {code_name} ({code_value}) - {description}"
    return f"{prefix}: {code_name} ({code_value})"


def exception_from_error(
    code: FC2ErrorCode | int,
    *,
    description: str | None = None,
    operation: str | None = None,
) -> FlyCapture2Error:
    typed_code = _coerce_code(code)
    exc_class = ERROR_CLASS_MAP.get(typed_code, FlyCapture2Error) if isinstance(typed_code, FC2ErrorCode) else FlyCapture2Error
    return exc_class(
        build_error_message(code=code, description=description, operation=operation),
        code=typed_code,
        description=description,
        operation=operation,
    )


def raise_for_error(
    code: FC2ErrorCode | int,
    *,
    description: str | None = None,
    operation: str | None = None,
) -> None:
    typed_code = _coerce_code(code)
    if typed_code == FC2ErrorCode.OK:
        return
    raise exception_from_error(typed_code if typed_code is not None else code, description=description, operation=operation)
