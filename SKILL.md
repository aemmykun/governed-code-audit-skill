---
name: governed-code-audit
version: 0.1.0
description: >
  Reviews source code and related artifacts for security, correctness,
  maintainability, architectural conformance, compliance, and AI-agent
  governance. Produces evidence-backed findings and a structured audit
  manifest. The skill is read-only and must never modify code,
  configuration, or external systems. Its output is a recommendation for
  human review, not a certification or an enforcement action.
---

# Governed Code Audit Skill

This document is the normative contract. It defines the audit scopes the skill
covers, the context it must receive before claiming anything, the taxonomy its
findings use, and the report it produces. Integration concerns (CI wiring,
policy engines, audit sinks) are deliberately out of scope here — see
`docs/integrations.md` for optional patterns.

## 1. Purpose

- Identify exploitable or high-impact defects.
- Verify conformance to declared architecture and policy rules.
- Assess maintainability and operational risk.
- Validate AI-agent authority, boundaries, provenance, and auditability.
- Produce traceable evidence for human review and compliance.

## 2. Hard constraints

A conforming implementation MUST:

- `must_not_modify_code` — never write to the audited tree or any external system.
- `must_not_execute_untrusted_code` — analysis is static; nothing under audit runs.
- `must_not_send_source_code_to_unapproved_external_services` — source material
  stays within the environment the host framework authorized.
- `must_not_expose_secrets_in_reports_or_logs` — evidence is quoted in redacted form.
- `evidence_required_for_findings` — no finding without inspectable evidence.
- `cite_exact_code_location` — file, line range, and commit where applicable.
- `fail_closed_on_missing_context` — missing required context blocks that scope;
  it is never guessed.
- `distinguish_fact_from_assumption` — assumptions are labelled as such.
- `separate_confirmed_findings_from_observations` — confirmed findings and
  informational observations are reported separately.
- `require_human_review_for_high_impact_or_uncertain_findings` — the skill
  recommends; humans decide.
- `enforce_least_privilege_tool_access` — request only the permissions the audit needs.
- `preserve_input_and_output_provenance` — record what was read, at which revision,
  and what was emitted.

## 3. Audit scopes

| Scope | What it covers |
| --- | --- |
| `security` | secrets, injection, authentication/authorization flaws, dependencies, deserialization, crypto misuse, file handling, SSRF/CSRF, logging, privilege escalation |
| `maintainability` | complexity, duplication, dead code, error handling, naming, testability, observability |
| `architecture` | boundary violations, dependency direction, module separation, domain-model integrity, data-flow integrity, governance rules |
| `compliance` | PII handling, audit logging, retention, policy alignment, consent/lawful basis, cross-border transfer, data minimisation |
| `agent_governance` | authority validation, pre-retrieval controls, provenance preservation, evidence traceability, audit-log generation, scope-boundary enforcement, fail-closed behavior, execution-proof verification, tool-call authorization, tool-argument validation, human approval for high-impact actions |

General code findings and agent-governance findings are reported separately even
when they share a root cause: they typically have different owners, controls,
and evidence requirements.

## 4. Required context (fail-closed)

The skill operates on a **context contract**, not a loose prompt. Every input has
a type, source, trust level, hash, and failure behavior. The full contract is in
`docs/context-contract.md`; the blocking rules are:

- **No `source_code`** → audit status `rejected`. Source is mandatory.
- **Source outside the approved repository scope** → `rejected`.
- **Any other missing required input** → audit status `incomplete`; the affected
  scopes are listed in `blocked_scopes` with `missing_context`, and completed
  scopes are reported normally. The skill must not make claims about controls it
  could not see.

Per-scope minimums:

| Scope | Required inputs beyond `source_code` and `repository_structure` |
| --- | --- |
| full audit | `architecture_rules`, `authentication_model`, `authorization_model`, `data_classification`, `dependency_manifest` |
| `security` | `authentication_model`, `authorization_model`, `dependency_manifest`, `data_classification` |
| `compliance` | `applicable_policies`, `data_classification`, `audit_log_configuration` |
| `agent_governance` | `agent_definition`, `tool_registry`, `authority_model`, `retrieval_configuration`, `output_policy`, `audit_log_configuration` |

Optional inputs (improve coverage, never fabricated when absent):
`dependency_manifest`, `infrastructure_configuration`, `threat_model`,
`data_classification`, `applicable_policies`, `prior_audit_results`,
`test_results`, `runtime_evidence`.

## 5. Finding taxonomy

Severity, confidence, and verification status are **independent fields** on every
finding:

