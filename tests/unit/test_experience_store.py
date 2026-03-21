from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_support import PROTOCOL_ROOT, load_example_manifest
from skill_se_kit.runtime.skill_runtime import SkillRuntime


class ExperienceStoreTests(unittest.TestCase):
    def test_record_experience_writes_protocol_valid_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.workspace.bootstrap(load_example_manifest())

            record = runtime.record_experience(
                kind="observation",
                summary="Observed stable behavior during unit test.",
                source_origin="unit-test",
                outcome={"status": "positive", "impact": "low"},
            )

            path = Path(tmpdir) / "local" / "experiences" / f"{record['record_id']}.json"
            self.assertTrue(path.exists())
            self.assertEqual(record["schema_name"], "ExperienceRecord")
            self.assertEqual(record["protocol_version"], "1.0.0")
            self.assertTrue((Path(tmpdir) / "audit" / "summaries").exists())
            self.assertTrue((Path(tmpdir) / "provenance" / "sources").exists())


if __name__ == "__main__":
    unittest.main()
