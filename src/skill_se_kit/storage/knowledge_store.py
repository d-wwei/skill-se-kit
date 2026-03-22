from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from skill_se_kit.common import (
    dump_json,
    generate_id,
    jaccard_similarity,
    list_json_files,
    load_json,
    normalize_text,
    utc_now_iso,
)


class KnowledgeStore:
    def __init__(self, workspace):
        self.workspace = workspace
        self.workspace.ensure_layout()
        if not self.workspace.local_skill_bank_path.exists():
            dump_json(self.workspace.local_skill_bank_path, {"skills": []})
        if not self.workspace.official_skill_bank_path.exists():
            dump_json(self.workspace.official_skill_bank_path, {"skills": []})

    def load_skill_bank(self, *, official: bool = False) -> List[Dict[str, Any]]:
        path = self.workspace.official_skill_bank_path if official else self.workspace.local_skill_bank_path
        payload = load_json(path)
        return list(payload.get("skills") or [])

    def save_skill_bank(self, skills: List[Dict[str, Any]], *, official: bool = False) -> List[Dict[str, Any]]:
        path = self.workspace.official_skill_bank_path if official else self.workspace.local_skill_bank_path
        dump_json(path, {"skills": skills})
        return skills

    def append_rollout(self, rollout: Dict[str, Any]) -> Dict[str, Any]:
        dump_json(self.workspace.local_rollouts_dir / f"{rollout['execution_id']}.json", rollout)
        return rollout

    def load_rollout(self, execution_id: str) -> Dict[str, Any]:
        return load_json(self.workspace.local_rollouts_dir / f"{execution_id}.json")

    def recent_rollouts(self, task_signature: str, limit: int = 5) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for path in list_json_files(self.workspace.local_rollouts_dir):
            rollout = load_json(path)
            if rollout.get("task_signature") == task_signature:
                items.append(rollout)
        items.sort(key=lambda item: item.get("executed_at", ""))
        return items[-limit:]

    def append_experience_item(self, experience_item: Dict[str, Any]) -> Dict[str, Any]:
        dump_json(
            self.workspace.local_experience_bank_dir / f"{experience_item['experience_id']}.json",
            experience_item,
        )
        return experience_item

    def load_experience_bank(self) -> List[Dict[str, Any]]:
        experiences = [load_json(path) for path in list_json_files(self.workspace.local_experience_bank_dir)]
        experiences.sort(key=lambda item: item.get("recorded_at", ""))
        return experiences

    def retrieve_knowledge(
        self,
        *,
        query_text: str,
        top_k: int = 3,
        skill_bank: Optional[List[Dict[str, Any]]] = None,
        experience_bank: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        active_skills = list(skill_bank if skill_bank is not None else self.load_skill_bank())
        experiences = list(experience_bank if experience_bank is not None else self.load_experience_bank())

        scored_skills = []
        for skill in active_skills:
            score = jaccard_similarity(
                query_text,
                " ".join(
                    [
                        normalize_text(skill.get("title")),
                        normalize_text(skill.get("content")),
                        " ".join(skill.get("keywords", [])),
                    ]
                ),
            )
            if score > 0:
                scored_skills.append((score, skill))

        scored_experiences = []
        for experience in experiences:
            score = jaccard_similarity(
                query_text,
                " ".join(
                    [
                        normalize_text(experience.get("lesson")),
                        normalize_text(experience.get("feedback_text")),
                        normalize_text(experience.get("task_signature")),
                    ]
                ),
            )
            if score > 0:
                scored_experiences.append((score, experience))

        scored_skills.sort(key=lambda item: item[0], reverse=True)
        scored_experiences.sort(key=lambda item: item[0], reverse=True)
        return {
            "skills": [dict(item[1], retrieval_score=item[0]) for item in scored_skills[:top_k]],
            "experiences": [dict(item[1], retrieval_score=item[0]) for item in scored_experiences[:top_k]],
        }

    def save_candidate_bundle(self, proposal_id: str, bundle: Dict[str, Any]) -> Path:
        path = self.workspace.local_proposals_dir / f"{proposal_id}.bundle.json"
        dump_json(path, bundle)
        return path

    def load_candidate_bundle(self, proposal_id: str) -> Dict[str, Any]:
        return load_json(self.workspace.local_proposals_dir / f"{proposal_id}.bundle.json")