- **Severity** — how bad is it if true? `critical` / `high` / `medium` / `low` / `informational`.
- **Confidence** — how likely is it real? `high` / `medium` / `low`.
- **Verification status** — what proof exists? `confirmed` / `probable` /
  `needs_human_review` / `false_positive_candidate` / `unverified`.

Decision model:

1. `confirmed` — a complete path is traced: untrusted input reaches a sensitive
   operation, the required validation/authorization is absent, and no
   compensating control is present.
2. `probable` — strong static evidence, but runtime behavior, deployment
   configuration, or a downstream control is unknown.
3. `needs_human_review` — depends on business rules, legal interpretation,
   architecture intent, or a compensating control not visible in code.
4. `false_positive_candidate` — a pattern matched, but a verified guard,
   allowlist, sanitizer, or policy exception exists.
5. `unverified` — mandatory context is absent. Do not guess.

**Never let confidence alone block a release.** A critical/low-confidence finding
routes to human review; a critical/confirmed finding may feed a release gate —
configured and owned by the operator's systems, not by this skill.

### Severity definitions

| Severity | Definition | Examples |
| --- | --- | --- |
| `critical` | Exploitable or policy-breaking issue with immediate confidentiality, integrity, availability, safety, legal, or financial impact | hardcoded production credential; cross-tenant data access; unauthenticated privileged action; prompt injection reaching a privileged tool |
| `high` | Significant weakness likely to cause material harm or control failure | missing authorization check on a sensitive endpoint; unsafe deserialization; unvalidated agent tool arguments |
| `medium` | Control weakness or maintainability issue needing scheduled remediation | weak error handling; missing audit event for a sensitive action; architecture boundary violation |
| `low` | Minor quality, documentation, or hygiene issue | duplicated logic; missing docstring; non-blocking lint issue |
| `informational` | Observation or improvement opportunity | recommended dependency upgrade; architectural observation |

### Finding fields

Required: `id`, `severity`, `confidence`, `verification_status`, `category`,
`title`, `location`, `evidence`, `impact`, `recommendation`.

Optional: `policy_reference`, `architecture_rule`, `compliance_control`,
`remediation_effort`, `owner_role`, `related_findings`, `false_positive_reason`,
`evidence_trace`, `detected_by`, `first_seen_commit`, `status`.

## 6. Report format

Reports contain, in order: `executive_summary`, `audit_scope`,
`context_completeness`, `findings`, `evidence`, `risk_analysis`, `remediation`,
`governance_assessment`, `limitations`, `sign_off`.

- `executive_summary` fields: `overall_risk`, `release_gate_recommendation`,
  `audit_status`, `findings_by_severity`, `coverage_by_area`,
  `blocked_scopes`, `key_risks`.
- `audit_status` ∈ `complete` | `complete_with_limitations` | `incomplete` | `rejected`.
- `release_gate_recommendation` ∈ `approve` | `approve_with_conditions` |
  `recommend_block_merge` | `recommend_block_release` |
  `recommend_block_deployment` | `incomplete`.

> The skill emits a **recommendation**. Whether a merge or release is actually
> blocked is decided by the operator's policy engine — see
> `docs/integrations.md`. A conforming report never presents its output as an
> executed enforcement action.

Coverage is reported per scope (`security`, `architecture`, `compliance`,
`maintainability`, `agent_governance`) with `status` ∈ `pass` | `fail` |
`not_assessed`, a risk level, and a coverage descriptor.

Machine-readable reports MUST validate against
`schema/audit-report.schema.json`.

## 7. Governance outputs

- **Audit manifest** — a hash-linked record: `audit_id`, skill name/version,
  `repository`, `commit_sha`/`snapshot_id`, timestamps, `actor`,
  `authority_scope`, `input_hashes`, `policy_pack_hashes`, `findings_summary`,
  `audit_status`, `release_gate_recommendation`, `limitations`, and an optional
  `signature` produced by the host framework.
- **Audit log event** — an append-only `code_audit.completed` event with the
  same identity fields, for the operator's governance log. Retention policy is
  owned by the operator, not the skill.

## 8. Evaluation criteria

A conforming audit:

- has evidence on every critical and high finding;
- cites file and line references where applicable;
- modified no code;
- produced a fail-closed result when required context was missing;
- yields a manifest reproducible from recorded input hashes;
- reports agent-governance checks separately from general code quality.

Regression fixtures live under `tests/fixtures/` and cover: vulnerable code,
clean code, missing authorization, cross-tenant access, a hardcoded secret, a
prompt-injection tool chain, and incomplete context.
