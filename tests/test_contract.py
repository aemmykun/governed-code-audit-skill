"""Contract checks only; these do not invoke an agent or execute target code."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema/audit-report.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)

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
    scope = report["scope"]
    requested, assessed, blocked = (set(scope[k]) for k in ("requested", "assessed", "blocked"))
    assert assessed.isdisjoint(blocked), "Assessed and blocked must be disjoint"
    assert requested == assessed | blocked, "Resolve every requested scope exactly once"
    if report["audit_status"] == "complete":
        assert not blocked and not report["missing_context"], "Complete cannot conceal context gaps"
    if report["audit_status"] == "incomplete":
        assert blocked, "Incomplete must identify a blocked scope"
    if report["audit_status"] == "rejected":
        assert not assessed and not report["findings"], "Rejected means no assessment"
        assert report["overall_risk"] == "unknown", "Rejected cannot establish risk"
    for finding in report["findings"]:
        assert finding["category"] in assessed, "Cannot report assessed findings in a blocked scope"
        ev = finding["evidence"]
        assert ev["line_end"] >= ev["line_start"], "Invalid evidence line range"
        assert ev["snapshot_id"] == report["source"]["snapshot_id"], "Snapshot mismatch"


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.example = load("examples/audit-report.example.json")

    def test_schema_is_valid(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_valid_examples(self):
        for path in REPORTS:
            with self.subTest(path=path):
                validate(load(path))

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


if __name__ == "__main__":
    unittest.main()
