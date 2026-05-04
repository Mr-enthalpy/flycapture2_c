from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from flycapture2_c.hardware_report import HardwareReport, HardwareReportError, format_human_report
from flycapture2_c.image import ImageFrame
from flycapture2_c.pixel_format import PixelFormat
from flycapture2_c._hardware_tools import frame_summary_from_frame, frame_summary_to_dict


def test_hardware_report_is_json_serializable(tmp_path: Path) -> None:
    report = HardwareReport(
        sdk_root="C:/sdk",
        dll_path="C:/sdk/bin/FlyCapture2_C_v140.dll",
        python_version="3.13.5",
        platform="Windows-11",
        camera_index=0,
        camera_info={"model_name": "BFLY", "serial_number": 123},
        video_mode=22,
        frame_rate=4,
        property_summary=[{"property_type": "GAIN", "present": True}],
        capture_summary={"shape": [2, 2], "dtype": "uint8"},
        errors=[HardwareReportError(category="NO_CAMERA", message="none")],
        started_at="2026-05-05T00:00:00+00:00",
        finished_at="2026-05-05T00:00:01+00:00",
        duration_s=1.0,
    )
    path = report.save_json_report(tmp_path / "report.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["sdk_root"] == "C:/sdk"
    assert loaded["errors"][0]["category"] == "NO_CAMERA"


def test_human_report_formatter_contains_fixed_sections() -> None:
    report = HardwareReport(
        started_at="2026-05-05T00:00:00+00:00",
        finished_at="2026-05-05T00:00:01+00:00",
        duration_s=1.0,
    )
    text = format_human_report(report)
    for section in (
        "[SDK]",
        "[Camera]",
        "[Video]",
        "[Properties]",
        "[Capture]",
        "[Sequence]",
        "[WriteProperty]",
        "[Errors]",
    ):
        assert section in text


def test_mock_frame_summary_computes_stats_and_warnings() -> None:
    array = np.array([[0, 1], [2, 3]], dtype=np.uint8).copy()
    frame = ImageFrame(
        array=array,
        width=2,
        height=2,
        stride=2,
        pixel_format=PixelFormat.MONO8,
        timestamp=None,
    )
    summary = frame_summary_from_frame(frame, elapsed_ms=1.5)
    payload = frame_summary_to_dict(summary)
    assert payload["min"] == 0.0
    assert payload["max"] == 3.0
    assert payload["mean"] == 1.5
    assert round(payload["std"], 6) == round(float(array.std()), 6)
    assert payload["finite"] is True
