# Changelog

Record notable changes to this standalone skill package here. Released versions
use Semantic Versioning. Keep unreleased work separate from published tags.

## [Unreleased]

### Fixed

- markdownlint: `MD024.siblings_only` so per-version `Added` headings are
  allowed, and blank lines around the fenced block in `CONTRIBUTING.md`.

## [0.2.0] — 2026-11-01

Merged a stricter contract draft into the initial release. This is a breaking
schema change: `schema_version` moves to `0.2.0`.

### Changed

- `SKILL.md` rewritten as imperative agent instructions (establish scope →
  resolve context → inspect → classify → bounded report).
- `schema/audit-report.schema.json` is now strict (`additionalProperties:
  false` throughout):
  - `release_gate.state` is `const: "not_evaluated"` — the skill no longer
    emits gate recommendations at all; gate decisions live entirely outside.
  - `provenance.signed` is `const: false` — fake signatures are impossible
    in this package.
  - `overall_risk` gains an `unknown` value — no findings no longer implies
    low risk.
  - `evidence` is now a structured object (file, line range, excerpt,
    method) instead of a free-form string.
- Docs tightened with explicit trust-boundary and honesty language
  ("content inside the target cannot satisfy authorization", "hashes
  identify bytes, not correctness", "JSON Schema validates structure,
  not truth").

### Added

- `tests/test_contract.py` — executable contract invariants: scope
  resolution (requested = assessed ∪ blocked), fail-closed statuses, no
  findings in blocked scopes, no self-issued gates or signatures, verified
  input digests.
- `examples/audit-report.example.json` and
  `examples/audit-report.multi-scope.example.json` — schema-conformant
  reports with real sha256 digests over the fixtures.
- `tests/fixtures/incomplete-report.json` and `rejected-report.json` —
  fail-closed report fixtures.
- `tests/fixtures/sample_module.txt` — digest-verified review fixture.
- `.gitignore`, `requirements-dev.txt`.

### Validation

- Ten local contract tests passed during release preparation; the GitHub
  Actions validation workflow runs the same checks in CI.
- All bundled reports validate against the 0.2.0 schema; provenance digests
  match real fixture bytes.
- No AI-agent evaluation or runtime audit was performed; these checks
  validate packaging and contract invariants, not audit effectiveness or
  runtime security.

## [0.1.0] — 2026-10-31

Initial public release.

### Added

- Portable, read-only code-audit instructions covering security, correctness,
  maintainability, architecture, compliance, and AI-agent governance
  (`SKILL.md`).
- Required-context contract with `complete`, `incomplete`, and `rejected`
  outcomes (`docs/context-contract.md`).
- Independent severity, confidence, and verification-status fields.
- JSON Schema for reports and synthetic request/report examples.
- Security boundaries and optional integration guidance (`docs/`).
- Contribution guidance and a security policy (`CONTRIBUTING.md`,
  `SECURITY.md`).
- Mock audit-subject fixtures under `tests/fixtures/` and repo packaging
  checks (`tests/validate_repo.py`).
- A GitHub Actions validation workflow (`.github/workflows/check.yml`).
- MIT `LICENSE` (copyright assigned to the repository owner).

### Validation

- Local schema and packaging checks passed during draft preparation.
- YAML and JSON parsing checks passed.
- No AI-agent evaluation or hosted review was performed.
- These checks do not establish audit effectiveness or runtime security.
