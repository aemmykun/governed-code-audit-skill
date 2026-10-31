# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project is
versioned with git tags.

## [Unreleased]

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

## [0.1.0] — 2026-10-31

Initial public release.

### Added

- `SKILL.md` — the governed code audit contract.
- `schema/audit-report.schema.json` — JSON Schema for audit reports.
- `docs/` — context contract, security model, integrations.
- `examples/`, `tests/fixtures/` — synthetic examples and mock fixtures.
- `CONTRIBUTING.md`, `SECURITY.md`, MIT `LICENSE`.
- `.github/workflows/check.yml` — CI checks.
