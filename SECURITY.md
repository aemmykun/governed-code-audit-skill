# Security Policy

This file covers **the security of this repository's own content** — the skill
specification, schema, examples, fixtures, docs, and CI workflow. It is not
about vulnerabilities that the audit skill may find in *other* codebases.

## Scope

In scope:

- Real credentials, personal data, or proprietary code accidentally committed
  to this repository.
- Examples or fixtures that contain exploitable patterns presented as safe.
- CI workflow misconfigurations that could execute untrusted code from forks
  or leaks repository secrets.
- Schema or contract wording that materially weakens the fail-closed or
  read-only guarantees in a way that could mislead adopters.

Out of scope:

- Vulnerabilities this skill is designed to detect in third-party code —
  those belong to the operators who run the skill.
- Issues in tools merely referenced by the docs (report those upstream).

## Reporting

Please do **not** open a public GitHub issue for security-sensitive reports.

Preferred options, in order:

1. **GitHub private vulnerability reporting** — use the repository's
   "Report a vulnerability" button under the Security tab.
2. **Email** — contact the maintainers at `security@example.org`
   (replace with the maintainer contact once the project names one). Include
   the affected file(s), a description, and whether the content has already
   been exposed publicly.

Include in your report: affected file path(s) or commit, why it matters, and
suggested remediation. We aim to acknowledge within 7 days.

## Handling of exposed secrets

If a real credential is found in this repository's history:

1. The secret is revoked/rotated first, then removed from history.
2. The fix is noted in the changelog without reproducing the secret.
3. The reporter is credited (unless they prefer otherwise).

## Supported versions

Only the latest tagged release is maintained. Check `CHANGELOG.md` for the
current version.
