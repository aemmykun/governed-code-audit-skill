#!/usr/bin/env python3
"""Reference audit agent — a real (deterministic) implementation of the
governed-code-audit contract, small enough to run inside the sandbox demo.

This is NOT a mock: it reads a locked request, reads only the authorized
snapshot, performs real static checks, fails closed on missing context, and
emits a schema-conformant report that tools/validate_report.py accepts.

Usage (inside or outside the sandbox):
    python reference_agent.py REQUEST_SNAPSHOT_DIR CONTEXT_DIR REPORT_OUT

    REQUEST   locked audit request (YAML/JSON, audit-request.schema.json)
    SNAPSHOT  authorized snapshot dir (read-only evidence)
    CONTEXT   approved context dir (files named by context key)
    REPORT    output path for the JSON report

Deterministic checks implemented (extend for real deployments):
  - credential-like literals in committed files        -> security / high
  - retrieval/search call before authorization call    -> agent_governance / critical

Missing required context for a requested scope blocks that scope
(fail closed) — matching docs/context-contract.md.
"""

import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_report import load_request  # noqa: E402

SCOPE_CONTEXT = {
    "security": ["authentication_model", "authorization_model",
                 "data_classification", "dependency_manifest"],
    "agent_governance": ["agent_definition", "tool_registry",
                         "authority_model", "retrieval_configuration",
                         "output_policy", "audit_log_configuration"],
    "maintainability": ["requirements", "coding_standards"],
    "architecture": ["architecture_rules", "dependency_boundaries",
                     "data_flow_rules"],
    "compliance": ["applicable_policies", "data_classification",
                   "audit_log_configuration"],
}

SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}")
# Retrieval-specific calls — deliberately NOT the bare word `search(`:
# generic .search() on regexes/strings would be a false-positive machine.
RETRIEVE_RE = re.compile(
    r"(?i)(vector_store|doc_store|retriev\w*|search_docs|query_docs|"
    r"fetch_docs|get_documents|lookup_docs)\s*[.\w]*\(")
AUTHZ_RE = re.compile(r"(?i)(authoriz|has_permission|check_scope|verify_access)")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(request, snapshot: Path, context: Path) -> dict:
    snap_id = f"audit-{request['audit_id']}"
    requested = request["requested_scopes"]

    # --- resolve context: fail closed on missing required inputs ---
    assessed, blocked, missing = [], [], []
    for scope in requested:
        needed = SCOPE_CONTEXT.get(scope, [])
        absent = [
            k for k in needed
            if k not in request.get("context", {})
            or not (context / k).exists()
        ]
        if absent:
            blocked.append(scope)
            missing.extend(f"{scope}: {k}" for k in absent)
        else:
            assessed.append(scope)

    # Host-declared exclusions: out of bounds entirely — the agent must not
    # inspect, cite, or digest them. (Digests cover only in-scope files, so
    # excluded files are never attested as reviewed.)
    excludes = request.get("exclude_paths", [])
    files = [
        p for p in sorted(snapshot.rglob("*"))
        if p.is_file()
        and not any(
            fnmatch.fnmatch(str(p.relative_to(snapshot)), pat)
            for pat in excludes)
    ]

    findings = []
    fid = 0
    if "security" in assessed:
        for p in files:
            for i, line in enumerate(
                    p.read_text(errors="replace").splitlines(), 1):
                if SECRET_RE.search(line):
                    fid += 1
                    findings.append({
                        "id": f"F-{fid:03d}",
                        "title": "Credential-like literal in committed file",
                        "category": "security", "severity": "high",
                        "confidence": "medium",
                        "verification_status": "probable",
                        "evidence": {
                            "snapshot_id": snap_id,
                            "file": str(p.relative_to(snapshot)),
                            "line_start": i, "line_end": i,
                            "excerpt": line.strip()[:80],
                            "method": "static_inspection"},
                        "impact": "A committed secret is readable by anyone with repository access.",
                        "recommendation": "Move to a secret store and rotate the value."})
    if "agent_governance" in assessed:
        for p in files:
            lines = p.read_text(errors="replace").splitlines()
            first_retrieve = next(
                (i for i, l in enumerate(lines, 1) if RETRIEVE_RE.search(l)),
                None)
            first_authz = next(
                (i for i, l in enumerate(lines, 1) if AUTHZ_RE.search(l)),
                None)
            if first_retrieve and (
                    first_authz is None or first_retrieve < first_authz):
                fid += 1
                findings.append({
                    "id": f"F-{fid:03d}",
                    "title": "Retrieval executes before caller authorization",
                    "category": "agent_governance", "severity": "critical",
                    "confidence": "high",
                    "verification_status": "probable",
                    "evidence": {
                        "snapshot_id": snap_id,
                        "file": str(p.relative_to(snapshot)),
                        "line_start": first_retrieve,
                        "line_end": first_authz or first_retrieve,
                        "excerpt": "retrieval call precedes authorization",
                        "method": "static_inspection"},
                    "impact": "Untrusted callers can trigger retrieval before their scope is checked (pre-retrieval authorization failure).",
                    "recommendation": "Authorize the caller's scope before issuing the retrieval call; pass the tenant filter into the query."})

    status = "incomplete" if blocked else "complete"
    return {
        "schema_version": "0.2.0",
        "audit_id": request["audit_id"],
        "audit_status": status,
        "source": {"snapshot_id": snap_id,
                   "commit_sha": request["source"]["commit_sha"]},
        "scope": {"requested": requested, "assessed": assessed,
                  "blocked": blocked},
        "missing_context": missing,
        "overall_risk": (
            "critical" if any(f["severity"] == "critical" for f in findings)
            else "high" if any(f["severity"] == "high" for f in findings)
            else "informational"),
        "findings": findings,
        "observations": [
            f"Reference agent: deterministic static checks only. "
            f"{len(files)} file(s) inspected."],
        "limitations": [
            "Pattern-based checks; no runtime verification.",
            "verification_status stays below 'confirmed' — a pattern match "
            "does not prove exploitability."],
        "release_gate": {"state": "not_evaluated",
                         "reason": "Gate decisions belong to host policy"},
        "provenance": {
            "skill_version": "0.2.0",
            "input_digests": [
                {"path": str(p.relative_to(snapshot)), "sha256": sha256(p)}
                for p in files],
            "signed": False},
    }


def main() -> int:
    req_path, snap_dir, ctx_dir, out = sys.argv[1:5]
    request = load_request(req_path)
    report = audit(request, Path(snap_dir), Path(ctx_dir))
    Path(out).write_text(json.dumps(report, indent=2))
    print(f"wrote {out}: status={report['audit_status']}, "
          f"findings={len(report['findings'])}, "
          f"blocked={report['scope']['blocked']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
