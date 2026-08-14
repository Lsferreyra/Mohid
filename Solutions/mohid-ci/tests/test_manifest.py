#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


CI_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CI_DIR.parents[1]
MANIFEST = CI_DIR / "cmake" / "MohidWaterSources.cmake"


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
    if relative_paths[-1] != "Software/MOHIDWater/Main.F90":
        print("Main.F90 must be the final manifest entry", file=sys.stderr)
        return 1

    if duplicates or missing:
        return 1

    print(f"Validated {len(relative_paths)} MOHID Water source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
