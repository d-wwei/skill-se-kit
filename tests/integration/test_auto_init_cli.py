from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_support import PROTOCOL_ROOT, ROOT, SRC


class AutoInitCliTests(unittest.TestCase):
    def test_init_creates_auto_integration_and_patches_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "SKILL.md").write_text("# Demo Skill\n", encoding="utf-8")
            (root / "executor.py").write_text(
                "def execute(input, context):\n"
                "    return {'text': f\"Handled {input.get('task', 'unknown')}\"}\n",
                encoding="utf-8",
            )
            result = self._run_cli(
                "init",
                "--skill-root",
                str(root),
                "--protocol-root",
                str(PROTOCOL_ROOT),
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "initialized")
            self.assertEqual(payload["executor_kind"], "python_file")
            self.assertTrue((root / ".skill_se_kit" / "auto_integration.json").exists())
            skill_md = (root / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Skill-SE-Kit Auto Runtime", skill_md)

    def test_run_uses_auto_integration_and_supports_chinese_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "executor.py").write_text(
                "def execute(input, context):\n"
                "    return {'text': '已处理任务'}\n",
                encoding="utf-8",
            )
            self._run_cli(
                "init",
                "--skill-root",
                str(root),
                "--protocol-root",
                str(PROTOCOL_ROOT),
            )
            result = self._run_cli(
                "run",
                "--skill-root",
                str(root),
                "--input-json",
                json.dumps({"task": "检查流程", "user_input": "每次都要先做安全检查"}, ensure_ascii=False),
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["kit_active"])
            self.assertEqual(payload["runtime_mode"], "auto")
            self.assertIn("每次都要先做安全检查", payload["autonomous_cycle"]["experience"]["lesson"])
            report_md = (root / "reports" / "evolution" / "latest.md").read_text(encoding="utf-8")
            self.assertIn("Learned Lesson", report_md)

    def test_init_detects_multi_script_skill_and_surfaces_dispatcher_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "scripts").mkdir()
            (root / "scripts" / "quote.py").write_text("print('quote')\n", encoding="utf-8")
            (root / "scripts" / "trade.py").write_text("print('trade')\n", encoding="utf-8")
            result = self._run_cli(
                "init",
                "--skill-root",
                str(root),
                "--protocol-root",
                str(PROTOCOL_ROOT),
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["executor_kind"], "passive")
            auto_config = json.loads((root / ".skill_se_kit" / "auto_integration.json").read_text(encoding="utf-8"))
            self.assertEqual(auto_config["executor"]["discovered_by"], "script_inventory")
            self.assertEqual(len(auto_config["executor"]["script_inventory"]), 2)

    def test_rollback_cli_restores_previous_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "executor.py").write_text(
                "def execute(input, context):\n"
                "    text = 'Draft report.'\n"
                "    if 'plan' in context.get('skill_guidance', '').lower():\n"
                "        text += ' Include a plan.'\n"
                "    return {'text': text}\n",
                encoding="utf-8",
            )
            self._run_cli(
                "init",
                "--skill-root",
                str(root),
                "--protocol-root",
                str(PROTOCOL_ROOT),
            )
            result = self._run_cli(
                "run",
                "--skill-root",
                str(root),
                "--input-json",
                json.dumps({"task": "draft report", "user_input": "Always include a plan section."}, ensure_ascii=False),
            )
            payload = json.loads(result.stdout)
            snapshot_id = payload["autonomous_cycle"]["promotion"]["snapshot_id"]
            rollback = self._run_cli(
                "rollback",
                "--skill-root",
                str(root),
                "--snapshot-id",
                snapshot_id,
            )
            rollback_payload = json.loads(rollback.stdout)
            self.assertEqual(rollback_payload["snapshot_id"], snapshot_id)
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], "0.1.0")

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC)
        return subprocess.run(
            [sys.executable, "-m", "skill_se_kit", *args],
            cwd=str(ROOT),
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
