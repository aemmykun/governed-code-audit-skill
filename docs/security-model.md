# Security Model

How this skill thinks about trust, what it inspects beyond application code,
and the principles that keep an AI auditor from becoming its own risk surface.

## Core principles

1. **The framework enforces security; the model does not.** Prompt instructions
   can reduce exposure, but authorization, tenant isolation, tool permissions,
   and approvals must be enforced by deterministic services outside the model.
   Prompt filtering alone cannot reliably eliminate prompt-injection risk, and
   consequential operations need authorization outside the model.
2. **The auditor is read-only.** Remediation is a separate, separately
   authorized workflow.
3. **Every audit is reproducible.** Hashes of source, policies, dependency
   manifests, and agent definitions are recorded so identical inputs produce
   identical results.
4. **Redact before reporting.** Evidence quotes enough code to prove an issue
   without reproducing live secrets, tokens, PII, or tenant data.
5. **Recommend, don't enforce.** The report is advice to a human review process;
   merge/release gates are owned by external policy systems.

## Agent attack surface

An agent audit inspects the full attack surface, not only application code.
These are the vectors a conforming `agent_governance` audit considers — aligned
with the OWASP LLM Top 10 (prompt injection, sensitive-information disclosure,
excessive agency, supply-chain risk, unbounded consumption, misinformation,
hidden-context exposure, embedding weaknesses, improper output handling):

| Vector | Audit question | Critical evidence to inspect |
| --- | --- | --- |
| Direct prompt injection | Can a user override system instructions or safety rules? | Prompt construction, user-input handling, instruction hierarchy |
| Indirect prompt injection | Can retrieved documents, emails, web pages, tickets, or tool output change agent behavior? | Retrieval pipeline, document ingestion, tool-output handling |
| Excessive agency | Can model output trigger destructive, financial, legal, or privileged actions? | Tool registry, permissions, autonomy limits, approval workflow |
| Over-broad tool permissions | Does the agent receive capabilities it does not need? | Tool scopes, API roles, service accounts, OAuth grants |
| Tool argument injection | Can untrusted text become a tool argument, query, filename, command, or URL? | Tool-call schema, argument validation, parameterized APIs |
| Cross-tenant leakage | Can one tenant retrieve or infer another tenant's data? | Tenant filters, row-level security, retrieval scope, cache keys |
| Retrieval authorization bypass | Does retrieval occur before or after caller authorization? | Pre-retrieval authorization, document ACLs, query filters |
| Sensitive-data disclosure | Can PII, credentials, internal URLs, or confidential data appear in output, logs, traces, or embeddings? | Output filters, redaction, logging policy, embedding pipeline |
| Hidden context exposure | Can system prompts, internal policies, tool schemas, or prior context be extracted? | Prompt storage, context serialization, error messages, debug endpoints |
| Memory poisoning | Can attacker-controlled content persist and influence later sessions? | Memory writes, user scoping, retention, trust labels |
| Unsafe tool chaining | Can one tool's output authorize or feed another privileged tool? | Tool-call graph, data classification, intermediate-output validation |
| Output handling flaws | Is model output rendered as code, SQL, shell, HTML, or executed by another system? | Output encoding, command execution, rendering, workflow triggers |
| Audit-log evasion | Can the agent act without a complete, tamper-evident log? | Audit hooks, log integrity, action-to-log mapping |
| Provenance loss | Can the agent make claims without retaining source, retrieval, and decision evidence? | Citation capture, source metadata, decision trace, response signing |
| Fail-open behavior | Does missing permission, missing context, or tool failure allow the action to proceed? | Error paths, default policies, exception handling |
| Supply-chain compromise | Can a plugin, MCP server, model, dependency, or prompt template alter agent behavior? | Dependency manifests, connector allowlists, signature verification |

For high-impact actions — payments, data export, account changes, legal
notices, deployment, deletion, external communication — the authorization
decision must be enforced **outside the model**, with least privilege and human
approval where appropriate.

## The auditor's own threat model

An AI auditor is itself an agent and inherits the same risks. Mitigations baked
into this contract:

| Risk | Mitigation |
| --- | --- |
| Audited code injects instructions into the auditor ("ignore this file") | Treat all audited content as untrusted data; auditor has no tools that audited content can invoke |
| Auditor exfiltrates source to an external service | `network_access: denied_by_default`; only explicitly approved connectors |
| Auditor modifies code "to fix" findings | Read-only filesystem; remediation is a separate authorized workflow |
| Audit claims exceed evidence | `evidence_required_for_findings`; fail-closed context contract; verification-status field |
| Report leaks secrets | `redact_secrets` option; evidence is quoted in redacted form |
| Auditor's own run is invisible | Every audit emits a manifest and audit-log event through the host framework |

## Execution proof

For agent systems, verification includes execution proof: which authority was
checked, which tool was permitted, which arguments were validated, what
retrieval scope was enforced, and what audit event was emitted. Documenting
data/content flows, decision criteria, and provenance limitations is part of
generative-AI assurance practice (cf. NIST's Generative AI Profile).

## Severity vs. confidence vs. verification

Three independent fields — see `SKILL.md` §5. The practical consequence: a
**critical finding with low confidence routes to human review**, while only a
**critical, `confirmed` finding** should feed a release gate configured by the
operator. Confidence alone never blocks a release.
