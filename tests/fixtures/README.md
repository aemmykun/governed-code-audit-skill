# Test Fixtures

Mock code and inputs for regression-testing a governed-code-audit
implementation. **Every file here is fictional** — invented names, fake
credentials marked `FAKE`/`EXAMPLE`, `example.*` domains only.

Two kinds of fixtures:

**Audit-subject fixtures** (code under audit + expected outcome):

| Fixture | Exercises |
| --- | --- |
| `hardcoded-secret/` | Secret detection; redaction in evidence |
| `missing-authorization/` | Authorization review on a privileged action |
| `cross-tenant-access/` | Tenant-isolation / retrieval-scope checks |
| `prompt-injection-tool-chain/` | Tool-argument validation, tool chaining |
| `incomplete-context/` | Fail-closed behavior on missing required context |
| `clean/` | No false positives on well-formed code |
| `sample_module.txt` | Digest-verified file used by the examples and contract tests |

Each scenario directory contains the code or input under audit plus an
`expected.yaml` describing what a conforming audit should produce.

**Report fixtures** (complete report documents validated against the schema):

| Fixture | Exercises |
| --- | --- |
| `incomplete-report.json` | `incomplete` status with a blocked scope and `missing_context` |
| `rejected-report.json` | `rejected` status — no findings, `overall_risk: unknown` |

`tests/test_contract.py` validates every report against the schema and checks
the contract invariants (fail-closed scope resolution, honest provenance, no
self-issued gate decisions). `tests/validate_repo.py` checks packaging: all
files parse, reports validate against the schema, and everything is mock data.
