# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project is
versioned with git tags.

## [Unreleased]

## [0.1.0] — 2026-10-31

Initial public release.

### Added

- `SKILL.md` — the governed code audit contract: audit scopes, hard
  constraints, fail-closed context requirements, the
  severity/confidence/verification taxonomy, and the report format.
- `schema/audit-report.schema.json` — JSON Schema (Draft 2020-12) for
  machine-readable audit reports.
- `docs/context-contract.md` — typed input contract with trust levels and
  per-scope fail-closed rules.
- `docs/security-model.md` — threat model, agent attack vectors, and
  governance principles.
- `docs/integrations.md` — optional integration patterns for CI, policy
  engines, and audit logging.
- `examples/` — a complete mock audit request and audit report.
- `tests/fixtures/` — mock vulnerable, clean, and incomplete-context fixtures
  for regression testing.
- `CONTRIBUTING.md`, `SECURITY.md`, MIT `LICENSE`.
- `.github/workflows/check.yml` — CI: markdown lint, YAML/JSON validation,
  schema validation, mock-data enforcement, and secret scanning.
