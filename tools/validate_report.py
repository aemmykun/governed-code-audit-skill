#!/usr/bin/env python3
"""Validate an audit report against the governed-code-audit contract.

For hosts integrating the skill: run this on a report returned by an agent
before acting on it. It checks the JSON Schema AND the semantic invariants
that the schema alone cannot express (scope resolution, fail-closed status,
snapshot binding, honest provenance).

Usage:
    python tools/validate_report.py report.json
    python tools/validate_report.py report.json --snapshot-dir ./snapshot
    python tools/validate_report.py report.json --expect-commit abc123...

Options:
    --snapshot-dir DIR   verify each provenance input_digest against the
                         bytes at DIR/<path>
    --expect-commit SHA  require report["source"]["commit_sha"] == SHA
                         (binds the report to the commit the host measured,
                         not one the agent claims)

Exit code 0 = contract satisfied. Non-zero with one line per violation.
This validates structure and invariants — it does not evaluate whether the
agent audited well.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "audit-report.schema.json"


def check(report: dict, errors: list) -> None:
    """Semantic invariants; schema validation happens in main()."""
    scope = report["scope"]
    requested, assessed, blocked = (
        set(scope[k]) for k in ("requested", "assessed", "blocked")
    )
    if not assessed.isdisjoint(blocked):
        errors.append("assessed and blocked scopes must be disjoint")
    if requested != assessed | blocked:
        errors.append("requested scopes must equal assessed ∪ blocked")
    if report["audit_status"] == "complete" and (
        blocked or report["missing_context"]
    ):
        errors.append("status 'complete' but blocked scopes or missing context exist")
    if report["audit_status"] == "incomplete" and not blocked:
        errors.append("status 'incomplete' but no scope is marked blocked")
    if report["audit_status"] == "rejected":
        if assessed or report["findings"]:
            errors.append("status 'rejected' but report contains assessed scopes/findings")
        if report["overall_risk"] != "unknown":
            errors.append("status 'rejected' but overall_risk is not 'unknown'")
    for f in report["findings"]:
        if f["category"] not in assessed:
            errors.append(f"finding {f['id']}: category '{f['category']}' was not assessed")
        ev = f["evidence"]
        if ev["line_end"] < ev["line_start"]:
            errors.append(f"finding {f['id']}: evidence line_end < line_start")
        if ev["snapshot_id"] != report["source"]["snapshot_id"]:
            errors.append(f"finding {f['id']}: evidence snapshot_id does not match report source")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--snapshot-dir")
    ap.add_argument("--expect-commit")
    args = ap.parse_args()

    errors: list = []
    report = json.loads(Path(args.report).read_text())

    try:
        import jsonschema
    except ImportError:
        print("jsonschema is required: pip install jsonschema", file=sys.stderr)
        return 2

    schema = json.loads(SCHEMA_PATH.read_text())
    for e in jsonschema.Draft202012Validator(schema).iter_errors(report):
        errors.append(f"schema: {e.message}")
    if not errors:
        check(report, errors)

    if args.expect_commit and report["source"].get("commit_sha") != args.expect_commit:
        errors.append(
            f"source.commit_sha '{report['source'].get('commit_sha')}' "
            f"does not match expected '{args.expect_commit}'"
        )

    if args.snapshot_dir:
        base = Path(args.snapshot_dir)
        for item in report["provenance"]["input_digests"]:
            target = base / item["path"]
            if not target.is_file():
                errors.append(f"input digest: '{item['path']}' not found in snapshot dir")
                continue
            if hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
                errors.append(f"input digest mismatch for '{item['path']}'")

    if errors:
        for e in errors:
            print(f"INVALID: {e}")
        return 1
    print("report satisfies schema and contract invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
