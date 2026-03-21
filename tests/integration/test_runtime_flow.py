from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_support import PROTOCOL_ROOT, load_example_manifest
from skill_se_kit.common import GovernanceError, load_json
from skill_se_kit.runtime.skill_runtime import SkillRuntime


class RuntimeFlowTests(unittest.TestCase):
    def _runtime(self, tmpdir: str, manifest_name: str = "standalone.manifest.json") -> SkillRuntime:
        runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
        runtime.workspace.bootstrap(load_example_manifest(manifest_name))
        return runtime

    def test_generate_proposal_apply_overlay_evaluate_promote_and_rollback_in_standalone(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir)
            runtime.register_verification_hook(
                "smoke",
                lambda proposal, context: {"status": "pass", "details": "integration smoke passed"},
            )
            candidate_manifest = runtime.version_store.load_active_manifest()
            candidate_manifest["version"] = "0.2.0"
            candidate_manifest["description"] = "Updated by integration test."
            candidate_manifest["metadata"]["change"] = "proposal"

            proposal = runtime.generate_proposal(
                change_summary="Bump version and update metadata",
                proposer_id="integration-test",
                target_manifest=candidate_manifest,
            )
            self.assertEqual(proposal["status"], "candidate")

            overlay = runtime.apply_overlay(
                overlay_type="annotation",
                operations=[{"op": "set", "path": "/metadata/overlay_note", "value": "active"}],
            )
            self.assertEqual(overlay["status"], "active")
            active_after_overlay = runtime.version_store.load_active_manifest()
            self.assertEqual(active_after_overlay["metadata"]["overlay_note"], "active")

            evaluation = runtime.evaluate_proposal(proposal["proposal_id"], source_origin="integration-test")
            self.assertEqual(evaluation["status"], "pass")
            self.assertIn("verification_receipt_id", evaluation)

            receipt = runtime.promote_candidate(proposal["proposal_id"])
            self.assertEqual(receipt["target_version"], "0.2.0")
            official_manifest = runtime.version_store.load_official_manifest()
            self.assertEqual(official_manifest["version"], "0.2.0")
            self.assertEqual(official_manifest["governance"]["official_status"], "official")
            self.assertEqual(official_manifest["metadata"]["official_scope"], "local")

            rollback = runtime.rollback(receipt["snapshot_id"])
            self.assertTrue(rollback["restored_active_manifest"])
            rolled_back_manifest = runtime.version_store.load_active_manifest()
            self.assertEqual(rolled_back_manifest["version"], "0.1.0")
            self.assertTrue((Path(tmpdir) / "audit" / "decision_logs").exists())
            self.assertTrue((Path(tmpdir) / "provenance" / "lineage").exists())

    def test_governed_mode_blocks_official_write_and_self_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir, "governed.manifest.json")
            manifest = runtime.version_store.load_active_manifest()
            with self.assertRaises(GovernanceError):
                runtime.version_store.write_official_manifest(manifest)

            proposal = runtime.generate_proposal(
                change_summary="Governed candidate",
                proposer_id="integration-test",
                target_manifest=manifest,
            )
            with self.assertRaises(GovernanceError):
                runtime.promote_candidate(proposal["proposal_id"])

    def test_failing_verification_hook_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir)
            runtime.register_verification_hook(
                "regression",
                lambda proposal, context: {"status": "fail", "details": "regression detected"},
            )
            candidate_manifest = runtime.version_store.load_active_manifest()
            candidate_manifest["version"] = "0.2.0"
            proposal = runtime.generate_proposal(
                change_summary="Candidate with failing verification",
                proposer_id="integration-test",
                target_manifest=candidate_manifest,
            )
            evaluation = runtime.evaluate_proposal(proposal["proposal_id"], source_origin="integration-test")
            self.assertEqual(evaluation["status"], "fail")
            with self.assertRaises(GovernanceError):
                runtime.promote_candidate(proposal["proposal_id"])

    def test_governed_handshake_and_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir, "governed.manifest.json")
            manifest = runtime.version_store.load_active_manifest()
            proposal = runtime.generate_proposal(
                change_summary="Submit to governor",
                proposer_id="integration-test",
                target_manifest=manifest,
            )
            handshake = runtime.governor_client.handshake(
                governor_id="governor-main",
                supported_min_version="1.0.0",
                supported_max_version="1.0.0",
            )
            self.assertTrue(handshake["compatible"])
            submitted = runtime.governor_client.submit_proposal(proposal["proposal_id"])
            self.assertEqual(submitted["status"], "submitted")
            self.assertIn("submitted_at", submitted)


if __name__ == "__main__":
    unittest.main()
