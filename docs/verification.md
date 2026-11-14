# Verification — what is proven, how to reproduce it

This repo separates three claims and verifies each **by running it**, not by
asserting it. Reproduce everything below on any Linux host with Python 3.10+
and `unshare` (util-linux). No Docker, no root.

```sh
git clone https://github.com/aemmykun/governed-code-audit-skill
cd governed-code-audit-skill
pip install -r requirements-dev.txt
```

## 1. Report validation (contract enforcement)

**Claim:** a report that violates the contract is rejected; a conforming one
passes. Schema + semantic invariants + host bindings.

```sh
python -m unittest discover -s tests -v     # 17 tests
python tests/validate_repo.py               # packaging checks
python tools/validate_report.py examples/audit-report.example.json \
    --snapshot-dir .
```

Covered: schema validity, scope resolution (`requested = assessed ∪ blocked`),
fail-closed statuses, evidence snapshot binding, honest provenance
(`release_gate.state` fixed `not_evaluated`, `signed` fixed `false`),
request binding (`--request`), commit binding (`--expect-commit`), snapshot
binding (`--snapshot-dir` — digests, file existence, line ranges, traversal
and symlink rejection).

## 2. Permission enforcement (runtime boundary)

**Claim:** inside `tools/run_audit_sandbox.sh` the agent cannot reach the
network, write the snapshot or host, read outside authorized inputs, or
execve() target code — the **OS** enforces it, the prompt never sees it.

```sh
python tools/adversarial_demo.py            # attack battery, exits non-zero if any boundary fails
```

Mechanism: unprivileged user namespace + fresh net/mount/pid/ipc namespaces +
chroot into a jail containing only `/snapshot` (ro, noexec, nosuid),
`/context` (ro, noexec), `/agent` (ro), `/workspace` (rw or 64 MiB tmpfs),
and ro-bind runtime dirs. On kernels that block unprivileged userns (e.g.
Ubuntu 24.04+ GitHub runners via AppArmor), the script falls back to
`sudo unshare` root namespaces and drops the agent to the invoking uid with
`setpriv` — same boundary, real-root namespaces.

**Honest gap — stated, not hidden:** `noexec` blocks `execve()` of files
under `/snapshot`. Feeding target code to an interpreter inside the jail
(`python3 /snapshot/x.py`) is indistinguishable from reading it at the
mount layer. Preventing it is a contract rule (SKILL.md), enforced by
review and by giving the jail only the agent's own bundle.

## 3. End-to-end pipeline

**Claim:** locked request → sandboxed agent → bound report → external gate
works as one pipeline. Proven two ways:

- `tools/reference_agent.py` — a real deterministic agent (not a mock) that
  runs inside the sandbox and emits schema-valid reports.
- `examples/ci-pr-audit.example.yml` — the same flow as a GitHub Actions
  workflow: host-measured snapshot digest, locked request, sandboxed agent,
  `validate_report.py --request --snapshot-dir`, then a policy gate where
  confirmed `high` **and** `critical` findings fail the check.

## 4. Detection quality — reported separately

Contract validity ≠ audit quality. The reference agent's two checks
(credential literals, retrieval-before-authorization) are smoke tests for the
pipeline, not a quality claim. Measuring recall / false-positive rate for a
real agent requires the adversarial fixture method in `docs/evaluation.md`.

## 5. Merge enforcement on real GitHub Actions

Proven on the repo itself. `.github/workflows/governed-audit.yml` runs on
`pull_request_target` (checked out at `pull_request.base.sha`, so the PR
cannot replace the workflow, validator, or policy), executes the same
pipeline as §3 inside the namespace sandbox, and posts the result as a check
run bound to the PR head SHA.

- **Passing PR:**
  [PR #1](https://github.com/aemmykun/governed-code-audit-skill/pull/1) —
  clean `examples/clean/cart.py`; sandbox ran, `findings=0`, report valid,
  `governed-audit` check **passed** on head SHA; merged.
- **Blocked PR:**
  [PR #2](https://github.com/aemmykun/governed-code-audit-skill/pull/2) —
  planted credentials + pre-authz retrieval in `examples/planted/service.py`;
  sandbox ran, `findings=2`, report valid, gate exited
  `2 high/critical finding(s) need human review`; `governed-audit` check
  **failed** on head SHA `c0ea237`.
- **Enforcement:** `main` branch protection requires the `governed-audit`
  status check, so PR #2 cannot merge until the findings are resolved. Run
  logs for both PRs are under the repo's
  [Actions](https://github.com/aemmykun/governed-code-audit-skill/actions)
  tab (`governed-audit` runs at the listed PR head SHAs).

Required-check binding note: GitHub evaluates the required check on the PR
head SHA; `pull_request_target` still records the check run on that head SHA,
which is what the merge box enforces — verified on both PRs.

## Not verified here

- A hosted LLM endpoint as the agent (the demo uses `reference_agent.py`;
  swap in your endpoint at the marked step — the host binding contract is
  identical)
- Detection quality of any specific model (see §4)
- Interpreted target-code execution inside the jail (see §2 honest gap)
