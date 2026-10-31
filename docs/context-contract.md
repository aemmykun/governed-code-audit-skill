# Context Contract

The audit skill operates on a **contract**, not a loose prompt payload. Every
input has a type, a trust level, an integrity requirement, and a defined
failure behavior. This document is the reference version of that contract;
`SKILL.md` §4 states the normative blocking rules.

## Why a contract

Loose prompts let missing context turn into confident guesses. A contract makes
each input's absence a declared, observable outcome: the scope that needed it
is blocked, the gap is listed in `missing_context`, and the audit status drops
to `incomplete` (or `rejected` when source code itself is missing).

## Input fields

Every input declares:

| Field | Meaning |
| --- | --- |
| `type` | `repository_snapshot`, `file_tree`, `structured_document`, `policy_pack`, `file`, `identity` |
| `required` / `required_for` | whether the audit or a specific scope blocks without it |
| `trust_level` | `trusted_internal` (operator-controlled source) or `derived` (computed from another input) |
| `source` | where the framework resolves it from |
| `integrity` | `require_commit_sha`, `compute_sha256` — inputs are hash-addressed so audits are reproducible |
| `fail_if_missing` | what happens when the input is absent |

## Inputs

### `audit_request` — required

Object carrying `audit_id`, `requested_scope` (subset of `security`,
`architecture`, `compliance`, `maintainability`, `agent_governance`),
`requester` identity, and `purpose`.

### `source_code` — required

- Type: `repository_snapshot`; trust: `trusted_internal`; source: approved VCS connector.
- Integrity: `require_commit_sha: true`, `compute_sha256: true`.
- Access: `repo:read`, scoped to the requesting tenant.
- `fail_if_missing: reject_audit` — source code is mandatory.
- Out-of-scope repository → `rejected`.

### `repository_structure` — required

- Type: `file_tree`; trust: `derived` from `source_code`.
- `fail_if_missing: derive_from_source_code`.

### `requirements` — required

- Type: `structured_document`; must include security and data-handling requirements.
- `fail_if_missing: limit_scope_to_static_quality_review`.

### `coding_standards` — required

- Type: `policy_pack`; versioned.
- `fail_if_missing: use_fallback_standards_and_mark_as_assumption` — findings
  derived from fallback standards are labelled assumptions, never facts.

### `architecture_rules` — required

- Type: `policy_pack`; must define dependency direction, module boundaries,
  data-classification flow, and isolation rules.
- `fail_if_missing: block_architecture_audit`.

### `authentication_model` — required for `security`

Fields: identity provider, session model, token validation, MFA requirements,
service authentication. `fail_if_missing: block_security_audit`.

### `authorization_model` — required for `security`

Fields: roles, permissions, resource ownership, isolation rules,
administrative actions. `fail_if_missing: block_authorization_review`.

### `data_classification` — required for `security` and `compliance`

Fields: data categories, sensitivity levels, retention rules, permitted
locations, cross-border rules. `fail_if_missing: block_compliance_audit`.

### `dependency_manifest` — required for dependency review

Accepted formats: `package-lock.json`, `package.json`, `requirements.txt`,
`poetry.lock`, `pyproject.toml`, `pom.xml`, `go.mod`, `Cargo.lock`.
`fail_if_missing: block_dependency_review`.

### `infrastructure_configuration` — optional

IaC, containers, CI/CD, deployment, secrets management, network policy.
`fail_if_missing: mark_deployment_review_not_assessed`.

### Agent-governance inputs — required for `agent_governance`

| Input | Key fields | fail_if_missing |
| --- | --- | --- |
| `agent_definition` | agent_id, intended_purpose, allowed_tools, allowed_data_sources, autonomy_level, human_approval_rules | block_agent_governance_audit |
| `tool_registry` | tool_id, capability, required_permission, input_schema, side_effects, reversibility, audit_event | block_tool_permission_review |
| `authority_model` | actor_identity, delegated_authority, scope_rules, tenant_scope, approval_requirements | block_agent_governance_audit |
| `retrieval_configuration` | retrieval_sources, authorization_point, tenant_filters, document_acl_enforcement, provenance_capture | block_retrieval_governance_review |
| `output_policy` | permitted_output_types, redaction_rules, citation_requirements, external_sharing_rules | block_output_governance_review |
| `audit_log_configuration` | log_destination, retention_period, integrity_protection, event_schema, access_controls | block_compliance_and_governance_signoff |

### Other optional inputs

`threat_model`, `applicable_policies`, `prior_audit_results`, `test_results`,
`runtime_evidence` — all `structured_document` / `policy_pack`, all
`trusted_internal`. Optional inputs improve coverage; they are never fabricated
when absent.

## Resolution outcomes

```yaml
context_resolution:
  complete:
    audit_status: complete
    allowed_scopes: [security, architecture, compliance, maintainability, agent_governance]
  partial:
    audit_status: incomplete
    allowed_scopes: [maintainability]          # scopes whose inputs were satisfied
    blocked_scopes: [security, compliance, agent_governance]
    missing_context: [authorization_model, data_classification, tool_registry]
  rejected:
    audit_status: rejected
    reason: source_code_missing_or_outside_approved_scope
```

The auditor never claims a control exists or is absent when the context needed
to check it was missing — it reports the scope as blocked instead.
