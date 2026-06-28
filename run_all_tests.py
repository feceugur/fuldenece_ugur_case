#!/usr/bin/env python3
"""
Single-command test runner for all three assignment tasks.

Runs UI tests, API tests, and the load test back to back, then produces one
consolidated report (terminal output + reports/SUMMARY.md + reports/summary.csv)
that distinguishes "known site/API bug, already documented" failures from
genuinely unexpected failures (broken selector, environment issue, etc.).

Usage:
    python run_all_tests.py                  # full run (load test = 60s)
    python run_all_tests.py --skip-load       # UI + API only, fast
    python run_all_tests.py --load-duration 30s

Setup is just `pip install -r requirements.txt` — no virtualenv creation is
required, and the Playwright browser binary (which pip alone cannot install)
is downloaded automatically on first run, below.

No extra dependencies beyond requirements.txt — report parsing uses only the
standard library (xml.etree, ast, csv).
"""
import argparse
import ast
import csv
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Use "python -m <tool>" instead of a hardcoded .venv/bin path so this works
# whether or not the user created a virtualenv at all.
PYTEST_CMD = [sys.executable, "-m", "pytest"]
LOCUST_CMD = [sys.executable, "-m", "locust"]
REPORTS_DIR = ROOT / "reports"


def ensure_playwright_browser():
    """`pip install` only gets the Playwright Python package — the actual
    browser binary still needs a separate download. Running this every time
    is cheap: Playwright checks what's already installed and skips it."""
    print(f"\n{'=' * 70}\n  Setup — ensuring Playwright's Chromium is installed\n{'=' * 70}")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], cwd=ROOT)


