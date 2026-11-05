"""Contract checks only; these do not invoke an agent or execute target code.

Invariants live in tools/validate_report.py — the same validator hosts run —
so these tests exercise the shipped implementation, not a parallel copy."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_report  # noqa: E402

SCHEMA = json.loads((ROOT / "schema/audit-report.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
VALIDATOR_CLI = ROOT / "tools" / "validate_report.py"

REPORTS = (
    "examples/audit-report.example.json",
    "examples/audit-report.multi-scope.example.json",
    "tests/fixtures/incomplete-report.json",
    "tests/fixtures/rejected-report.json",
)


def load(path):
    return json.loads((ROOT / path).read_text())


def validate(report):
    VALIDATOR.validate(report)
    errors = []
    validate_report.check(report, errors)
    assert not errors, "; ".join(errors)


def run_cli(*argv):
    return subprocess.run(
        [sys.executable, str(VALIDATOR_CLI), *argv],
        capture_output=True, text=True,
    )


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.example = load("examples/audit-report.example.json")

    def test_schema_is_valid(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_valid_examples(self):
        for path in REPORTS:
            with self.subTest(path=path):
                validate(load(path))

    def test_valid_examples_via_cli(self):
        """Every bundled report passes the shipped validator CLI."""
        for path in REPORTS:
            with self.subTest(path=path):
                r = run_cli(str(ROOT / path), "--snapshot-dir", str(ROOT))
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fixture_digests_match_bytes(self):
        for path in REPORTS:
            report = load(path)
            for item in report["provenance"]["input_digests"]:
                with self.subTest(report=path, digest=item["path"]):
                    self.assertEqual(
                        hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest(),
                        item["sha256"],
                    )

    def test_missing_evidence_is_rejected(self):
        bad = copy.deepcopy(self.example)
        del bad["findings"][0]["evidence"]
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_unresolved_scope_cannot_be_complete(self):
        bad = copy.deepcopy(self.example)
        bad["scope"]["blocked"] = ["maintainability"]
        with self.assertRaises(AssertionError):
            validate(bad)

    def test_incomplete_requires_blocked_scope(self):
        bad = copy.deepcopy(self.example)
        bad["audit_status"] = "incomplete"
        with self.assertRaises(AssertionError):
            validate(bad)

    def test_rejected_cannot_contain_findings(self):
        bad = copy.deepcopy(self.example)
        bad["audit_status"] = "rejected"
        with self.assertRaises(AssertionError):
            validate(bad)

    def test_automatic_gate_is_not_a_core_output(self):
        bad = copy.deepcopy(self.example)
        bad["release_gate"]["state"] = "approve"
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_fake_signature_is_not_allowed(self):
        bad = copy.deepcopy(self.example)
        bad["provenance"]["signed"] = True
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_reversed_lines_are_rejected(self):
        bad = copy.deepcopy(self.example)
        bad["findings"][0]["evidence"]["line_start"] = 10
        with self.assertRaises(AssertionError):
            validate(bad)


class BindingTests(unittest.TestCase):
    """Host-side binding: request, commit, and snapshot checks via the CLI."""

    def write_report(self, report):
        f = tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False)
        json.dump(report, f)
        f.close()
        return f.name

    def test_dropped_requested_scope_fails(self):
        """A report that silently drops a requested scope must not pass."""
        r = run_cli(
            str(ROOT / "examples/audit-report.example.json"),
            "--requested-scopes", "security,maintainability",
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("scope.requested", r.stdout)

    def test_matching_requested_scope_passes(self):
        r = run_cli(
            str(ROOT / "examples/audit-report.example.json"),
            "--requested-scopes", "maintainability",
        )
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_wrong_commit_fails(self):
        r = run_cli(
            str(ROOT / "examples/audit-report.example.json"),
            "--expect-commit", "0" * 40,
        )
        self.assertNotEqual(r.returncode, 0)

    def test_path_traversal_fails(self):
        bad = copy.deepcopy(load("examples/audit-report.example.json"))
        bad["provenance"]["input_digests"] = [
            {"path": "../etc/passwd", "sha256": "0" * 64}
        ]
        with tempfile.TemporaryDirectory() as d:
            r = run_cli(self.write_report(bad), "--snapshot-dir", d)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("escapes snapshot dir", r.stdout)

    def test_absolute_path_fails(self):
        bad = copy.deepcopy(load("examples/audit-report.example.json"))
        bad["provenance"]["input_digests"] = [
            {"path": "/etc/passwd", "sha256": "0" * 64}
        ]
        with tempfile.TemporaryDirectory() as d:
            r = run_cli(self.write_report(bad), "--snapshot-dir", d)
        self.assertNotEqual(r.returncode, 0)

    def test_evidence_beyond_file_fails(self):
        bad = copy.deepcopy(load("examples/audit-report.example.json"))
        bad["findings"][0]["evidence"]["line_end"] = 99999
        r = run_cli(self.write_report(bad), "--snapshot-dir", str(ROOT))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("past end", r.stdout)


def locked_request(**over):
    req = {
        "request_version": "0.2.0", "audit_id": "t-1",
        "source": {"repository": "o/r", "commit_sha": "0" * 40,
                   "snapshot_sha256": "0" * 64},
        "requested_scopes": ["maintainability"],
        "context": {}, "agent_permissions": {
            "read_snapshot": True, "write_repository": False,
            "execute_target_code": False, "network": False,
            "disclose_externally": False}}
    req.update(over)
    return req


class RequestBindingTests(unittest.TestCase):
    """--request binds the report to the locked audit request."""

    def write(self, obj):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(obj, f)
        f.close()
        return f.name

    def matching_report(self):
        r = load("examples/audit-report.example.json")
        r["source"]["commit_sha"] = "0" * 40
        return self.write(r)

    def test_matching_request_passes(self):
        r = run_cli(self.matching_report(),
                    "--request", self.write(locked_request(
                        audit_id="example-maintainability-001")))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_audit_id_mismatch_fails(self):
        r = run_cli(self.matching_report(),
                    "--request", self.write(locked_request()))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("audit_id", r.stdout)

    def test_scope_mismatch_fails(self):
        r = run_cli(self.matching_report(),
                    "--request", self.write(locked_request(
                        audit_id="example-maintainability-001",
                        requested_scopes=["security", "maintainability"])))
        self.assertNotEqual(r.returncode, 0)

    def test_commit_mismatch_fails(self):
        r = run_cli(self.matching_report(),
                    "--request", self.write(locked_request(
                        audit_id="example-maintainability-001",
                        source={"repository": "o/r",
                                "commit_sha": "f" * 40,
                                "snapshot_sha256": "0" * 64})))
        self.assertNotEqual(r.returncode, 0)


class SandboxTests(unittest.TestCase):
    """OS-enforced read-only runtime — attacks fail inside the jail."""

    SANDBOX = ROOT / "tools" / "run_audit_sandbox.sh"

    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.mkdtemp(prefix="sbx-")
        for d in ("snap", "ctx", "out"):
            Path(cls.work, d).mkdir()
        Path(cls.work, "snap/evil.sh").write_text("#!/bin/sh\necho RAN\n")
        Path(cls.work, "snap/data.txt").write_text("evidence\n")

    def in_jail(self, cmd):
        return subprocess.run(
            ["bash", str(self.SANDBOX), f"{self.work}/snap",
             f"{self.work}/ctx", f"{self.work}/out", "--",
             "sh", "-c", cmd],
            capture_output=True, text=True)

    def assert_jail_ran(self, r):
        # Every denial test must prove the jail actually executed — a dead
        # sandbox produces empty output and would vacuously "pass" them.
        self.assertIn(
            "ALIVE", r.stdout,
            f"sandbox did not run (rc={r.returncode}): {r.stderr[:300]}")

    def test_no_network(self):
        r = self.in_jail(
            "echo ALIVE; curl -sm2 -o /dev/null https://github.com && echo NET-OK")
        self.assert_jail_ran(r)
        self.assertNotIn("NET-OK", r.stdout + r.stderr)

    def test_snapshot_read_only(self):
        r = self.in_jail("echo ALIVE; touch /snapshot/x && echo WROTE")
        self.assert_jail_ran(r)
        self.assertNotIn("WROTE", r.stdout + r.stderr)

    def test_target_not_executable(self):
        r = self.in_jail("echo ALIVE; /snapshot/evil.sh && echo RAN")
        self.assert_jail_ran(r)
        self.assertNotIn("RAN", r.stdout + r.stderr)

    def test_no_reads_outside_authorized(self):
        r = self.in_jail("echo ALIVE; ls /home /root && echo SAW")
        self.assert_jail_ran(r)
        self.assertNotIn("SAW", r.stdout + r.stderr)

    def test_workspace_writable_and_snapshot_readable(self):
        r = self.in_jail(
            "cat /snapshot/data.txt; touch /workspace/o && echo OK")
        self.assertIn("evidence", r.stdout)
        self.assertIn("OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
