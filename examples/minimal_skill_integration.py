from __future__ import annotations

import json
import tempfile
from pathlib import Path

from skill_se_kit.runtime.skill_runtime import SkillRuntime


def build_demo_manifest() -> dict:
    return {
        "schema_name": "SkillManifest",
        "schema_version": "1.0.0",
        "protocol_version": "1.0.0",
        "skill_id": "example.todo-assistant",
        "name": "Todo Assistant",
        "version": "0.1.0",
        "description": "A tiny example skill integrated with Skill-SE-Kit.",
        "governance": {
            "mode": "standalone",
            "official_status": "local",
        },
        "capability": {
            "level": "native",
            "summary": "Helps organize and summarize todo items.",
            "declared_interfaces": ["todo.organize", "todo.summarize"],
        },
        "compatibility": {
            "min_protocol_version": "1.0.0",
            "max_protocol_version": "1.0.0",
        },
        "metadata": {
            "domain": "productivity",
        },
    }


def todo_regression_hook(proposal_document: dict, context: dict) -> dict:
    change_summary = proposal_document["change_summary"].lower()
    if "unsafe" in change_summary:
        return {"status": "fail", "details": "unsafe change marker detected"}
    return {
        "status": "pass",
        "details": f"todo regression checks passed for {proposal_document['proposal_id']}",
        "metadata": {"source_origin": context.get("source_origin", "unknown")},
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    protocol_root = repo_root / "skill-evolution-protocol"

    with tempfile.TemporaryDirectory(prefix="skill-se-kit-demo-") as tmpdir:
        skill_root = Path(tmpdir) / "todo-skill"
        runtime = SkillRuntime(skill_root=skill_root, protocol_root=protocol_root)

        manifest = build_demo_manifest()
        runtime.workspace.bootstrap(manifest)
        runtime.register_verification_hook("todo_regression", todo_regression_hook)

        runtime.record_experience(
            kind="observation",
            summary="Users preferred the shorter todo summaries in smoke tests.",
            source_origin="minimal-example",
            outcome={"status": "positive", "impact": "low"},
        )

        candidate_manifest = runtime.version_store.load_active_manifest()
        candidate_manifest["version"] = "0.2.0"
        candidate_manifest["description"] = "Improves todo summary clarity."
        candidate_manifest.setdefault("metadata", {})
        candidate_manifest["metadata"]["release_note"] = "shorter summaries"

        proposal = runtime.generate_proposal(
            change_summary="Improve todo summary clarity and update metadata",
            proposer_id="minimal-example",
            target_manifest=candidate_manifest,
        )

        evaluation = runtime.evaluate_proposal(
            proposal["proposal_id"],
            source_origin="minimal-example",
        )
        promotion = runtime.promote_candidate(proposal["proposal_id"])

        result = {
            "skill_root": str(skill_root),
            "proposal_id": proposal["proposal_id"],
            "evaluation_status": evaluation["status"],
            "promotion_id": promotion["promotion_id"],
            "active_manifest_version": runtime.version_store.load_active_manifest()["version"],
            "audit_logs": sorted(str(path.name) for path in (skill_root / "audit" / "decision_logs").glob("*.json")),
            "provenance_lineage": sorted(
                str(path.name) for path in (skill_root / "provenance" / "lineage").glob("*.json")
            ),
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
