#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


CI_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CI_DIR.parents[1]
MANIFEST = CI_DIR / "cmake" / "MohidWaterSources.cmake"
IFX_DOCKERFILE = CI_DIR / "containers" / "Dockerfile.ifx"
SMOKE_SCRIPT = CI_DIR / "scripts" / "smoke-in-container.sh"
HDF5_MODULES = (
    REPO_ROOT / "Software" / "MOHIDBase1" / "ModuleHDF5.F90",
    REPO_ROOT / "Software" / "MOHIDBase1" / "ModuleHDF5_OO.F90",
)


def validate_hdf5_interfaces() -> list[str]:
    errors: list[str] = []
    hid_t_misuse = re.compile(
        r"integer\s*\(\s*HID_T\s*\).*::.*\b"
        r"(STAT_CALL|STAT_|Rank|rank_|rank_out|class_id|GroupType|"
        r"nmembers|nItems|HDF5ID|Array[123]D|iArray[123]D)\b",
        re.IGNORECASE,
    )
    hid_t_count_function = re.compile(
        r"integer\s*\(\s*HID_T\s*\)\s+function\s+"
        r"GetHDF5GroupNumberOfItems\b",
        re.IGNORECASE,
    )

    for path in HDF5_MODULES:
        text = path.read_text(encoding="latin-1")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("!"):
                continue
            if hid_t_misuse.search(line) or hid_t_count_function.search(line):
                errors.append(f"{path.relative_to(REPO_ROOT)}:{line_number}: {line.strip()}")

    return errors


def validate_ifx_environment() -> list[str]:
    text = IFX_DOCKERFILE.read_text(encoding="utf-8")
    if text.count("source /opt/intel/oneapi/setvars.sh --force") != 2:
        return ["Dockerfile.ifx must force both oneAPI setvars initializations"]
    return []


def validate_serial_tree_normalization() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="mohid-smoke-test.") as temporary:
        root = Path(temporary)
        input_dir = root / "input"
        exe_dir = input_dir / "exe"
        results_dir = root / "results"
        executable = root / "mohid-stub.sh"
        exe_dir.mkdir(parents=True)

        (exe_dir / "nomfich.dat").write_text("stub\n", encoding="utf-8")
        tree_file = exe_dir / "tree.dat"
        original_tree = "MOHID configuration\nGenerated test\n+../exe : 1\n"
        tree_file.write_text(original_tree, encoding="utf-8")
        executable.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "grep -Fqx '+../exe' tree.dat\n"
            "echo 'Program Mohid Water successfully terminated'\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)

        environment = os.environ.copy()
        environment.update(
            {
                "MOHID_INPUT_DIR": str(input_dir),
                "MOHID_RESULTS_DIR": str(results_dir),
                "MOHID_EXECUTABLE": str(executable),
                "MOHID_TIMEOUT_SECONDS": "10",
            }
        )
        completed = subprocess.run(
            ["bash", str(SMOKE_SCRIPT)],
            check=False,
            capture_output=True,
            env=environment,
            text=True,
        )

        errors: list[str] = []
        if completed.returncode != 0:
            errors.append(
                "serial smoke normalization test failed: "
                f"{completed.stdout}{completed.stderr}"
            )
        if tree_file.read_text(encoding="utf-8") != original_tree:
            errors.append("smoke runner modified the source case")
        status_file = results_dir / "status.txt"
        if not status_file.is_file():
            errors.append("smoke runner did not create status.txt")
        elif "tree_mode=single-domain-normalized" not in status_file.read_text(
            encoding="utf-8"
        ):
            errors.append("smoke runner did not record tree normalization")
        return errors


def main() -> int:
    text = MANIFEST.read_text(encoding="utf-8")
    relative_paths = re.findall(r'\$\{MOHID_ROOT\}/([^"\n]+)', text)

    if not relative_paths:
        print("No sources found in CMake manifest", file=sys.stderr)
        return 1

    duplicates = [path for path, count in Counter(relative_paths).items() if count > 1]
    missing = [path for path in relative_paths if not (REPO_ROOT / path).is_file()]

    if duplicates:
        print(f"Duplicate sources: {duplicates}", file=sys.stderr)
    if missing:
        print(f"Missing sources: {missing}", file=sys.stderr)
    errors: list[str] = []
    if relative_paths[-1] != "Software/MOHIDWater/Main.F90":
        errors.append("Main.F90 must be the final manifest entry")

    errors.extend(validate_hdf5_interfaces())
    errors.extend(validate_ifx_environment())
    errors.extend(validate_serial_tree_normalization())

    if errors:
        print("\n".join(errors), file=sys.stderr)

    if duplicates or missing or errors:
        return 1

    print(
        f"Validated {len(relative_paths)} MOHID Water source files, "
        "HDF5 declarations, oneAPI setup, and serial smoke normalization"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
