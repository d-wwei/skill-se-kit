from __future__ import annotations

import importlib.util
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

    def test_autonomous_cycle_can_apply_structured_code_repair_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir)
            logic_path = Path(tmpdir) / "logic.py"
            logic_path.write_text(
                "ALIASES = {'us_chip': 'BK9999'}\n"
                "def resolve_alias(name):\n"
                "    return ALIASES.get(name, 'UNKNOWN')\n",
                encoding="utf-8",
            )
            runtime.configure_integration(
                managed_files=[{"path": "logic.py", "kind": "code"}],
                evaluation_cases=[
                    {
                        "id": "alias-fix",
                        "input": {"task": "resolve alias", "alias": "us_ai"},
                        "must_contain": ["BK8888"],
                    }
                ],
            )

            def executor(input, context):
                module = self._load_module(logic_path)
                if context.get("candidate_file_patches", {}).get("logic.py"):
                    patched = Path(tmpdir) / "logic_candidate.py"
                    patched.write_text(context["candidate_file_patches"]["logic.py"], encoding="utf-8")
                    module = self._load_module(patched)
                return {"text": module.resolve_alias(input["alias"])}

            runtime.register_executor(executor)
            cycle = runtime.run_autonomous_cycle(
                {"task": "resolve alias", "alias": "us_ai"},
                feedback={
                    "status": "negative",
                    "lesson": "US AI alias is missing.",
                    "repair_actions": [
                        {
                            "adapter": "python_dict_set",
                            "path": "logic.py",
                            "target": "ALIASES",
                            "key": "us_ai",
                            "value": "BK8888",
                        }
                    ],
                },
            )["autonomous_cycle"]

            self.assertIsNotNone(cycle["promotion"])
            self.assertIn("'us_ai': 'BK8888'", logic_path.read_text(encoding="utf-8"))
            repaired = runtime.execute({"task": "resolve alias", "alias": "us_ai"})
            self.assertIn("BK8888", repaired["result"]["text"])

    def test_failed_evaluation_case_can_trigger_automatic_followup_repair_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = self._runtime(tmpdir)
            prompt_path = Path(tmpdir) / "prompt_rules.py"
            prompt_path.write_text(
                "INCLUDE_SUMMARY = False\n"
                "def render():\n"
                "    return 'Plan only'\n",
                encoding="utf-8",
            )
            runtime.configure_integration(
                managed_files=[{"path": "prompt_rules.py", "kind": "code"}],
                evaluation_cases=[
                    {
                        "id": "summary-required",
                        "input": {"task": "draft memo"},
                        "must_contain": ["summary"],
                        "repair_actions_on_fail": [
                            {
                                "adapter": "replace_text",
                                "path": "prompt_rules.py",
                                "old": "INCLUDE_SUMMARY = False",
                                "new": "INCLUDE_SUMMARY = True",
                            }
                        ],
                    }
                ],
                max_repair_rounds=1,
            )

            def executor(input, context):
                module = self._load_module(prompt_path)
                if context.get("candidate_file_patches", {}).get("prompt_rules.py"):
                    patched = Path(tmpdir) / "prompt_rules_candidate.py"
                    patched.write_text(context["candidate_file_patches"]["prompt_rules.py"], encoding="utf-8")
                    module = self._load_module(patched)
                text = module.render()
                if "INCLUDE_SUMMARY = True" in Path(module.__file__).read_text(encoding="utf-8"):
                    text += " Summary included"
                return {"text": text}

            runtime.register_executor(executor)
            cycle = runtime.run_autonomous_cycle(
                {"task": "draft memo"},
                feedback={"status": "positive", "lesson": "Add a summary block for memo outputs."},
            )["autonomous_cycle"]

            self.assertEqual(cycle["evaluation"]["status"], "pass")
            self.assertIsNotNone(cycle["promotion"])
            self.assertIn("INCLUDE_SUMMARY = True", prompt_path.read_text(encoding="utf-8"))
            improved = runtime.execute({"task": "draft memo"})
            self.assertIn("summary", improved["result"]["text"].lower())

    @staticmethod
    def _load_module(path: Path):
        spec = importlib.util.spec_from_file_location(f"mod_{path.stem}_{path.name}", path)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        return module


if __name__ == "__main__":
    unittest.main()
