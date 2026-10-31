# governed-code-audit-skill

A portable specification and agent skill for **governed code auditing**: read-only,
evidence-backed analysis of source code and agent configurations that produces
structured findings for human review — never code changes, never verdicts that
silently bypass a human decision.

The skill is designed to run inside a host framework (CI pipeline, agent
orchestrator, policy engine) that owns identity, permissions, and enforcement.
The skill itself only analyzes and reports.

## What it does

- Reviews code for **security, maintainability, architecture conformance,
  compliance, and AI-agent governance** risks.
- Requires every finding to carry **evidence**, a **confidence** level, and a
  **verification status** — three independent fields, never collapsed into one score.
- **Fails closed**: when the context required for an audit scope is missing, that
  scope is reported as blocked rather than silently skipped or guessed.
- Emits a structured audit report (Markdown or JSON) plus an audit manifest with
  input hashes so the same inputs reproduce the same audit.

## What it does not do

- **Modify code, configuration, or external systems.** The skill is read-only by contract.
- **Execute untrusted code.** All analysis is static; nothing under audit is run.
- **Send source code to unapproved services.** Source material never leaves the
  environment the host framework authorizes.
- **Certify safety or block releases on its own.** Report output is a
  *recommendation for human review*. Approving merges, gating releases, and
  enforcing policy belong to external systems the operator configures
  (see [`docs/integrations.md`](docs/integrations.md)).
- **Replace a human auditor.** High-impact and uncertain findings are explicitly
  marked `needs_human_review`.

## Repository layout

```
├── SKILL.md                     # The skill contract: scope, inputs, constraints, report format
├── schema/
│   └── audit-report.schema.json # JSON Schema for machine-readable audit reports
├── examples/
│   ├── audit-request.example.yaml   # A complete, mock audit request
│   └── audit-report.example.md      # A complete, mock audit report
├── docs/
│   ├── context-contract.md      # Required/optional inputs, trust levels, fail-closed rules
│   ├── security-model.md        # Threat model, agent attack vectors, governance principles
│   └── integrations.md          # Optional patterns: CI, policy engines, audit logs
├── tests/
│   └── fixtures/                # Mock vulnerable/clean code for regression testing
├── CONTRIBUTING.md
├── SECURITY.md                  # How to report vulnerabilities in this repo
├── CHANGELOG.md
├── LICENSE
└── .github/workflows/check.yml  # CI: lint, schema validation, mock-data checks, secret scan
```

## Quick start

1. Read [`SKILL.md`](SKILL.md) — it is the normative contract a compliant
   implementation must satisfy.
2. Supply the inputs described in [`docs/context-contract.md`](docs/context-contract.md).
   Missing required context produces a fail-closed (`incomplete` / `rejected`)
   result, not a partial guess.
3. Produce a report that validates against
   [`schema/audit-report.schema.json`](schema/audit-report.schema.json). See
   [`examples/audit-report.example.md`](examples/audit-report.example.md) for a
   complete worked example.
4. Optionally wire the report into your own gates using the patterns in
   [`docs/integrations.md`](docs/integrations.md) — those are integration
   *recipes*, not built-in behavior.

## Design principles

- **The framework enforces security; the model advises.** Authorization, tenant
  isolation, tool permissions, and approvals belong to deterministic services,
  not prompt instructions.
- **Every audit is reproducible.** Inputs are hashed and recorded in the audit
  manifest; identical inputs should yield identical results.
- **Severity, confidence, and verification are independent.** A critical finding
  with low confidence triggers human review; only a confirmed critical finding
  should feed a release gate configured by the operator.
- **Redact before reporting.** Evidence quotes enough code to prove an issue
  without reproducing live secrets, tokens, or personal data.

## Conformance

An implementation conforms to this skill when it satisfies the `constraints` and
`context_requirements` in [`SKILL.md`](SKILL.md) and emits reports that validate
against `schema/audit-report.schema.json`. The fixtures under `tests/fixtures/`
provide regression cases (vulnerable, clean, and incomplete-context inputs) with
expected outcomes.

## Versioning

This repository is versioned with git tags. The current release is **v0.1.0** —
the contract is usable but may evolve in backwards-incompatible ways until
v1.0.0. See [`CHANGELOG.md`](CHANGELOG.md) for what changed between releases.
If you fork or vendor this skill, pin a tag and note the version you are on.

## Contributing and security

- Contributions: see [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Reporting a vulnerability in this repository's own content: see
  [`SECURITY.md`](SECURITY.md).
- Note the distinction: this repo defines an *audit skill*; `SECURITY.md` covers
  reporting bugs in the skill itself, not findings the skill produces.

## License

MIT — see [`LICENSE`](LICENSE).
