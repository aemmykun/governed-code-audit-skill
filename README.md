# Governed Code Audit Skill

A portable, read-only instruction package for evidence-backed code review.
Review security, correctness, maintainability, architectural conformance,
compliance, and AI-agent governance within an explicitly authorized scope.

The skill runs inside a host framework (CI pipeline, agent orchestrator,
policy engine) that owns identity, permissions, and enforcement. The skill
itself only analyzes and reports — its output is structured findings for
human review, never code changes and never a gate decision.

## What is included

- `SKILL.md`: portable agent instructions — the normative contract.
- `schema/audit-report.schema.json`: a strict JSON Schema for report structure.
- `examples/`: synthetic request and report examples (single-scope and
  multi-scope).
- `docs/`: context requirements, security boundaries, and integration guidance.
- `tests/`: contract checks and synthetic fixtures; not an audit engine.

## What is not included

No autonomous auditor, scanner installation, hosting service, repository
connector, permission enforcement, signing service, immutable log, or
merge/release control is implemented. No vendor-specific or private
organizational policy is bundled. Instructions are not a security boundary
and cannot make an unsafe host safe.

## Scope at a glance

What this skill is: an instruction contract that makes an AI agent audit code
systematically — a way of working and a report format, not a program.

Scopes it can audit (each requested scope is assessed independently):

- `security` — exposed secrets, injection, authn/authz flaws, cryptographic
  misuse, insecure logging
- `maintainability` — complexity, duplication, dead code, error handling,
  readability
- `architecture` — boundary violations, dependency direction, module
  separation, data-flow integrity
- `compliance` — PII handling, audit logging, retention, policy alignment
- `agent_governance` — the differentiator: authority, tool permissions,
  prompt-injection surface, cross-tenant isolation, provenance, and audit
  logging of AI agents

Rules that set it apart from a linter:

- **Read-only** — never modifies or executes the target code.
- **Fail-closed** — missing required context blocks that scope; nothing is
  guessed.
- **Three independent axes per finding** — severity (impact if true),
  confidence (how likely true), verification status (what proof exists).
- **No release-gate decisions** — findings are recommendations for human
  review; merge/release enforcement belongs to an external policy layer.
- **Honest provenance** — never fabricates hashes, signatures, or tool runs.

Not covered: no bundled scanner, CLI, or runtime; not an enforcement tool;
not a certification. You bring your own agent host and enforcement.

## Quick start

```sh
git clone https://github.com/aemmykun/governed-code-audit-skill.git
cd governed-code-audit-skill
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v   # 10 contract tests
python tests/validate_repo.py             # packaging + mock-data checks
```

Then read `SKILL.md` (the contract), look at `examples/` for a request and
report, and see `docs/integrations.md` plus
`examples/ci-pr-audit.example.yml` for wiring it into your own pipeline.

## Use the skill

1. Select an agent host approved to process the target source code.
2. Configure read-only target access and an explicit repository/scope allowlist.
3. Give the agent `SKILL.md` and the referenced documentation. Loading a
   Markdown file does not automatically install a skill; registration depends
   on the host.
4. Supply an authorized snapshot and a request following the example YAML.
5. Collect the JSON report and review all limitations and blocked scopes.
6. Have a human review consequential findings. Enforce any gates outside the
   model (see [`docs/integrations.md`](docs/integrations.md)).

Do not execute the target repository, its tests, build scripts, hooks, or
tools supplied by it. Existing approved test results may be reviewed as
evidence.

## Design principles

- **The framework enforces security; the model advises.** Authorization,
  tenant isolation, tool permissions, and approvals belong to deterministic
  services, not prompt instructions.
- **Fail closed.** Missing required context produces `incomplete` or
  `rejected`, never a guess.
- **Severity, confidence, and verification are independent.** A critical
  finding with low confidence triggers human review; only a confirmed finding
  is material an external gate might consume.
