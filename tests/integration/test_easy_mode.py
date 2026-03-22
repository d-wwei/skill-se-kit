from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skill_se_kit.integration.easy_mode import EasyIntegrator
from skill_se_kit.runtime.skill_runtime import SkillRuntime
from tests.test_support import PROTOCOL_ROOT, load_example_manifest


class EasyModeTests(unittest.TestCase):
    def _manifest(self):
        return load_example_manifest("standalone.manifest.json")

    def test_one_click_integration_auto_mode_runs_learning_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = EasyIntegrator.one_click(
                skill_root=tmpdir,
                protocol_root=PROTOCOL_ROOT,
                manifest=self._manifest(),
                executor=lambda input, context: {"text": "Task result."},
                run_mode="auto",
                evaluation_cases=[],
            )
            result = runtime.run_integrated_skill(
                {"task": "status update", "user_input": "Always include a summary section."},
            )
            self.assertTrue(result["kit_active"])
            self.assertEqual(result["runtime_mode"], "auto")
            self.assertIn("autonomous_cycle", result)
            self.assertIn("evolution_report", result)
            self.assertTrue((Path(tmpdir) / "reports" / "evolution" / "latest.md").exists())

    def test_manual_mode_runs_tracking_without_auto_improve(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.enable_easy_integration(
                manifest=self._manifest(),
                executor=lambda input, context: {"text": "Manual result."},
                run_mode="manual",
            )
            result = runtime.run_integrated_skill({"task": "manual task"})
            self.assertTrue(result["kit_active"])
            self.assertEqual(result["runtime_mode"], "manual")
            self.assertNotIn("autonomous_cycle", result)

    def test_off_mode_bypasses_kit_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.enable_easy_integration(
                manifest=self._manifest(),
                executor=lambda input, context: {"text": "Bypass result."},
                run_mode="off",
            )
            result = runtime.run_integrated_skill({"task": "off task"})
            self.assertFalse(result["kit_active"])
            self.assertEqual(result["runtime_mode"], "off")
            self.assertEqual(result["result"]["text"], "Bypass result.")

    def test_auto_feedback_extracts_lesson_from_user_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.enable_easy_integration(
                manifest=self._manifest(),
                executor=lambda input, context: {"text": "Report delivered."},
                run_mode="auto",
            )
            result = runtime.run_integrated_skill(
                {"task": "write report"},
                context={"user_input": "Always include a concise executive summary."},
            )
            lesson = result["autonomous_cycle"]["experience"]["lesson"]
            self.assertIn("Always include a concise executive summary", lesson)


if __name__ == "__main__":
    unittest.main()
