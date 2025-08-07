#!/usr/bin/env python3
"""Test_scripts.py

This helper script performs the following steps:
1. Ensures that all Python dependencies required to execute the test-suite are
   installed (requirements.txt + pytest & pytest-json-report).
2. Recursively discovers test files across the Intelli-Shop repository using
   the conventional patterns ``test_*.py`` and ``*_test.py`` (skipping the
   ``venv`` directories).
3. Saves the discovered list into *discovered_tests.json* for downstream
   consumption.
4. Prints a concise summary so the calling shell script can show feedback to
   the user.

The script is intentionally idempotent – running it multiple times will not
re-install already existing packages and will simply refresh the file list.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _run(cmd: List[str]) -> None:
    """Run *cmd* via *subprocess* while inheriting the current stdio."""
    subprocess.run(cmd, check=False)


def ensure_dependencies() -> None:
    """Install project and test-runner dependencies if they are missing."""
    req_file = ROOT_DIR.parent / "requirements.txt"  # Look in project root

    # Upgrade pip to latest (non-critical if it fails)
    _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

    # Install the main project requirements if available
    if req_file.is_file():
        _run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])

    # Always ensure pytest and json reporter are present for the test run
    _run([sys.executable, "-m", "pip", "install", "pytest", "pytest-json-report"])


def discover_tests() -> List[str]:
    """Return a de-duplicated, sorted list of test files found in project."""
    patterns = ("test_*.py", "*_test.py")
    test_files: set[str] = set()

    project_root = ROOT_DIR.parent

    for pattern in patterns:
        for path in project_root.rglob(pattern):
            # Skip virtual-environment & cached files
            if any(part.startswith("venv") for part in path.parts):
                continue
            if path.name.startswith(".__") or "__pycache__" in path.parts:
                continue
            if path.is_file():
                test_files.add(str(path.relative_to(project_root)))

    return sorted(test_files)


def main() -> None:
    ensure_dependencies()

    tests = discover_tests()
    out_file = ROOT_DIR / "discovered_tests.json"
    out_file.write_text(json.dumps({"tests": tests}, indent=2), encoding="utf-8")

    print(f"Discovered {len(tests)} test file(s). List saved to {out_file}.")

    # Exit with non-zero if no tests were found so the caller can act
    sys.exit(0 if tests else 1)


if __name__ == "__main__":
    main() 