- **Honest provenance.** The schema forbids fake signatures (`signed` is
  always `false` here) and any release-gate state other than `not_evaluated`.
- **Redact before reporting.** Evidence quotes enough code to prove an issue
  without reproducing live secrets, tokens, or personal data.

## Repository layout

```
├── SKILL.md                          # Agent instructions — the normative contract
├── schema/
│   ├── audit-request.schema.json     # Locked host request (commit, digest, scopes, context, permissions)
│   └── audit-report.schema.json      # Strict JSON Schema (Draft 2020-12)
├── examples/
│   ├── audit-request.example.yaml
│   ├── audit-report.example.json         # single-scope report
│   ├── audit-report.multi-scope.example.json  # multi-scope report over the fixtures
│   ├── audit-report.example.md           # human-readable rendering
│   └── ci-pr-audit.example.yml           # self-contained CI demo: lock → sandbox → bind → gate
├── docs/
│   ├── context-contract.md           # Required inputs, trust levels, fail-closed rules
│   ├── security-model.md             # Threat model, agent attack vectors, limitations
│   ├── integrations.md               # Optional patterns: CI, policy engines, audit logs
│   ├── evaluation.md                 # How to evaluate an implementation (not a certification)
│   └── verification.md               # What is proven, how to reproduce it, honest gaps
├── tools/
│   ├── validate_report.py            # Host-callable schema + contract-invariant validator
│   ├── run_audit_sandbox.sh          # OS-enforced read-only jail (no net, noexec snapshot)
│   ├── reference_agent.py            # Real deterministic agent for the demo pipeline
│   └── adversarial_demo.py           # Attack battery: runtime escapes + dishonest reports
├── tests/
│   ├── test_contract.py              # Contract + request-binding + sandbox tests (unittest)
│   ├── validate_repo.py              # Packaging checks: parse, schema, mock data
│   └── fixtures/                     # Mock vulnerable/clean code + report fixtures
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── requirements-dev.txt
├── .gitignore
├── LICENSE                           # MIT
└── .github/workflows/
    ├── check.yml                     # CI: lint, contract tests, repo checks, secret scan
    └── governed-audit.yml            # Required check: sandboxed audit of the PR (pull_request_target)
```

## Validate the package

```sh
python -m venv .venv
# Linux/macOS; use .venv\Scripts\activate on Windows.
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tests/validate_repo.py
```

The contract tests check the schema, every bundled report, and the semantic
invariants (fail-closed scope resolution, honest provenance, no self-issued
gate decisions). They do not evaluate an AI model, prove audit quality, or
enforce runtime isolation.

## Live demo on this repository

The `governed-audit` required check runs the full pipeline
(lock → sandbox → bind → gate) on every pull request and is enforced by
branch protection on `main`:

- [PR #1](https://github.com/aemmykun/governed-code-audit-skill/pull/1) —
  clean example change; audit passed and the PR merged.
- [PR #2](https://github.com/aemmykun/governed-code-audit-skill/pull/2) —
  intentionally vulnerable example (`examples/planted/service.py`); the gate
  failed the check and branch protection blocks the merge. **Do not merge
  this PR** — it is the standing blocked-merge demonstration. Close it only
  if you no longer want the live example.

## Fork and customize

Fork this repository and replace the example policies with your own
versioned, approved policy pack. Keep local policies separate from the
portable core. Re-run contract tests after changes. A fork must not imply
certification, endorsement, or inherited access to the original author's
private services.

## Versioning

Versioned with git tags; `schema_version` inside the report schema tracks the
contract. Current release: **v0.3.0** — the contract may still evolve until
v1.0.0. See [`CHANGELOG.md`](CHANGELOG.md). If you fork or vendor this skill,
pin a tag and note the version you are on.

## Contributing and security

- Contributions: see [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Reporting a vulnerability in this repository's own content: see
  [`SECURITY.md`](SECURITY.md).

## License

MIT — see [`LICENSE`](LICENSE).
