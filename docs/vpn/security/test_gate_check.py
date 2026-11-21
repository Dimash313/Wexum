"""Negative tests for metadata-only security release gates; no network or secrets."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from gate_check import REQUIRED_GATES, assess

MANIFEST_PATH = Path(__file__).with_name("release_gates.json")
SYNTHETIC_SHA = "a" * 40


def baseline() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def artificial_complete() -> dict:
    """Made-up records exercise the linter, NOT a real security attestation."""
    manifest = copy.deepcopy(baseline())
    manifest["target_sha"] = SYNTHETIC_SHA
    for gate in manifest["gates"]:
        gate["state"] = "attested"
        gate["evidence"] = [
            {"kind": "verification", "actor": "synthetic-tester",
             "url": "https://example.test/synthetic-test", "commit_sha": SYNTHETIC_SHA},
            {"kind": "independent_review", "actor": "synthetic-reviewer",
             "url": "https://example.test/synthetic-review", "commit_sha": SYNTHETIC_SHA},
        ]
    for finding in manifest["findings"]:
        finding["state"] = "mitigated"
    return manifest


class ReleaseManifestTests(unittest.TestCase):
    def test_baseline_is_well_formed_but_blocked(self):
        errors, blockers = assess(baseline())
        self.assertEqual([], errors)
        self.assertGreater(len(blockers), 0)
        self.assertTrue(any("SEC-CTRL-001" in x for x in blockers))

    def test_all_required_gates_present(self):
        self.assertEqual(REQUIRED_GATES,
                         {g["id"] for g in baseline()["gates"]})

    def test_synthetic_attested_metadata_is_structurally_complete_only(self):
        errors, blockers = assess(artificial_complete())
        self.assertEqual(([], []), (errors, blockers))

    def test_missing_required_gate_rejected(self):
        obj = baseline()
        obj["gates"].pop()
        self.assertTrue(any("missing mandatory gates" in x for x in assess(obj)[0]))

    def test_duplicate_gate_rejected(self):
        obj = baseline()
        obj["gates"].append(copy.deepcopy(obj["gates"][0]))
        self.assertTrue(any("duplicate gate" in x for x in assess(obj)[0]))

    def test_invalid_state_cannot_pass(self):
        obj = baseline()
        obj["gates"][0]["state"] = "ready"
        self.assertTrue(any("invalid state" in x for x in assess(obj)[0]))

    def test_attestation_without_evidence_rejected(self):
        obj = baseline()
        obj["target_sha"] = SYNTHETIC_SHA
        obj["gates"][0]["state"] = "attested"
        self.assertTrue(any("require verification" in x for x in assess(obj)[0]))

    def test_evidence_from_stale_commit_rejected(self):
        obj = artificial_complete()
        obj["gates"][0]["evidence"][0]["commit_sha"] = "b" * 40
        self.assertTrue(any("does not match target_sha" in x for x in assess(obj)[0]))

    def test_same_reviewer_as_submitter_rejected(self):
        obj = artificial_complete()
        obj["gates"][0]["evidence"][1]["actor"] = "synthetic-tester"
        self.assertTrue(any("must differ" in x for x in assess(obj)[0]))

    def test_missing_target_sha_rejected_when_attested(self):
        obj = artificial_complete()
        obj["target_sha"] = None
        self.assertTrue(any("requires a target_sha" in x for x in assess(obj)[0]))

    def test_open_high_finding_blocks_even_with_all_gates_attested(self):
        obj = artificial_complete()
        obj["findings"][0]["state"] = "open"
        errors, blockers = assess(obj)
        self.assertEqual([], errors)
        self.assertTrue(any("unresolved high" in x for x in blockers))

    def test_malformed_findings_rejected(self):
        obj = baseline()
        obj["findings"] = {"not": "an array"}
        self.assertTrue(any("findings must be an array" in x for x in assess(obj)[0]))

    def test_invalid_root_rejected(self):
        self.assertTrue(assess([])[0])

    def test_blocked_gate_cannot_claim_accepted_evidence(self):
        obj = artificial_complete()
        obj["gates"][0]["state"] = "blocked"
        self.assertTrue(any("may not claim accepted evidence" in x for x in assess(obj)[0]))

    def test_extra_critical_finding_blocks(self):
        obj = artificial_complete()
        obj["findings"].append({
            "id": "SEC-OPS-003", "severity": "critical", "state": "open",
            "owner": "#8", "source": "https://example.test/synthetic",
            "description": "Synthetic critical issue to check blocking"
        })
        errors, blockers = assess(obj)
        self.assertEqual([], errors)
        self.assertTrue(any("SEC-OPS-003" in x for x in blockers))


if __name__ == "__main__":
    unittest.main()
