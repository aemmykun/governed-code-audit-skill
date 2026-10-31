# Integrations

Optional patterns for wiring a governed-code-audit implementation into real
systems. **Nothing here is built into the skill** — these are reference recipes
for the host framework that invokes it. The framework owns identity,
permissions, policy evaluation, tool invocation, evidence storage, and audit
logging; the skill only performs read-only analysis and returns structured
results.

## Manual use first

Load the core skill in an approved host, provide a snapshot and context, and
review the returned report manually. This repository does not implement a CLI
that audits code or automatically register with any agent product.

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
Report (release_gate: not_evaluated) + Provenance digests
        |
        v
External policy engine enforces (or humans approve)
```

## Optional host adapter

An adapter may authenticate the requester, check scope, fetch an immutable
source snapshot, validate context, invoke an approved agent, validate the
returned structure, and store redacted evidence. Implement these controls
outside the model.

Keep organization-specific policy packs in the consumer's environment. Do not
bundle production credentials, tenant data, internal architecture, or private
source into a public fork. Do not grant the auditor production or deployment
tools.

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

The report validates against `schema/audit-report.schema.json`. The schema
itself enforces two honesty constraints:

- `release_gate.state` is always `not_evaluated` — the skill never issues a
  gate decision, not even a recommendation. Gate logic lives entirely outside.
- `provenance.signed` is always `false` in this package — a signature requires
  a real signer configured by the host.

Prohibited outputs: raw secrets, unredacted PII, credentials, private keys,
unverified claims presented as facts, fabricated hashes, fabricated tool runs.

## Scanners, provenance, signing, and gates

Run any trusted scanner only in a separately authorized, isolated host
workflow. Do not execute target-provided scripts. Record scanner
version/configuration and the exact snapshot. Scanner availability and
dependency intelligence are not supplied by this skill.

If a real hashing/signing service is configured, record its exact input bytes,
algorithm, key identity, and verification method in a separate versioned
sidecar. Do not populate a fake signature or call an unsigned report
signed/immutable.

Keep the core report's release gate `not_evaluated`. A separate policy engine
or human may consume the report, context completeness, verification status,
and approved policy to issue a gate decision. Confidence alone must not
approve or block a release. Ticketing and notifications require separate
authorization.

## Trigger types

Typical triggers: `manual_request`, `pull_request_opened`,
`pull_request_updated`, `pre_merge`, `pre_release`, `scheduled_scan`,
`policy_change`, `dependency_change`, `agent_definition_change`.

A direct production-deployment trigger is normally **denied** — the audit is a
review step, not a deployment action.

## External gate patterns (policy engine territory)

The report carries findings with independent `severity`, `confidence`, and
`verification_status`. An operator's policy engine might map them to gates like:

| Finding condition | Example external action |
| --- | --- |
| any `confirmed` + `critical` security finding | fail the PR status check; require human override |
| any `confirmed` cross-tenant or hardcoded-secret finding | hold merge pending review |
| `probable` / `needs_human_review` high findings | open human review tasks, don't block |
| medium findings without owner + deadline | approve_with_conditions |

Only `confirmed` findings should feed automated gates. `probable` and
`needs_human_review` findings route to humans, not to blocking logic.

## Approval policy

| Action | Decided by |
| --- | --- |
| read_repository, read_policy_pack, run scanners, create report | the agent's own authority (audited, no approval needed) |
| block_merge / block_release / notify security team | policy engine |
| create external tickets, send chat notifications | human approval or a pre-approved service account |

## Example invocation and response

- Request: [`examples/audit-request.example.yaml`](../examples/audit-request.example.yaml)
- Response: [`examples/audit-report.example.json`](../examples/audit-report.example.json)
  (also [`audit-report.multi-scope.example.json`](../examples/audit-report.multi-scope.example.json)
  for a multi-scope run, and
  [`audit-report.example.md`](../examples/audit-report.example.md) for the
  human-readable rendering)

All are mock data. Wire the real fields to your own identity, repository, and
policy references.

## Audit logging

Emit a `code_audit.completed` append-only event per run with: `audit_id`,
`actor`, `repository`, `commit_sha`, `authority_scope`, `input_hashes`,
`result_summary`, `timestamp`, and a signature produced by the framework.
Retention is the operator's policy decision (a common default is seven years
for compliance programs).

## Fork-safe CI

The bundled workflow validates this package, not third-party target code. Give
it read-only permissions and no secrets. Do not use `pull_request_target` to
run untrusted fork code. Before public release, review dependencies and pin
reusable GitHub Actions to reviewed full commit SHAs.
