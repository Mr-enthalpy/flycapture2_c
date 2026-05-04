from __future__ import annotations

import os

import pytest

from flycapture2_c._hardware_tools import ENV_HARDWARE_TEST, ENV_HARDWARE_WRITE_TEST, HardwareSmokeConfig


@pytest.fixture
def hardware_config() -> HardwareSmokeConfig:
    return HardwareSmokeConfig.from_env()


@pytest.fixture
def hardware_guard() -> None:
    if os.environ.get(ENV_HARDWARE_TEST) != "1":
        pytest.skip("hardware tests are opt-in; set FLYCAPTURE2_HARDWARE_TEST=1")


@pytest.fixture
def hardware_write_guard(hardware_guard) -> None:
    if os.environ.get(ENV_HARDWARE_WRITE_TEST) != "1":
        pytest.skip("hardware property-write tests require FLYCAPTURE2_HARDWARE_WRITE_TEST=1")
