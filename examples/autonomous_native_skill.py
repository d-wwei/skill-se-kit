from __future__ import annotations

import json
import tempfile
from pathlib import Path

from skill_se_kit.runtime.skill_runtime import SkillRuntime


def build_manifest() -> dict:
    return {
        "schema_name": "SkillManifest",
        "schema_version": "1.0.0",
        "protocol_version": "1.0.0",
        "skill_id": "example.autonomous-checklist",
        "name": "Autonomous Checklist Skill",
        "version": "0.1.0",
        "description": "Example autonomous skill built on Skill-SE-Kit.",
        "governance": {"mode": "standalone", "official_status": "local"},
        "capability": {"level": "native", "summary": "Produces operational checklists."},
        "compatibility": {"min_protocol_version": "1.0.0", "max_protocol_version": "1.0.0"},
        "metadata": {"owner": "skill-se-kit"},
    }


def checklist_executor(input, context):
    task = input["task"]
    guidance = context.get("skill_guidance", "")
    response = f"Checklist for {task}:"
    if "safety" in guidance.lower():
        response += " include safety checks;"
    if "step-by-step" in guidance.lower() or "plan" in guidance.lower():
        response += " include a step-by-step plan;"
    return {"text": response}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    protocol_root = repo_root / "skill-evolution-protocol"

    with tempfile.TemporaryDirectory(prefix="skill-se-kit-autonomous-") as tmpdir:
        skill_root = Path(tmpdir) / "autonomous-skill"
        runtime = SkillRuntime(skill_root=skill_root, protocol_root=protocol_root)
        runtime.workspace.bootstrap(build_manifest())
        runtime.register_executor(checklist_executor)
        runtime.configure_integration(
            evaluation_cases=[
                {
                    "id": "launch-readiness",
                    "input": {"task": "launch readiness"},
                    "must_contain": ["safety", "plan"],
                }
            ],
            auto_promote_min_improvement=0.0,
        )

        cycle = runtime.run_autonomous_cycle(
            {"task": "launch readiness"},
            feedback={
                "status": "positive",
                "lesson": "Always include safety checks and a step-by-step plan for launch readiness tasks.",
            },
        )

        improved = runtime.execute({"task": "launch readiness"})
        print(
            json.dumps(
                {
                    "decision": cycle["autonomous_cycle"]["decision"],
                    "benchmark": cycle["autonomous_cycle"]["evaluation"]["benchmark"],
                    "improved_output": improved["result"]["text"],
                    "skill_bank_size": len(runtime.knowledge_store.load_skill_bank()),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
