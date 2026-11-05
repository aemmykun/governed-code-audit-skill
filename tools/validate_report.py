#!/usr/bin/env python3
"""Validate an audit report against the governed-code-audit contract.

For hosts integrating the skill: run this on a report returned by an agent
before acting on it. It checks the JSON Schema AND the semantic invariants
the schema alone cannot express (scope resolution, fail-closed status,
snapshot binding, honest provenance).

Usage:
    python tools/validate_report.py report.json
    python tools/validate_report.py report.json --request locked-request.yaml
    python tools/validate_report.py report.json --requested-scopes security
    python tools/validate_report.py report.json --expect-commit abc123...
    python tools/validate_report.py report.json --snapshot-dir ./snapshot

Options:
    --request FILE           the LOCKED audit request the host issued (YAML or
                             JSON, see schema/audit-request.schema.json).
                             Binds commit_sha, requested scopes, snapshot
                             digest and audit_id in one host-owned file —
                             the strongest form of request binding.
    --requested-scopes LIST  comma-separated scopes the HOST actually
                             requested. The report's scope.requested must
                             match exactly — a scope silently dropped by the
                             agent fails validation.
    --expect-commit SHA      require report["source"]["commit_sha"] == SHA
                             (binds the report to the commit the host
                             measured, not one the agent claims)
    --snapshot-dir DIR       verify provenance digests AND finding evidence
                             against the bytes under DIR. Paths are resolved
                             and must stay inside DIR — absolute paths,
                             ".." components, and symlink escapes are
                             rejected.

Exit code 0 = contract satisfied. Non-zero with one line per violation.
This validates structure and invariants — it does not evaluate whether the
agent audited well.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "audit-report.schema.json"
REQUEST_SCHEMA_PATH = REPO_ROOT / "schema" / "audit-request.schema.json"


def load_request(path: str):
    """Parse a locked request file (JSON or YAML) + validate its schema."""
    text = Path(path).read_text()
    req = json.loads(text) if path.endswith(".json") else None
    if req is None:
        import yaml
        req = yaml.safe_load(text)
    import jsonschema
    rs = json.loads(REQUEST_SCHEMA_PATH.read_text())
    jsonschema.Draft202012Validator(rs).validate(req)
    return req


def check_request_binding(report: dict, req: dict, errors: list) -> None:
    """Every host-owned fact in the locked request must match the report."""
    if report["audit_id"] != req["audit_id"]:
        errors.append(
            f"audit_id '{report['audit_id']}' does not match locked "
            f"request '{req['audit_id']}'"
        )
    if report["source"].get("commit_sha") != req["source"]["commit_sha"]:
        errors.append(
            "source.commit_sha does not match the locked request's "
            f"'{req['source']['commit_sha']}'"
        )
    if set(report["scope"]["requested"]) != set(req["requested_scopes"]):
        errors.append(
            f"scope.requested {sorted(report['scope']['requested'])} does not "
            f"match locked request {sorted(req['requested_scopes'])}"
        )


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


def resolve_inside(base: Path, rel: str, errors: list, label: str):
    """Resolve a report-controlled path inside base; return None on escape."""
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts:
        errors.append(f"{label}: path escapes snapshot dir: {rel!r}")
        return None
    target = (base / str(p)).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        errors.append(f"{label}: path escapes snapshot dir (symlink): {rel!r}")
        return None
    return target


def check_snapshot(report: dict, base: Path, errors: list) -> None:
    """Bind provenance digests and finding evidence to snapshot bytes."""
    digests = report["provenance"]["input_digests"]
    if not digests:
        errors.append("provenance.input_digests is empty — nothing to verify")
    for item in digests:
        target = resolve_inside(base, item["path"], errors, "input digest")
        if target is None:
            continue
        if not target.is_file():
            errors.append(f"input digest: '{item['path']}' not found in snapshot dir")
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
            errors.append(f"input digest mismatch for '{item['path']}'")
    for f in report["findings"]:
        ev = f["evidence"]
        target = resolve_inside(base, ev["file"], errors, f"finding {f['id']} evidence")
        if target is None:
            continue
        if not target.is_file():
            errors.append(f"finding {f['id']}: evidence file '{ev['file']}' not in snapshot")
            continue
        n_lines = len(target.read_text(errors="replace").splitlines())
        if ev["line_end"] > n_lines:
            errors.append(
                f"finding {f['id']}: evidence line_end {ev['line_end']} "
                f"past end of '{ev['file']}' ({n_lines} lines)"
            )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--request")
    ap.add_argument("--requested-scopes")
    ap.add_argument("--expect-commit")
    ap.add_argument("--snapshot-dir")
    args = ap.parse_args()

    errors: list = []
    report = json.loads(Path(args.report).read_text())

    try:
        import jsonschema
        import yaml
    except ImportError:
        print(
            "jsonschema and pyyaml are required: "
            "pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        return 2

    schema = json.loads(SCHEMA_PATH.read_text())
    for e in jsonschema.Draft202012Validator(schema).iter_errors(report):
        errors.append(f"schema: {e.message}")
    if not errors:
        check(report, errors)

    if args.request:
        try:
            check_request_binding(report, load_request(args.request), errors)
        except (jsonschema.ValidationError, yaml.YAMLError,
                json.JSONDecodeError, KeyError) as e:
            errors.append(f"locked request invalid: {e}")

    if args.requested_scopes:
        expected = {s.strip() for s in args.requested_scopes.split(",") if s.strip()}
        if set(report["scope"]["requested"]) != expected:
            errors.append(
                f"scope.requested {sorted(report['scope']['requested'])} does not "
                f"match the scopes the host requested {sorted(expected)}"
            )

    if args.expect_commit and report["source"].get("commit_sha") != args.expect_commit:
        errors.append(
            f"source.commit_sha '{report['source'].get('commit_sha')}' "
            f"does not match expected '{args.expect_commit}'"
        )

    if args.snapshot_dir:
        check_snapshot(report, Path(args.snapshot_dir), errors)

    if errors:
        for e in errors:
            print(f"INVALID: {e}")
        return 1
    print("report satisfies schema and contract invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
