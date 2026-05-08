from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENV_HARDWARE_TEST = "FLYCAPTURE2_HARDWARE_TEST"
ENV_HARDWARE_WRITE_TEST = "FLYCAPTURE2_HARDWARE_WRITE_TEST"


@dataclass(frozen=True)
class PytestGroup:
    name: str
    files: tuple[str, ...]
    write: bool = False


READONLY_GROUPS: tuple[PytestGroup, ...] = (
    PytestGroup("readonly smoke", ("tests/hardware/test_hardware_enumerate.py", "tests/hardware/test_hardware_readonly_info.py")),
    PytestGroup("grab-one / grab-sequence", ("tests/hardware/test_hardware_grab_one.py", "tests/hardware/test_hardware_grab_short_sequence.py")),
    PytestGroup("trigger readonly", ("tests/hardware/test_hardware_trigger_readonly.py",)),
    PytestGroup("Format7 readonly", ("tests/hardware/test_hardware_format7_readonly.py",)),
    PytestGroup("pixel format matrix readonly", ("tests/hardware/test_hardware_pixel_format_matrix.py",)),
    PytestGroup("property readonly", ("tests/hardware/test_hardware_properties_readonly.py",)),
    PytestGroup("metadata readonly", ("tests/hardware/test_hardware_metadata_readonly.py",)),
    PytestGroup("strobe/GPIO readonly", ("tests/hardware/test_hardware_strobe_gpio_readonly.py",)),
    PytestGroup("software trigger readonly/safe", ("tests/hardware/test_hardware_software_trigger.py",)),
    PytestGroup("GigE readonly", ("tests/hardware/test_hardware_gige_readonly.py",)),
)

WRITE_GROUPS: tuple[PytestGroup, ...] = (
    PytestGroup("config write-gated reversible", ("tests/hardware/test_hardware_config_write_reversible.py",), write=True),
    PytestGroup("trigger write-gated reversible", ("tests/hardware/test_hardware_trigger_write_reversible.py",), write=True),
    PytestGroup("Format7 write-gated reversible", ("tests/hardware/test_hardware_format7_write_reversible.py",), write=True),
    PytestGroup(
        "property write-gated reversible",
        (
            "tests/hardware/test_hardware_property_write_reversible.py",
            "tests/hardware/test_hardware_properties_write_reversible.py",
        ),
        write=True,
    ),
    PytestGroup("metadata write-gated reversible", ("tests/hardware/test_hardware_metadata_write_reversible.py",), write=True),
    PytestGroup("strobe/GPIO write-gated reversible", ("tests/hardware/test_hardware_strobe_gpio_write_reversible.py",), write=True),
    PytestGroup("software trigger write-gated", ("tests/hardware/test_hardware_software_trigger.py",), write=True),
    PytestGroup("GigE write-gated same-value", ("tests/hardware/test_hardware_gige_write_reversible.py",), write=True),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run opt-in FlyCapture2 hardware validation pytest groups.")
    parser.add_argument("--include-write", action="store_true", help=f"also run write-gated tests; requires {ENV_HARDWARE_WRITE_TEST}=1")
    parser.add_argument("--pytest-arg", action="append", default=[], help="extra argument passed through to pytest")
    return parser.parse_args(argv)


def require_hardware_opt_in(include_write: bool) -> None:
    if os.environ.get(ENV_HARDWARE_TEST) != "1":
        raise SystemExit(f"Refusing to touch hardware. Set {ENV_HARDWARE_TEST}=1 to enable validation.")
    if include_write and os.environ.get(ENV_HARDWARE_WRITE_TEST) != "1":
        raise SystemExit(f"--include-write requires {ENV_HARDWARE_WRITE_TEST}=1.")


def build_pytest_command(group: PytestGroup, *, extra_args: tuple[str, ...] = ()) -> list[str]:
    return [sys.executable, "-m", "pytest", "-q", *extra_args, *group.files]


def selected_groups(*, include_write: bool) -> tuple[PytestGroup, ...]:
    if include_write:
        return READONLY_GROUPS + WRITE_GROUPS
    return READONLY_GROUPS


def environment_for_group(group: PytestGroup) -> dict[str, str]:
    env = os.environ.copy()
    env[ENV_HARDWARE_TEST] = "1"
    if group.write:
        env[ENV_HARDWARE_WRITE_TEST] = "1"
    else:
        env[ENV_HARDWARE_WRITE_TEST] = "0"
    return env


def run_groups(groups: tuple[PytestGroup, ...], *, extra_args: tuple[str, ...] = ()) -> int:
    results: list[tuple[str, int]] = []
    for index, group in enumerate(groups, start=1):
        command = build_pytest_command(group, extra_args=extra_args)
        print(f"[{index}/{len(groups)}] {group.name}", flush=True)
        print(" ".join(command), flush=True)
        completed = subprocess.run(command, cwd=ROOT, env=environment_for_group(group))
        results.append((group.name, completed.returncode))
        if completed.returncode != 0:
            break

    print("Hardware validation summary:", flush=True)
    for name, returncode in results:
        status = "passed" if returncode == 0 else f"failed ({returncode})"
        print(f"- {name}: {status}", flush=True)
    return next((returncode for _name, returncode in results if returncode != 0), 0)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    require_hardware_opt_in(args.include_write)
    groups = selected_groups(include_write=args.include_write)
    return run_groups(groups, extra_args=tuple(args.pytest_arg))


if __name__ == "__main__":
    raise SystemExit(main())
