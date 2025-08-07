#!/usr/bin/env python3
"""Run_Test_scripts.py

Executes the project test-suite using *pytest* and produces a concise
human-readable QA report (``QA_Report.txt``) based on the JSON data emitted by
*pytest-json-report*.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent  # unit_tests directory
PROJECT_ROOT = ROOT_DIR.parent
JSON_REPORT_FILE = ROOT_DIR / "qa_report.json"
OUTPUT_QA_REPORT = ROOT_DIR / "QA_Report.txt"


def _run_pytest() -> int:
    """Run pytest and return the process exit status."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--json-report",
        f"--json-report-file={JSON_REPORT_FILE}",
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{PROJECT_ROOT}{os.pathsep}" + env.get("PYTHONPATH", "")
    env.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

    completed = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env)
    return completed.returncode


def _determine_test_type(filepath: str) -> str:
    lower = filepath.lower()
    if any(key in lower for key in {"integration", "integrate"}):
        return "integration"
    if "ai" in lower:
        return "AI"
    if "data" in lower:
        return "data"
    return "unit"


def _generate_report(data: Dict[str, Any]) -> None:
    lines: list[str] = []
    now = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines.append("IntelliShop Automated QA Test Report")
    lines.append("=" * 45)
    lines.append(f"Generated on: {now}\n")

    tests = data.get("tests", [])
    summary = data.get("summary", {})
    outcome_totals = summary.get("outcome_totals", {})

    for test in tests:
        nodeid = test.get("nodeid", "<unknown>")
        outcome = test.get("outcome", "<unknown>").upper()
        filepath, *rest = nodeid.split("::")
        test_name = "::".join(rest) if rest else "<module>"
        duration = test.get("duration", 0.0)

        lines.append(f"Test File : {filepath}")
        lines.append(f"Test Name : {test_name}")
        lines.append(f"Outcome   : {outcome}")
        lines.append(f"Duration  : {duration:.2f}s")
        lines.append(f"Type      : {_determine_test_type(filepath)}\n")

    lines.append("\nOverall Summary")
    lines.append("-" * 15)
    total_tests = summary.get("total", 0)
    for outc, count in outcome_totals.items():
        lines.append(f"{outc.capitalize():10}: {count}")
    lines.append(f"Total Tests : {total_tests}")

    OUTPUT_QA_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"QA report generated → {OUTPUT_QA_REPORT.relative_to(ROOT_DIR)}")


def main() -> None:
    status = _run_pytest()

    if not JSON_REPORT_FILE.exists():
        print("❌ Pytest did not generate a JSON report – aborting.")
        sys.exit(status or 1)

    with JSON_REPORT_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    _generate_report(data)
    sys.exit(status)


if __name__ == "__main__":
    main() 