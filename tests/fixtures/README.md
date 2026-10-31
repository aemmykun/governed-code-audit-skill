# Test Fixtures

Mock code and inputs for regression-testing a governed-code-audit
implementation. **Every file here is fictional** — invented names, fake
credentials marked `FAKE`/`EXAMPLE`, `example.*` domains only.

Each fixture directory contains the code or input under audit plus an
`expected.yaml` describing what a conforming audit should produce: the expected
findings (by severity and category) or the expected fail-closed status.

| Fixture | Exercises |
| --- | --- |
| `hardcoded-secret/` | Secret detection; redaction in evidence |
| `missing-authorization/` | Authorization review on a privileged action |
| `cross-tenant-access/` | Tenant-isolation / retrieval-scope checks |
| `prompt-injection-tool-chain/` | Tool-argument validation, tool chaining |
| `incomplete-context/` | Fail-closed behavior on missing required context |
| `clean/` | No false positives on well-formed code |

CI verifies these files parse and contain only mock data — see
`.github/workflows/check.yml`.
