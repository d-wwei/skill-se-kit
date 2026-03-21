from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skill_se_kit.common import list_json_files
from skill_se_kit.runtime.skill_runtime import SkillRuntime
from tests.test_support import PROTOCOL_ROOT, load_example_manifest


class PlatformArtifactTests(unittest.TestCase):
    def test_proposal_and_evaluation_emit_audit_and_provenance_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.workspace.bootstrap(load_example_manifest())
            runtime.register_verification_hook("smoke", lambda proposal, context: True)

            candidate_manifest = runtime.version_store.load_active_manifest()
            candidate_manifest["version"] = "0.2.0"
            proposal = runtime.generate_proposal(
                change_summary="Platform artifact test proposal",
                proposer_id="unit-test",
                target_manifest=candidate_manifest,
            )
            evaluation = runtime.evaluate_proposal(proposal["proposal_id"], source_origin="unit-test")

            audit_logs = list(list_json_files(Path(tmpdir) / "audit" / "decision_logs"))
            summaries = list(list_json_files(Path(tmpdir) / "audit" / "summaries"))
            evidence = list(list_json_files(Path(tmpdir) / "audit" / "evidence"))
            lineage = list(list_json_files(Path(tmpdir) / "provenance" / "lineage"))

            self.assertTrue(audit_logs)
            self.assertTrue(summaries)
            self.assertTrue(evidence)
            self.assertTrue(lineage)
            self.assertEqual(evaluation["status"], "pass")


if __name__ == "__main__":
    unittest.main()
