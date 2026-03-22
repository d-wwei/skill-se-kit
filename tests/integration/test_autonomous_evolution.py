from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skill_se_kit.runtime.skill_runtime import SkillRuntime
from tests.test_support import PROTOCOL_ROOT, load_example_manifest


class AutonomousEvolutionTests(unittest.TestCase):
    def _runtime(self, tmpdir: str) -> SkillRuntime:
        runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
        runtime.workspace.bootstrap(load_example_manifest("standalone.manifest.json"))
        return runtime

    def test_autonomous_cycle_learns_and_improves_future_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir)
            runtime.configure_integration(
                evaluation_cases=[
                    {
                        "id": "safety-case",
                        "input": {"task": "prepare launch plan"},
                        "must_contain": ["safety", "plan"],
                    }
                ]
            )

            def executor(input, context):
                task = input["task"]
                guidance = context.get("skill_guidance", "")
                response = f"Task: {task}."
                if "safety" in guidance.lower():
                    response += " Include safety checks."
                if "plan" in guidance.lower():
                    response += " Provide a step-by-step plan."
                return {"text": response}

            runtime.register_executor(executor)
            first = runtime.run_autonomous_cycle(
                {"task": "prepare launch plan"},
                feedback={"status": "positive", "lesson": "Always mention safety checks and give a step-by-step plan."},
            )
            cycle = first["autonomous_cycle"]
            self.assertEqual(cycle["decision"]["action"], "add")
            self.assertEqual(cycle["evaluation"]["status"], "pass")
            self.assertIsNotNone(cycle["promotion"])

            second = runtime.execute({"task": "prepare launch plan"})
            self.assertIn("safety", second["result"]["text"].lower())
            self.assertIn("step-by-step plan", second["result"]["text"].lower())

    def test_autonomous_cycle_merges_similar_lessons_and_rollback_restores_skill_bank(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir)
            managed_path = Path(tmpdir) / "SKILL.md"
            managed_path.write_text("# Base Skill\n", encoding="utf-8")
            runtime.configure_integration(
                managed_files=[{"path": "SKILL.md", "kind": "markdown"}],
                evaluation_cases=[
                    {"id": "plan-case", "input": {"task": "draft report"}, "must_contain": ["plan"]},
                ],
            )

            def executor(input, context):
                guidance = context.get("skill_guidance", "") + "\n" + context.get("candidate_file_patches", {}).get("SKILL.md", "")
                response = "Draft report."
                if "plan" in guidance.lower():
                    response += " Include a plan."
                return {"text": response}

            runtime.register_executor(executor)
            first = runtime.run_autonomous_cycle(
                {"task": "draft report"},
                feedback="Always include a plan section.",
            )
            second = runtime.run_autonomous_cycle(
                {"task": "draft report"},
                feedback="Include a plan section and keep it reusable.",
            )
            self.assertEqual(second["autonomous_cycle"]["decision"]["action"], "merge")
            skill_bank = runtime.knowledge_store.load_skill_bank()
            self.assertEqual(len(skill_bank), 1)
            self.assertEqual(skill_bank[0]["version"], "0.1.1")

            snapshot_id = second["autonomous_cycle"]["promotion"]["snapshot_id"]
            runtime.rollback(snapshot_id)
            rolled_back_bank = runtime.knowledge_store.load_skill_bank()
            self.assertEqual(len(rolled_back_bank), 1)
            self.assertEqual(rolled_back_bank[0]["version"], "0.1.0")


if __name__ == "__main__":
    unittest.main()
