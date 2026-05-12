from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

from scripts import diagnose_frame_rate_property, hardware_capability_report, run_hardware_validation
from flycapture2_c.properties import CameraPropertyInfo, CameraPropertyValue, PropertyType
from flycapture2_c.pixel_format import PixelFormat


def test_capability_report_refuses_without_hardware_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(hardware_capability_report.ENV_HARDWARE_TEST, raising=False)

    with pytest.raises(SystemExit) as exc_info:
        hardware_capability_report.require_hardware_opt_in()

    assert hardware_capability_report.ENV_HARDWARE_TEST in str(exc_info.value)


def test_capability_report_serializes_fake_capability_record() -> None:
    record = {
        "schema_version": 1,
        "camera_index": 0,
        "capabilities": {
            "camera_info": hardware_capability_report.capability_ok(
                {
                    "model_name": "BFLY",
                    "serial_number": 123,
                    "mac_address": (1, 2, 3, 4, 5, 6),
                    "temperature_max": math.inf,
                }
            ),
            "unsupported_area": {
                "status": "unsupported",
                "error": {"type": "FlyCapture2NotSupportedError", "message": "not exported"},
            },
        },
        "errors": [],
    }

    payload = hardware_capability_report.normalize_json(record)
    text = json.dumps(payload, sort_keys=True)
    loaded = json.loads(text)

    assert loaded["capabilities"]["camera_info"]["status"] == "ok"
    assert loaded["capabilities"]["camera_info"]["value"]["mac_address"] == [1, 2, 3, 4, 5, 6]
    assert loaded["capabilities"]["camera_info"]["value"]["temperature_max"] is None
    assert loaded["capabilities"]["unsupported_area"]["status"] == "unsupported"


def test_capability_report_output_is_valid_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = {
        "schema_version": 1,
        "camera_index": 0,
        "capabilities": {"lifecycle": hardware_capability_report.capability_ok({"opened": True})},
        "errors": [],
    }
    output = tmp_path / "capability.json"

    hardware_capability_report.emit_report(report, output)

    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["capabilities"]["lifecycle"]["value"]["opened"] is True


def test_capability_report_pixel_format_bitfield_summary() -> None:
    summary = hardware_capability_report.pixel_format_summary_from_bitfield(
        int(PixelFormat.MONO8) | int(PixelFormat.RGB8)
    )

    assert summary["supported_by_camera"] == ["MONO8", "RGB8"]
    assert summary["read_frame_decodable"] == ["MONO8", "RGB8"]
    assert summary["raw_copy_only"] == []
    assert summary["unsupported_or_compressed"] == []

    composite_summary = hardware_capability_report.pixel_format_summary_from_bitfield(int(PixelFormat.BGR))
    assert composite_summary["supported_by_camera"] == ["BGR"]
    assert "MONO8" not in composite_summary["supported_by_camera"]
    assert composite_summary["raw_copy_only"] == ["BGR"]

    compressed_summary = hardware_capability_report.pixel_format_summary_from_bitfield(int(PixelFormat.YUV422_JPEG))
    assert "YUV411" not in compressed_summary["supported_by_camera"]
    assert "YUV422_JPEG" in compressed_summary["unsupported_or_compressed"]


class FakeFrameRateDiagnosticCamera:
    def __init__(self) -> None:
        self.info = CameraPropertyInfo(
            property_type=PropertyType.FRAME_RATE,
            present=True,
            auto_supported=True,
            manual_supported=True,
            on_off_supported=True,
            one_push_supported=False,
            abs_val_supported=True,
            read_out_supported=True,
            min_value=1,
            max_value=4095,
            abs_min=1.0,
            abs_max=75.47,
            units="frames per second",
            unit_abbr="fps",
        )
        self.value = CameraPropertyValue(
            property_type=PropertyType.FRAME_RATE,
            present=True,
            abs_control=False,
            one_push=False,
            on_off=True,
            auto_manual_mode=False,
            value_a=1811,
            value_b=0,
            abs_value=20.0,
        )

    def get_property_info(self, property_type):
        assert property_type == PropertyType.FRAME_RATE
        return self.info

    def get_property(self, property_type):
        assert property_type == PropertyType.FRAME_RATE
        return self.value

    def get_property_display_value(self, property_type):
        assert property_type == PropertyType.FRAME_RATE
        return 20.0


def test_frame_rate_property_diagnostic_reports_raw_and_display_fields() -> None:
    payload = diagnose_frame_rate_property.build_frame_rate_property_diagnostic(FakeFrameRateDiagnosticCamera())
    text = diagnose_frame_rate_property.format_diagnostic(payload)

    assert payload["property"] == "FRAME_RATE"
    assert payload["abs_val_supported"] is True
    assert payload["abs_control"] is False
    assert payload["value_a"] == 1811
    assert payload["abs_value"] == 20.0
    assert payload["display_value"] == 20.0
    assert payload["display_range"] == [1.0, 75.47]
    assert payload["readback_policy"] == "abs_value"
    assert "property: FRAME_RATE" in text
    assert "value_a: 1811" in text
    assert "abs_value: 20.0" in text


def test_hardware_validation_runner_builds_expected_readonly_commands() -> None:
    groups = run_hardware_validation.selected_groups(include_write=False)
    commands = [run_hardware_validation.build_pytest_command(group) for group in groups]

    assert groups[0].name == "readonly smoke"
    assert groups[-1].name == "GigE readonly"
    assert all("test_hardware_gige_write_reversible.py" not in command for command in commands)
    assert commands[0][:4] == [sys.executable, "-m", "pytest", "-q"]
    assert "tests/hardware/test_hardware_readonly_info.py" in commands[0]


def test_hardware_validation_runner_requires_write_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(run_hardware_validation.ENV_HARDWARE_TEST, "1")
    monkeypatch.delenv(run_hardware_validation.ENV_HARDWARE_WRITE_TEST, raising=False)

    with pytest.raises(SystemExit) as exc_info:
        run_hardware_validation.require_hardware_opt_in(include_write=True)

    assert run_hardware_validation.ENV_HARDWARE_WRITE_TEST in str(exc_info.value)


def test_hardware_validation_runner_forces_write_env_off_for_readonly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(run_hardware_validation.ENV_HARDWARE_TEST, "1")
    monkeypatch.setenv(run_hardware_validation.ENV_HARDWARE_WRITE_TEST, "1")
    readonly = run_hardware_validation.READONLY_GROUPS[0]
    write = run_hardware_validation.WRITE_GROUPS[0]

    readonly_env = run_hardware_validation.environment_for_group(readonly)
    write_env = run_hardware_validation.environment_for_group(write)

    assert readonly_env[run_hardware_validation.ENV_HARDWARE_TEST] == "1"
    assert readonly_env[run_hardware_validation.ENV_HARDWARE_WRITE_TEST] == "0"
    assert write_env[run_hardware_validation.ENV_HARDWARE_WRITE_TEST] == "1"


def test_hardware_validation_runner_includes_write_groups_only_when_requested() -> None:
    readonly_names = [group.name for group in run_hardware_validation.selected_groups(include_write=False)]
    all_names = [group.name for group in run_hardware_validation.selected_groups(include_write=True)]

    assert not any("write-gated" in name for name in readonly_names)
    assert any("write-gated" in name for name in all_names)
