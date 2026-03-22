from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

from skill_se_kit.runtime.skill_runtime import SkillRuntime


def build_manifest() -> dict:
    return {
        "schema_name": "SkillManifest",
        "schema_version": "1.0.0",
        "protocol_version": "1.0.0",
        "skill_id": "example.autonomous-code-repair",
        "name": "Autonomous Code Repair Skill",
        "version": "0.1.0",
        "description": "Demonstrates automatic code repair landing in managed files.",
        "governance": {"mode": "standalone", "official_status": "local"},
        "capability": {"level": "native", "summary": "Repairs a managed Python file when a defect is observed."},
        "compatibility": {"min_protocol_version": "1.0.0", "max_protocol_version": "1.0.0"},
        "metadata": {"owner": "skill-se-kit"},
    }


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"repair_demo_{path.stem}_{path.name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    protocol_root = repo_root / "skill-evolution-protocol"

    with tempfile.TemporaryDirectory(prefix="skill-se-kit-repair-") as tmpdir:
        skill_root = Path(tmpdir) / "repair-skill"
        runtime = SkillRuntime(skill_root=skill_root, protocol_root=protocol_root)
        runtime.workspace.bootstrap(build_manifest())

        logic_path = skill_root / "logic.py"
        logic_path.write_text(
            "ALIASES = {'us_chip': 'BK9999'}\n"
            "def resolve_alias(name):\n"
            "    return ALIASES.get(name, 'UNKNOWN')\n",
            encoding="utf-8",
        )

        def executor(input, context):
            module_path = logic_path
            if context.get("candidate_file_patches", {}).get("logic.py"):
                module_path = skill_root / "logic_candidate.py"
                module_path.write_text(context["candidate_file_patches"]["logic.py"], encoding="utf-8")
            module = load_module(module_path)
            return {"text": module.resolve_alias(input["alias"])}

        runtime.register_executor(executor)
        runtime.configure_integration(
            managed_files=[{"path": "logic.py", "kind": "code"}],
            evaluation_cases=[
                {
                    "id": "resolve-us-ai",
                    "input": {"task": "resolve alias", "alias": "us_ai"},
                    "must_contain": ["BK8888"],
                }
            ],
            max_repair_rounds=1,
        )

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

        print(
            json.dumps(
                {
                    "decision": cycle["decision"],
                    "evaluation": cycle["evaluation"]["benchmark"],
                    "promotion_id": cycle["promotion"]["promotion_id"] if cycle["promotion"] else None,
                    "patched_file": logic_path.read_text(encoding="utf-8"),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