def run(cmd: list[str], label: str) -> int:
    print(f"\n{'=' * 70}\n  {label}\n{'=' * 70}")
    print(f"$ {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def functions_with_bug_docstring(py_file: Path) -> set[str]:
    """Returns test function names whose docstring/body mentions 'BUG:' —
    used to tell "this failure documents a known site/API defect" apart
    from "something actually broke" without hand-maintaining a list."""
    tree = ast.parse(py_file.read_text())
    flagged = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            src = ast.get_source_segment(py_file.read_text(), node) or ""
            if "BUG:" in src:
                flagged.add(node.name)
    return flagged


def bug_tagged_scenarios(step_defs_dir: Path) -> set[str]:
    """UI tests are pytest-bdd scenarios; the Gherkin `@bug` tag becomes a
    pytest marker. Ask pytest directly which test IDs that marker selects,
    instead of hand-maintaining a parallel list that can drift."""
    result = subprocess.run(
        [*PYTEST_CMD, str(step_defs_dir), "-m", "bug", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    names = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" in line:
            names.add(line.split("::")[-1])
    return names


def parse_junit(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {"total": 0, "passed": 0, "failed": [], "errors": [], "skipped": 0}
    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    failed, errors = [], []
    for tc in suite.findall("testcase"):
        name = tc.get("name")
        if tc.find("failure") is not None:
            failed.append(name)
        elif tc.find("error") is not None:
            errors.append(name)
    return {
        "total": int(suite.get("tests", 0)),
        "passed": int(suite.get("tests", 0)) - len(failed) - len(errors)
                  - int(suite.get("skipped", 0)),
        "failed": failed,
        "errors": errors,
        "skipped": int(suite.get("skipped", 0)),
    }


def run_ui_tests() -> dict:
    REPORTS_DIR.mkdir(exist_ok=True)
    rc = run([
        *PYTEST_CMD, "ui_tests/step_defs/", "-v",
        f"--junitxml={REPORTS_DIR / 'ui_results.xml'}",
        f"--html={REPORTS_DIR / 'ui_report.html'}", "--self-contained-html",
    ], "TASK 1 — UI Tests")
    stats = parse_junit(REPORTS_DIR / "ui_results.xml")
    known_bugs = bug_tagged_scenarios(ROOT / "ui_tests" / "step_defs")
    stats["known_bug_failures"] = [f for f in stats["failed"] if f in known_bugs]
    stats["unexpected_failures"] = [f for f in stats["failed"] if f not in known_bugs]
    stats["returncode"] = rc
    return stats


def run_api_tests() -> dict:
    REPORTS_DIR.mkdir(exist_ok=True)
    rc = run([
        *PYTEST_CMD, "api_tests/", "-v",
        f"--junitxml={REPORTS_DIR / 'api_results.xml'}",
        f"--html={REPORTS_DIR / 'api_report.html'}", "--self-contained-html",
    ], "TASK 3 — API Tests (petstore.swagger.io)")
    stats = parse_junit(REPORTS_DIR / "api_results.xml")
    known_bugs = functions_with_bug_docstring(ROOT / "api_tests" / "test_petstore.py")
    stats["known_bug_failures"] = [f for f in stats["failed"] if f in known_bugs]
    stats["unexpected_failures"] = [f for f in stats["failed"] if f not in known_bugs]
    stats["returncode"] = rc
    return stats


def run_load_test(duration: str) -> dict:
    REPORTS_DIR.mkdir(exist_ok=True)
    csv_prefix = REPORTS_DIR / "load"
    rc = run([
        *LOCUST_CMD, "-f", "load_tests/locustfile.py", "--headless",
        "-u", "1", "-r", "1", "--run-time", duration,
        "--host", "https://www.n11.com",
        "--csv", str(csv_prefix), "--html", str(REPORTS_DIR / "load_report.html"),
    ], f"TASK 2 — Load Test (n11.com search, {duration})")

    stats_file = Path(f"{csv_prefix}_stats.csv")
    failures_file = Path(f"{csv_prefix}_failures.csv")
    requests_total, failures_total = 0, 0
    if stats_file.exists():
        with open(stats_file) as f:
            for row in csv.DictReader(f):
                if row["Name"] == "Aggregated":
                    requests_total = int(row["Request Count"])
                    failures_total = int(row["Failure Count"])
    failure_messages = []
    if failures_file.exists():
        with open(failures_file) as f:
            for row in csv.DictReader(f):
                failure_messages.append(f"{row['Name']}: {row['Error']} (x{row['Occurrences']})")
    return {
        "requests_total": requests_total,
        "failures_total": failures_total,
        "failure_messages": failure_messages,
        "returncode": rc,
    }


def print_section(title: str):
    print(f"\n{title}\n{'-' * len(title)}")


def write_summary(ui: dict, api: dict, load: dict, duration: str):
    lines_md = [
        f"# Test Run Summary — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "",
        "## Task 1 — UI Tests",
        f"- Total: {ui['total']} | Passed: {ui['passed']} | Skipped: {ui['skipped']}",
        f"- Bugs found by this suite: {len(ui['known_bug_failures'])} — {', '.join(ui['known_bug_failures']) or 'none'}",
        f"- **Unexpected failures: {len(ui['unexpected_failures'])}** — {', '.join(ui['unexpected_failures']) or 'none'}",
        "",
        "## Task 2 — Load Test",
        f"- Requests: {load['requests_total']} | Failures: {load['failures_total']}",
        "- Failure messages (these ARE the findings, not bugs in the test):",
    ]
    lines_md += [f"  - {m}" for m in load["failure_messages"]] or ["  - none"]
    lines_md += [
        "",
        "## Task 3 — API Tests",
        f"- Total: {api['total']} | Passed: {api['passed']} | Skipped: {api['skipped']}",
        f"- Bugs found by this suite: {len(api['known_bug_failures'])} — {', '.join(api['known_bug_failures']) or 'none'}",
        f"- **Unexpected failures: {len(api['unexpected_failures'])}** — {', '.join(api['unexpected_failures']) or 'none'}",
        "",
        "## Reports",
        "- reports/ui_report.html, reports/api_report.html, reports/load_report.html",
        "- reports/*_results.xml (JUnit), reports/load_stats.csv, reports/load_failures.csv",
    ]
    (REPORTS_DIR / "SUMMARY.md").write_text("\n".join(lines_md) + "\n")

    with open(REPORTS_DIR / "summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task", "total", "passed", "known_bug_failures", "unexpected_failures"])
        writer.writerow(["ui_tests", ui["total"], ui["passed"], len(ui["known_bug_failures"]), len(ui["unexpected_failures"])])
        writer.writerow(["api_tests", api["total"], api["passed"], len(api["known_bug_failures"]), len(api["unexpected_failures"])])
        writer.writerow(["load_test", load["requests_total"], load["requests_total"] - load["failures_total"], "n/a", load["failures_total"]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-load", action="store_true", help="Skip the load test (UI + API only)")
    parser.add_argument("--load-duration", default="60s", help="Locust --run-time (default: 60s)")
    args = parser.parse_args()

    ensure_playwright_browser()

    ui = run_ui_tests()
    api = run_api_tests()
    load = {"requests_total": 0, "failures_total": 0, "failure_messages": [], "returncode": 0}
    if not args.skip_load:
        load = run_load_test(args.load_duration)

    write_summary(ui, api, load, args.load_duration)

    print(f"\n{'=' * 70}\n  FINAL SUMMARY\n{'=' * 70}")

    print_section("Task 1 — UI Tests")
    print(f"  Total: {ui['total']}  Passed: {ui['passed']}  Skipped: {ui['skipped']}")
    print(f"  Bugs found by this suite ({len(ui['known_bug_failures'])}): {', '.join(ui['known_bug_failures']) or '-'}")
    print(f"  Unexpected failures ({len(ui['unexpected_failures'])}): {', '.join(ui['unexpected_failures']) or '-'}")

    if not args.skip_load:
        print_section("Task 2 — Load Test")
        print(f"  Requests: {load['requests_total']}  Failures: {load['failures_total']}")
        for m in load["failure_messages"]:
            print(f"    - {m}")

    print_section("Task 3 — API Tests")
    print(f"  Total: {api['total']}  Passed: {api['passed']}  Skipped: {api['skipped']}")
    print(f"  Bugs found by this suite ({len(api['known_bug_failures'])}): {', '.join(api['known_bug_failures']) or '-'}")
    print(f"  Unexpected failures ({len(api['unexpected_failures'])}): {', '.join(api['unexpected_failures']) or '-'}")

    print(f"\nFull reports written to: {REPORTS_DIR}/")
    print(f"  - {REPORTS_DIR}/SUMMARY.md   (this summary)")
    print(f"  - {REPORTS_DIR}/summary.csv  (machine-readable)")
    print(f"  - {REPORTS_DIR}/ui_report.html, api_report.html, load_report.html")

    unexpected_total = len(ui["unexpected_failures"]) + len(api["unexpected_failures"])
    if unexpected_total > 0:
        print(f"\n{unexpected_total} UNEXPECTED failure(s) found — see above. Exiting with status 1.")
        sys.exit(1)
    print("\nAll failures are bugs this suite found and documented (not unexpected breakage). Exiting with status 0.")
    sys.exit(0)


if __name__ == "__main__":
    main()
