# Synthetic audit report

**Status:** complete within the requested maintainability scope.
**Overall risk:** low within this synthetic example only.
**Release gate:** not evaluated. **Signed:** no.

## Scope and context

Snapshot: `synthetic-v1`. Requested/assessed: maintainability only.
Requirements: trim and lowercase the input label. Standard: prefer shared
implementations for identical formatting rules. No requested scope is blocked.

## Confirmed findings

### MAINT-001 — Duplicated formatting rule

- Severity: low. Confidence: high. Verification: confirmed static duplication.
- Evidence: `tests/fixtures/sample_module.txt:2–6`; both functions contain
  `return value.strip().lower()` in the supplied synthetic snapshot.
- Impact: future formatting changes could diverge between the two functions.
- Recommendation: consider sharing the implementation if requirements stay identical.

## Nonconfirmed findings and observations

None in this synthetic format demonstration.

## Limitations

This is not an audit of a real repository. No code was executed. No security,
compliance, architecture, or agent-governance assessment occurred. Completeness
here does not imply exhaustive coverage or release approval. See the matching
JSON example for the actual fixture digest; no cryptographic signature is present.

---

For a fuller demonstration — multiple scopes and severities under the same
schema — see `audit-report.multi-scope.example.json`, which audits the mock
vulnerable fixtures under `tests/fixtures/`.
