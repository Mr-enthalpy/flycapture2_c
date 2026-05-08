from __future__ import annotations

import pytest

from scripts import measure_capture_rate

pytestmark = pytest.mark.hardware


def test_hardware_capture_rate_baseline(hardware_guard, hardware_config) -> None:
    report, returncode = measure_capture_rate.build_report(
        measure_capture_rate.parse_args(
            [
                "--camera-index",
                str(hardware_config.camera_index),
                "--duration",
                "2",
                "--warmup",
                "1",
            ]
        )
    )

    assert returncode == 0
    assert report["restore_failed"] is False
    assert report["results"]
    result = report["results"][0]
    if result["status"] == "skipped":
        pytest.skip(result["error"]["message"])
    assert result["status"] == "ok"
    assert result["frames"] > 0
    assert result["actual_wall_clock_fps"] > 0
    assert result["frame_shape"]
    assert result["dtype"] in {"uint8", "uint16"}
    assert result["pixel_format"] in {"MONO8", "MONO16", "RAW8", "RAW16"}


def test_hardware_capture_rate_matrix_write_gated(hardware_write_guard, hardware_config) -> None:
    report, returncode = measure_capture_rate.build_report(
        measure_capture_rate.parse_args(
            [
                "--camera-index",
                str(hardware_config.camera_index),
                "--fps",
                "5",
                "10",
                "--duration",
                "2",
                "--warmup",
                "1",
            ]
        )
    )

    assert returncode == 0
    assert report["restore_failed"] is False
    assert len(report["results"]) == 2
    for result in report["results"]:
        if result["status"] == "skipped":
            assert result["unsupported"] is True
            continue
        assert result["status"] == "ok"
        assert result["frames"] > 0
        assert result["actual_readback_ratio"] is not None
