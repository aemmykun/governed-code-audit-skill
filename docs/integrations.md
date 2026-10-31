# Integrations

Optional patterns for wiring a governed-code-audit implementation into real
systems. **Nothing here is built into the skill** — these are reference recipes
for the host framework that invokes it. The framework owns identity,
permissions, policy evaluation, tool invocation, evidence storage, and audit
logging; the skill only performs read-only analysis and returns structured
results.

## Runtime flow

```
User / CI trigger
        |
        v
Agent Orchestrator
        |
        +-- Authority Service: validate actor, tenant, repo, and audit scope
        +-- Context Service: fetch approved inputs and compute hashes
        +-- Policy Engine: decide which audit scopes may run
        v
Code Audit Skill            <-- read-only analysis only
        |
        +-- Static analyzers / secret scanner / dependency scanner
        +-- Architecture rule engine / agent-governance rule engine
        v
Finding Normaliser          (dedupe; classify severity/confidence/verification)
        v
Evidence Store + Audit Log
        v
Signed Audit Manifest / Release-gate recommendation
        |
        v
External policy engine enforces (or humans approve)
```

## Execution environment contract

A conforming deployment runs the skill with least privilege:

```yaml
execution_environment:
  network_access: denied_by_default
  filesystem_access: read_only_snapshot
  code_execution: denied
  allowed_connectors:
    - source_control
    - policy_repository
    - evidence_store
    - audit_log
  denied_connectors:
    - production_database
    - deployment_system
    - external_llm_services
    - email
    - payment_systems

authority:
  required_permissions: [repo:read, policy:read, audit:write, evidence:write]
  delegation:
    allowed: true
    max_scope: requested_audit_scope
    prohibit_scope_escalation: true
```

## Output contract

```yaml
output_contract:
  return_type: structured_json           # see schema/audit-report.schema.json
  required_sections:
    - audit_status
    - release_gate_recommendation
    - findings
    - evidence_traceability
    - audit_manifest
  prohibited_outputs:
    - raw_secrets
    - unredacted_pii
    - credentials
    - private_keys
    - unverified_claims_presented_as_facts
```

## Trigger types

Typical triggers: `manual_request`, `pull_request_opened`,
`pull_request_updated`, `pre_merge`, `pre_release`, `scheduled_scan`,
`policy_change`, `dependency_change`, `agent_definition_change`.

A direct production-deployment trigger is normally **denied** — the audit is a
review step, not a deployment action.

## Staged gates (policy engine territory)

The report carries `release_gate_recommendation`. The operator's policy engine
decides what to do with it. Typical mappings:

| Recommendation | Example external action |
| --- | --- |
| `recommend_block_merge` | Fail the PR status check; require human override |
| `recommend_block_release` | Hold the release pipeline pending review |
| `approve_with_conditions` | Merge allowed once medium findings have owner + deadline |
| `approve` | Proceed |

Example gate conditions an operator might configure:

```yaml
block_merge_conditions:
  - any_confirmed_critical_security_finding
  - any_confirmed_cross_tenant_access_finding
  - any_confirmed_hardcoded_production_secret
  - any_agent_privileged_tool_without_authorization

block_release_conditions:
  - any_unresolved_high_compliance_finding
  - missing_audit_log_for_sensitive_agent_action
  - missing_provenance_for_agent_response

approve_with_conditions:
  - medium_findings_have_owner_and_deadline
  - probable_high_findings_have_human_review_task
```

Key rule: only `confirmed` findings feed automated gates. `probable` and
`needs_human_review` findings route to humans, not to blocking logic.

## Approval policy

| Action | Decided by |
| --- | --- |
| read_repository, read_policy_pack, run scanners, create report | the agent's own authority (audited, no approval needed) |
| block_merge / block_release / notify security team | policy engine |
| create external tickets, send chat notifications | human approval or a pre-approved service account |

## Example invocation and response

- Request: [`examples/audit-request.example.yaml`](../examples/audit-request.example.yaml)
- Response: [`examples/audit-report.example.md`](../examples/audit-report.example.md)
  (contains the equivalent JSON, validatable against
  `schema/audit-report.schema.json`)

Both are mock data. Wire the real fields to your own identity, repository, and
policy references.

## Audit logging

Emit a `code_audit.completed` append-only event per run with: `audit_id`,
`actor`, `repository`, `commit_sha`, `authority_scope`, `input_hashes`,
`result_summary`, `release_gate_recommendation`, `timestamp`, and a signature
produced by the framework. Retention is the operator's policy decision (a
common default is seven years for compliance programs).
