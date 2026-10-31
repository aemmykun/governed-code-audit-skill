# Example Audit Report — MOCK DATA

All repositories, people, organizations, code paths, and findings below are
fictional and exist only to demonstrate the report format defined in
`SKILL.md` and `schema/audit-report.schema.json`.

**Audit ID:** `audit-2026-10-31-001`
**Repository:** `example-service` (mock)
**Commit:** `0123456789abcdef0123456789abcdef01234567`
**Status:** `complete_with_limitations`
**Release gate recommendation:** `recommend_block_merge` *(a recommendation —
enforcement belongs to the operator's policy engine)*

---

## 1. Executive summary

| Field | Value |
| --- | --- |
| Overall risk | critical |
| Release gate recommendation | recommend_block_merge |
| Audit status | complete_with_limitations |
| Findings | critical: 1, high: 1, medium: 2, low: 1, informational: 0 |
| Blocked scopes | none |
| Key risks | Retrieval can run before caller authorization; a committed secret-like token was found in a fixture file. |

## 2. Audit scope

- Trigger: `pre_merge`
- Requested scopes: `security`, `architecture`, `compliance`, `agent_governance`
- Completed scopes: all requested

## 3. Context completeness

`status: complete` — every input required for the requested scopes was supplied
and hashed into the audit manifest.

## 4. Findings

### FIND-001 (critical, confirmed)

- **Category:** `agent_governance`
- **Title:** Retrieval executes before caller authorization
- **Location:** `src/agents/assistant/retrieval.py:48-63` (mock path)
- **Evidence:** `vector_store.search(query)` is invoked before
  `authorize(user, tenant_id, resource_ids)` returns; see the embedded JSON for
  the exact quoted lines (redacted).
- **Impact:** A caller may cause retrieval of documents outside their permitted
  scope before the authorization decision is applied.
- **Policy reference:** `EXAMPLE-POLICY-001` — pre-retrieval authorization required.
- **Recommendation:** Authorize the caller and constrain the query to the
  verified tenant and permitted resource IDs before retrieval executes.
- **Remediation effort:** medium · **Owner role:** agent-platform-owner

### FIND-002 (high, confirmed)

- **Category:** `security`
- **Title:** Secret-like token committed to repository
- **Location:** `config/settings.yaml:14` (mock path)
- **Evidence:** A value matching a token pattern is present. The value is
  redacted in this report and must be treated as compromised.
- **Impact:** Anyone with repository read access can obtain the credential.
- **Recommendation:** Revoke the credential, remove it from history, and move
  it to the secrets manager referenced in `infrastructure_configuration`.
- **Remediation effort:** small · **Owner role:** repo-owner

### FIND-003 (medium, probable)

- **Category:** `security`
- **Title:** Missing audit event on administrative action
- **Location:** `src/admin/users.py:112` (mock path)
- **Evidence:** `disable_user()` performs a privileged change without an
  adjacent audit event emission found by static inspection.
- **Impact:** Sensitive actions may lack a tamper-evident trail.
- **Recommendation:** Emit a `user.disabled` audit event before returning.
- **Remediation effort:** small · **Owner role:** service-owner

### FIND-004 (medium, needs_human_review)

- **Category:** `architecture`
- **Title:** Domain layer imports from infrastructure layer
- **Location:** `src/domain/billing.py:7` (mock path)
- **Evidence:** `from infra.db import Connection` inside a module declared
  domain-layer by `architecture_rules` (mock rule `ARCH-DEP-002`).
- **Impact:** Violates the declared dependency direction; may couple domain
  logic to a specific datastore.
- **Recommendation:** Introduce a port interface or confirm the import is
  intentional and record an architecture exception.
- **Remediation effort:** medium · **Owner role:** architecture-owner

### FIND-005 (low, confirmed)

- **Category:** `maintainability`
- **Title:** Duplicated retry helper
- **Location:** `src/util/retry.py`, `src/util/retry_v2.py` (mock paths)
- **Evidence:** Two near-identical `with_retry` implementations (92% similarity).
- **Recommendation:** Consolidate into a single helper.
- **Remediation effort:** trivial · **Owner role:** service-owner

## 5. Risk analysis

The single critical finding is `confirmed` with `high` confidence and is the
basis of the `recommend_block_merge` recommendation. The high finding is also
`confirmed`. Medium findings are probable or need human review and carry
scheduled remediation. No `unverified` findings exist because all required
context was supplied.

## 6. Remediation

| Finding | Priority | Action | Owner role | Verification | Deadline |
| --- | --- | --- | --- | --- | --- |
| FIND-001 | immediate | Authorize before retrieval; constrain query scope | agent-platform-owner | Regression test `test_authz_before_retrieval` | next_release |
| FIND-002 | immediate | Revoke credential, purge history, migrate to secrets manager | repo-owner | Secret-scan re-run returns clean | 2026-11-03 |
| FIND-003 | high | Emit `user.disabled` audit event | service-owner | Unit test asserts event emitted | 2026-11-14 |
| FIND-004 | scheduled | Introduce port interface or record exception | architecture-owner | Architecture rule re-check passes | 2026-12-01 |
| FIND-005 | backlog | Consolidate retry helpers | service-owner | `duplication` check passes | backlog |

## 7. Governance assessment

The `agent_governance` scope ran and is reported separately. FIND-001 is a
pre-retrieval control failure. Tool-call authorization and output-policy
checks passed on the supplied mock definitions; see the manifest's
`policy_pack_hashes` for the exact versions assessed.

## 8. Limitations

- Runtime authorization behavior was not dynamically tested (static audit only).
- External connector configuration was not supplied; integrations were not assessed.
- This report is a recommendation for human review; no gate was enforced by the skill.

## 9. Sign-off

*Pending human review.* A conforming deployment routes critical/high findings
to a human owner before any release decision.

---

## Machine-readable form

The same report serialized as JSON (validates against
`schema/audit-report.schema.json`):

```json
{
  "audit_id": "audit-2026-10-31-001",
  "audit_status": "complete_with_limitations",
  "executive_summary": {
    "overall_risk": "critical",
    "release_gate_recommendation": "recommend_block_merge",
    "audit_status": "complete_with_limitations",
    "findings_by_severity": {
      "critical": 1,
      "high": 1,
      "medium": 2,
      "low": 1,
      "informational": 0
    },
    "coverage_by_area": {
      "security": { "status": "fail", "risk": "high", "coverage": "full" },
      "architecture": { "status": "fail", "risk": "medium", "coverage": "full" },
      "compliance": { "status": "pass", "risk": "low", "coverage": "full" },
      "maintainability": { "status": "pass", "risk": "low", "coverage": "full" },
      "agent_governance": { "status": "fail", "risk": "critical", "coverage": "full" }
    },
    "blocked_scopes": [],
    "key_risks": [
      "Retrieval can execute before caller authorization",
      "Secret-like token committed to the repository"
    ]
  },
  "audit_scope": {
    "repository": "example-service",
    "commit_sha_or_snapshot": "0123456789abcdef0123456789abcdef01234567",
    "trigger": "pre_merge",
    "requested_scopes": ["security", "architecture", "compliance", "agent_governance"],
    "completed_scopes": ["security", "architecture", "compliance", "agent_governance", "maintainability"]
  },
  "context_completeness": {
    "status": "complete",
    "missing_context": [],
    "blocked_scopes": []
  },
  "findings": [
    {
      "id": "FIND-001",
      "severity": "critical",
      "confidence": "high",
      "verification_status": "confirmed",
      "category": "agent_governance",
      "title": "Retrieval executes before caller authorization",
      "location": "src/agents/assistant/retrieval.py:48-63",
      "evidence": "vector_store.search(query) is invoked before authorize(user, tenant_id, resource_ids) returns",
      "impact": "A caller may cause retrieval of documents outside their permitted scope",
      "policy_reference": "EXAMPLE-POLICY-001",
      "recommendation": "Authorize the caller and constrain the query to the verified tenant and permitted resource IDs before retrieval executes",
      "remediation_effort": "medium",
      "owner_role": "agent-platform-owner",
      "evidence_trace": {
        "rule": "agent.pre_retrieval_authorization",
        "input_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000001",
        "commit_sha": "0123456789abcdef0123456789abcdef01234567"
      },
      "status": "open"
    },
    {
      "id": "FIND-002",
      "severity": "high",
      "confidence": "high",
      "verification_status": "confirmed",
      "category": "security",
      "title": "Secret-like token committed to repository",
      "location": "config/settings.yaml:14",
      "evidence": "Value matching a token pattern present; redacted in report",
      "impact": "Anyone with repository read access can obtain the credential",
      "recommendation": "Revoke the credential, remove it from history, move it to the secrets manager",
      "remediation_effort": "small",
      "owner_role": "repo-owner",
      "status": "open"
    },
    {
      "id": "FIND-003",
      "severity": "medium",
      "confidence": "medium",
      "verification_status": "probable",
      "category": "security",
      "title": "Missing audit event on administrative action",
      "location": "src/admin/users.py:112",
      "evidence": "disable_user() performs a privileged change with no adjacent audit event emission found by static inspection",
      "impact": "Sensitive actions may lack a tamper-evident trail",
      "recommendation": "Emit a user.disabled audit event before returning",
      "remediation_effort": "small",
      "owner_role": "service-owner",
      "status": "open"
    },
    {
      "id": "FIND-004",
      "severity": "medium",
      "confidence": "medium",
      "verification_status": "needs_human_review",
      "category": "architecture",
      "title": "Domain layer imports from infrastructure layer",
      "location": "src/domain/billing.py:7",
      "evidence": "from infra.db import Connection inside a module declared domain-layer by rule ARCH-DEP-002",
      "impact": "Violates the declared dependency direction",
      "recommendation": "Introduce a port interface or record an architecture exception",
      "architecture_rule": "ARCH-DEP-002",
      "remediation_effort": "medium",
      "owner_role": "architecture-owner",
      "status": "open"
    },
    {
      "id": "FIND-005",
      "severity": "low",
      "confidence": "high",
      "verification_status": "confirmed",
      "category": "maintainability",
      "title": "Duplicated retry helper",
      "location": "src/util/retry.py, src/util/retry_v2.py",
      "evidence": "Two near-identical with_retry implementations (92% similarity)",
      "impact": "Duplicated logic increases maintenance cost",
      "recommendation": "Consolidate into a single helper",
      "remediation_effort": "trivial",
      "owner_role": "service-owner",
      "status": "open"
    }
  ],
  "remediation": [
    {
      "finding_id": "FIND-001",
      "priority": "immediate",
      "action": "Authorize before retrieval; constrain query scope to the verified tenant",
      "owner_role": "agent-platform-owner",
      "verification_method": "Regression test test_authz_before_retrieval",
      "target_deadline": "next_release",
      "estimated_effort": "medium",
      "approval_required": true
    },
    {
      "finding_id": "FIND-002",
      "priority": "immediate",
      "action": "Revoke credential, purge from history, migrate to secrets manager",
      "owner_role": "repo-owner",
      "verification_method": "Secret-scan re-run returns clean",
      "target_deadline": "2026-11-03",
      "estimated_effort": "small"
    },
    {
      "finding_id": "FIND-003",
      "priority": "high",
      "action": "Emit user.disabled audit event",
      "owner_role": "service-owner",
      "verification_method": "Unit test asserts event emitted",
      "target_deadline": "2026-11-14",
      "estimated_effort": "small"
    },
    {
      "finding_id": "FIND-004",
      "priority": "scheduled",
      "action": "Introduce port interface or record architecture exception",
      "owner_role": "architecture-owner",
      "verification_method": "Architecture rule re-check passes",
      "target_deadline": "2026-12-01",
      "estimated_effort": "medium"
    },
    {
      "finding_id": "FIND-005",
      "priority": "backlog",
      "action": "Consolidate retry helpers",
      "owner_role": "service-owner",
      "verification_method": "duplication check passes",
      "target_deadline": "backlog",
      "estimated_effort": "trivial"
    }
  ],
  "governance_assessment": {
    "pre_retrieval_authorization": "fail",
    "tool_call_authorization": "pass",
    "output_policy": "pass",
    "audit_log_generation": "pass",
    "note": "Agent-governance checks reported separately from general code quality"
  },
  "limitations": [
    "Runtime authorization behavior was not dynamically tested",
    "External connector configuration was not supplied",
    "This report is a recommendation for human review; no gate was enforced by the skill"
  ],
  "audit_manifest": {
    "audit_id": "audit-2026-10-31-001",
    "skill_name": "governed-code-audit",
    "skill_version": "0.1.0",
    "repository": "example-service",
    "commit_sha": "0123456789abcdef0123456789abcdef01234567",
    "snapshot_id": "snapshot-0123ab",
    "started_at": "2026-10-31T09:00:00Z",
    "completed_at": "2026-10-31T09:04:00Z",
    "actor": "code-audit-agent",
    "authority_scope": "requested_audit_scope",
    "input_hashes": {
      "source_code": "sha256:0000000000000000000000000000000000000000000000000000000000000001",
      "architecture_rules": "sha256:0000000000000000000000000000000000000000000000000000000000000002",
      "authorization_model": "sha256:0000000000000000000000000000000000000000000000000000000000000003",
      "tool_registry": "sha256:0000000000000000000000000000000000000000000000000000000000000004"
    },
    "policy_pack_hashes": {
      "code-standards": "sha256:0000000000000000000000000000000000000000000000000000000000000005",
      "security-policies": "sha256:0000000000000000000000000000000000000000000000000000000000000006"
    },
    "findings_summary": {
      "critical": 1,
      "high": 1,
      "medium": 2,
      "low": 1,
      "informational": 0
    },
    "audit_status": "complete_with_limitations",
    "release_gate_recommendation": "recommend_block_merge",
    "limitations": [
      "Runtime authorization behavior was not dynamically tested",
      "External connector configuration was not supplied"
    ],
    "signature": "example-signature-placeholder"
  }
}
```
