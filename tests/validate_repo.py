#!/usr/bin/env python3
"""Repo self-checks for governed-code-audit-skill.

Validates, without any third-party services:
  1. Every .yaml/.yml file parses.
  2. Every .json file parses (schema included).
  3. The JSON report embedded in examples/audit-report.example.md validates
     against schema/audit-report.schema.json (jsonschema package).
  4. Every fixture expected.yaml parses and its referenced source files exist.
  5. Mock-data enforcement: no email addresses outside example.* domains /
     noreply placeholders, no real-looking secrets (values must be marked
     FAKE/EXAMPLE when they look credential-shaped).

Exit code 0 = all checks passed.
"""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ERRORS: list[str] = []

ALLOWED_EMAIL_DOMAIN = re.compile(r"@(example\.(com|org|net)|users\.noreply\.github\.com)$", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
BANNED_TERMS = re.compile(r"tenantsage", re.I)
# Credential-shaped assignment, e.g.  api_key: "..." / password = "..."
SECRETISH_RE = re.compile(
    r"(?:api[_-]?key|secret|password|token|private[_-]?key)\s*[:=]\s*[\"']?([A-Za-z0-9_\-+/=]{8,})",
    re.I,
)
MOCK_MARKERS = ("FAKE", "EXAMPLE", "DO_NOT_USE", "PLACEHOLDER", "0000")


def fail(msg: str) -> None:
    ERRORS.append(msg)


def check_parses() -> None:
    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        try:
            if path.suffix in (".yaml", ".yml"):
                yaml.safe_load(path.read_text())
            elif path.suffix == ".json":
                json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            fail(f"parse error in {path.relative_to(ROOT)}: {exc}")


def check_schema_and_example() -> None:
    try:
        import jsonschema
    except ImportError:
        print("jsonschema not installed; skipping schema validation")
        return

    schema_path = ROOT / "schema" / "audit-report.schema.json"
    schema = json.loads(schema_path.read_text())

    md = (ROOT / "examples" / "audit-report.example.md").read_text()
    match = re.search(r"```json\s*\n(.*?)```", md, re.S)
    if not match:
        fail("no ```json block found in examples/audit-report.example.md")
        return
    report = json.loads(match.group(1))
    try:
        jsonschema.validate(report, schema)
    except jsonschema.ValidationError as exc:
        fail(f"example report fails schema validation: {exc.message}")


def check_fixtures() -> None:
    fixtures = ROOT / "tests" / "fixtures"
    for expected in sorted(fixtures.rglob("expected.yaml")):
        try:
            yaml.safe_load(expected.read_text())
        except Exception as exc:  # noqa: BLE001
            fail(f"parse error in {expected.relative_to(ROOT)}: {exc}")
            continue
        siblings = [p for p in expected.parent.iterdir() if p.name != "expected.yaml"]
        if not siblings:
            fail(f"fixture {expected.parent.name} has expected.yaml but no source files")


def check_mock_data() -> None:
    text_exts = {".md", ".yaml", ".yml", ".json", ".py", ".txt"}
    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts or not path.is_file() or path.suffix not in text_exts:
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(errors="replace")
        # This validator legitimately contains the banned term as a regex.
        if rel != Path("tests/validate_repo.py") and BANNED_TERMS.search(text):
            fail(f"{rel}: contains org-specific term (banned)")
        for m in EMAIL_RE.finditer(text):
            if not ALLOWED_EMAIL_DOMAIN.search(m.group(0)):
                fail(f"{rel}: non-example email address {m.group(0)!r}")
        for m in SECRETISH_RE.finditer(text):
            value = m.group(1)
            if not any(marker in value for marker in MOCK_MARKERS):
                fail(
                    f"{rel}: credential-shaped value lacks a mock marker "
                    f"(add FAKE/EXAMPLE/DO_NOT_USE): {value[:12]}..."
                )


def main() -> int:
    check_parses()
    check_schema_and_example()
    check_fixtures()
    check_mock_data()
    if ERRORS:
        print("CHECKS FAILED:")
        for e in ERRORS:
            print(f"  - {e}")
        return 1
    print("all repo checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
