from __future__ import annotations

import re
from pathlib import Path

import flycapture2_c


def test_all_top_level_exports_are_classified_in_public_api_doc() -> None:
    root = Path(__file__).resolve().parents[1]
    public_api = (root / "docs" / "public_api.md").read_text(encoding="utf-8")
    documented_exports = set(re.findall(r"^- `([^`]+)`", public_api, re.MULTILINE))

    missing = sorted(set(flycapture2_c.__all__) - documented_exports)

    assert missing == []

