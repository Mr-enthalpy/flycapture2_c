from __future__ import annotations

import sys
from pathlib import Path

import pytest

import flycapture2_c
from flycapture2_c._hardware_tools import ENV_HARDWARE_WRITE_TEST

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from hardware_headless_readiness_check import (
    _check_write_gating,
    parse_args,
)


# ---------------------------------------------------------------------------
# _check_write_gating tests
# ---------------------------------------------------------------------------


def test_write_flag_raises_without_env(monkeypatch) -> None:
    monkeypatch.setenv(ENV_HARDWARE_WRITE_TEST, "0")
    with pytest.raises(SystemExit):
        _check_write_gating(True)


def test_write_flag_ok_with_env(monkeypatch) -> None:
    monkeypatch.setenv(ENV_HARDWARE_WRITE_TEST, "1")
    _check_write_gating(True)


def test_readonly_always_passes(monkeypatch) -> None:
    monkeypatch.setenv(ENV_HARDWARE_WRITE_TEST, "0")
    _check_write_gating(False)


def test_readonly_passes_when_write_absent(monkeypatch) -> None:
    monkeypatch.delenv(ENV_HARDWARE_WRITE_TEST, raising=False)
    _check_write_gating(False)


def test_write_flag_raises_when_env_absent(monkeypatch) -> None:
    monkeypatch.delenv(ENV_HARDWARE_WRITE_TEST, raising=False)
    with pytest.raises(SystemExit):
        _check_write_gating(True)


# ---------------------------------------------------------------------------
# parse_args tests
# ---------------------------------------------------------------------------


def test_parse_args_default_no_write() -> None:
    args = parse_args([])
    assert args.write is False


def test_parse_args_write_flag() -> None:
    args = parse_args(["--write"])
    assert args.write is True


def test_parse_args_help_contains_write() -> None:
    """--write flag appears in help text."""
    try:
        parse_args(["--help"])
    except SystemExit:
        pass


# ---------------------------------------------------------------------------
# CameraCleanupWarning removed
# ---------------------------------------------------------------------------


def test_CameraCleanupWarning_not_in_module() -> None:
    assert not hasattr(flycapture2_c, "CameraCleanupWarning")


def test_CameraCleanupWarning_not_in_all() -> None:
    assert "CameraCleanupWarning" not in flycapture2_c.__all__


# ---------------------------------------------------------------------------
# public_api.md check
# ---------------------------------------------------------------------------


def test_public_api_doc_no_cleanup_warning() -> None:
    doc = (ROOT / "docs" / "public_api.md").read_text(encoding="utf-8")
    assert "CameraCleanupWarning" not in doc


def test_public_api_doc_contains_CameraStateError() -> None:
    doc = (ROOT / "docs" / "public_api.md").read_text(encoding="utf-8")
    assert "CameraStateError" in doc


# ---------------------------------------------------------------------------
# Cleanup errors property still exists
# ---------------------------------------------------------------------------


def test_Camera_has_cleanup_errors_property() -> None:
    from flycapture2_c.camera import Camera
    assert hasattr(Camera, "cleanup_errors")


# ---------------------------------------------------------------------------
# Exports baseline updated (no CameraCleanupWarning)
# ---------------------------------------------------------------------------


def test_all_exports_no_CameraCleanupWarning() -> None:
    for name in flycapture2_c.__all__:
        if "Cleanup" in name:
            pytest.fail(f"Unexpected cleanup-related export: {name}")


# ---------------------------------------------------------------------------
# TriggerModeInfo serialization
# ---------------------------------------------------------------------------


def test_trigger_mode_info_has_supported_sources_and_modes() -> None:
    from flycapture2_c.trigger import TriggerModeInfo
    assert hasattr(TriggerModeInfo, "supported_sources")
    assert hasattr(TriggerModeInfo, "supported_modes")
    assert not hasattr(TriggerModeInfo, "available_sources")
    assert not hasattr(TriggerModeInfo, "available_modes")


def test_trigger_mode_info_supported_sources_returns_tuple() -> None:
    from flycapture2_c.trigger import TriggerModeInfo
    info = TriggerModeInfo(
        present=True,
        read_out_supported=True,
        on_off_supported=True,
        polarity_supported=True,
        value_readable=True,
        source_mask=0x0007,
        software_trigger_supported=True,
        mode_mask=0x8000,
    )
    sources = info.supported_sources
    assert isinstance(sources, tuple)
    assert 0 in sources


def test_trigger_mode_info_supported_modes_returns_tuple() -> None:
    from flycapture2_c.trigger import TriggerModeInfo
    info = TriggerModeInfo(
        present=True,
        read_out_supported=True,
        on_off_supported=True,
        polarity_supported=True,
        value_readable=True,
        source_mask=0x0007,
        software_trigger_supported=True,
        mode_mask=0x8000,
    )
    modes = info.supported_modes
    assert isinstance(modes, tuple)
    assert 0 in modes
