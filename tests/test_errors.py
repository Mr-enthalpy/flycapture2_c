from __future__ import annotations

import pytest

from flycapture2_c.errors import (
    FC2ErrorCode,
    FlyCapture2InvalidParameterError,
    FlyCapture2NotConnectedError,
    build_error_message,
    raise_for_error,
)


def test_raise_for_error_is_noop_for_ok() -> None:
    raise_for_error(FC2ErrorCode.OK, operation="noop")


def test_raise_for_error_maps_not_connected() -> None:
    with pytest.raises(FlyCapture2NotConnectedError) as exc_info:
        raise_for_error(FC2ErrorCode.NOT_CONNECTED, description="camera missing", operation="fc2Connect")
    assert exc_info.value.code == FC2ErrorCode.NOT_CONNECTED
    assert "camera missing" in str(exc_info.value)


def test_raise_for_error_maps_invalid_parameter() -> None:
    with pytest.raises(FlyCapture2InvalidParameterError):
        raise_for_error(FC2ErrorCode.INVALID_PARAMETER, operation="fc2GetCameraFromIndex")


def test_build_error_message_contains_operation_and_code() -> None:
    message = build_error_message(code=FC2ErrorCode.TIMEOUT, description="timed out", operation="fc2RetrieveBuffer")
    assert "fc2RetrieveBuffer failed" in message
    assert "TIMEOUT" in message
