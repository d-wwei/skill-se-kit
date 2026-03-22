from __future__ import annotations

import json
import tempfile
from pathlib import Path

from skill_se_kit.integration.easy_mode import EasyIntegrator


def build_manifest() -> dict:
    return {
        "schema_name": "SkillManifest",
        "schema_version": "1.0.0",
        "protocol_version": "1.0.0",
        "skill_id": "example.easy-mode-skill",
        "name": "Easy Mode Skill",
        "version": "0.1.0",
        "description": "One-click integrated skill example.",
        "governance": {"mode": "standalone", "official_status": "local"},
        "capability": {"level": "native", "summary": "Demonstrates foolproof integration."},
        "compatibility": {"min_protocol_version": "1.0.0", "max_protocol_version": "1.0.0"},
        "metadata": {"owner": "skill-se-kit"},
    }


def executor(input, context):
    task = input.get("task", "unknown task")
    guidance = context.get("skill_guidance", "")
    text = f"Handled {task}."
    if "summary" in guidance.lower():
        text += " Added a summary section."
    return {"text": text}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    protocol_root = repo_root / "skill-evolution-protocol"

    with tempfile.TemporaryDirectory(prefix="skill-se-kit-easy-") as tmpdir:
        runtime = EasyIntegrator.one_click(
            skill_root=tmpdir,
            protocol_root=protocol_root,
            manifest=build_manifest(),
            executor=executor,
            run_mode="auto",
            human_reports=True,
        )
        result = runtime.run_integrated_skill(
            {"task": "draft memo"},
            context={"user_input": "Always include a concise summary section."},
        )
        print(
            json.dumps(
                {
                    "runtime_mode": result["runtime_mode"],
                    "kit_active": result["kit_active"],
                    "learned_action": result["autonomous_cycle"]["decision"]["action"],
                    "report_summary": runtime.get_latest_evolution_summary(),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
