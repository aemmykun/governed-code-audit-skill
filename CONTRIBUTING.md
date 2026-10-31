# Contributing

Thanks for helping improve the governed code audit skill. This document covers
the ground rules; the CI workflow in `.github/workflows/check.yml` enforces most
of them automatically.

## What belongs here

This repository is a **specification and instruction package**, not an
implementation. Do not contribute private source, credentials, tenant records,
internal policy packs, or confidential findings. Good contributions:

- Clarifications or corrections to the skill contract in `SKILL.md`.
- Improvements to `schema/audit-report.schema.json` (with matching example and
  test updates when the shape changes).
- Additional mock fixtures under `tests/fixtures/` that exercise a rule —
  including negative cases: missing context, unauthorized scope, invalid
  reports.
- Documentation improvements in `docs/`.
- Neutral, reusable integration recipes in `docs/integrations.md`.

Out of scope: organization-specific policies, real deployment configs,
vendor-specific wiring that cannot generalize, and any content copied from a
private codebase.

## Ground rules

1. **Mock data only.** Examples and fixtures must use invented names,
   `example.com`/`example.org`/`example.net` domains, and fake identifiers
   (e.g. `EXAMPLE_FAKE_KEY_DO_NOT_USE`). Never commit real repository names,
   emails, organization names, code, or credentials. `tests/validate_repo.py`
   checks this.
2. **No secrets, ever.** Anything that looks like a live credential will fail
   the secret-scanning check and must be removed from history before merging.
3. **Keep the skill honest.** The skill never issues a release-gate decision
   (`release_gate.state` stays `not_evaluated`) and never claims a signature
   (`provenance.signed` stays `false`). Do not weaken these constraints.
4. **Fail-closed stays.** Do not weaken the context contract or the
   fail-closed behavior without a clear rationale in the PR discussion.
5. **Keep tests honest.** Distinguish tested package behavior from model
   quality or runtime enforcement. Contract tests validate structure and
   invariants; they do not prove an agent audits well.

## Workflow

1. Fork the repository and create a branch.
2. Make your change; keep edits minimal and in the existing style.
3. Explain the intended behavior and affected trust boundary in the PR.
4. Update examples, schema, tests, and version identifiers **together** when
   the contract changes.
5. Run the checks locally:
   ```sh
   python -m pip install -r requirements-dev.txt
   python -m unittest discover -s tests -v
   python tests/validate_repo.py
   ```
6. Open a pull request describing the change and its motivation. If it changes
   the contract or schema, say so explicitly in the title.

## Versioning and changelog

- Contract/schema changes bump `schema_version` in
  `schema/audit-report.schema.json`, the version in `SKILL.md` frontmatter,
  and every example/fixture report, plus a `CHANGELOG.md` entry.
- Pre-1.0, minor bumps may include breaking schema changes; after 1.0 the
  schema follows semver.

## Reporting security issues

Do not open public issues for vulnerabilities in this repository's content.
See [`SECURITY.md`](SECURITY.md).
