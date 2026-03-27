from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from skill_se_kit.common import (
    bump_patch_version,
    generate_id,
    jaccard_similarity,
    normalize_text,
    tokenize_text,
    utc_now_iso,
)

if TYPE_CHECKING:
    from skill_se_kit.intelligence.backend import IntelligenceBackend

# Number of bullets in a skill before auto-synthesis is triggered.
_AUTO_SYNTHESIS_THRESHOLD = 15


class AutonomousEvolutionEngine:
    def __init__(
        self,
        workspace,
        version_store,
        knowledge_store,
        proposal_generator,
        local_evaluator,
        local_promoter,
        audit_logger=None,
        provenance_store=None,
        contract_store=None,
        repair_planner=None,
        regression_runner=None,
        intelligence_backend: "IntelligenceBackend | None" = None,
    ):
        self.workspace = workspace
        self.version_store = version_store
        self.knowledge_store = knowledge_store
        self.proposal_generator = proposal_generator
        self.local_evaluator = local_evaluator
        self.local_promoter = local_promoter
        self.audit_logger = audit_logger
        self.provenance_store = provenance_store
        self.contract_store = contract_store
        self.repair_planner = repair_planner
        self.regression_runner = regression_runner
        self._backend: IntelligenceBackend | None = intelligence_backend

    def set_intelligence_backend(self, backend: "IntelligenceBackend") -> None:
        self._backend = backend

    def execute(self, input: Dict[str, Any], context: Optional[Dict[str, Any]], executor) -> Dict[str, Any]:
        task_signature = self._task_signature(input, context)
        query_text = self._query_text(input, context)
        retrieved = self.knowledge_store.retrieve_knowledge(query_text=query_text)
        effective_context = {
            **(context or {}),
            "task_signature": task_signature,
            "retrieved_skills": retrieved["skills"],
            "retrieved_experiences": retrieved["experiences"],
            "skill_guidance": "\n".join(skill["content"] for skill in retrieved["skills"]),
        }
        result = executor(input, effective_context)
        execution = {
            "execution_id": generate_id("execution"),
            "executed_at": utc_now_iso(),
            "input": input,
            "context": context or {},
            "task_signature": task_signature,
            "retrieved": retrieved,
            "result": result,
        }
        self.knowledge_store.append_rollout(execution)
        return {
            "execution_id": execution["execution_id"],
            "task_signature": task_signature,
            "retrieved": retrieved,
            "result": result,
        }

    def learn_from_interaction(
        self,
        *,
        execution_id: str,
        feedback: Dict[str, Any] | str,
        proposer_id: str = "autonomous-engine",
        rewriter=None,
        auto_promote: bool = True,
    ) -> Dict[str, Any]:
        rollout = self.knowledge_store.load_rollout(execution_id)
        feedback_payload = self._normalize_feedback(feedback)
        confidence = float(feedback_payload.get("confidence", 1.0))
        min_confidence = 0.0
        if self.contract_store is not None:
            min_confidence = float(self.contract_store.load_contract().get("min_feedback_confidence", 0.35))
        experience = self._extract_experience(rollout, feedback_payload)
        self.knowledge_store.append_experience_item(experience)

        if confidence < min_confidence:
            return {
                "execution_id": execution_id,
                "experience": experience,
                "decision": {
                    "action": "skip",
                    "summary": f"Skipped low-confidence feedback for {execution_id}",
                    "reason": "low_feedback_confidence",
                    "confidence": confidence,
                    "min_feedback_confidence": min_confidence,
                },
                "proposal": None,
                "evaluation": None,
                "promotion": None,
            }

        decision, updated_skill_bank = self._decide_skill_update(experience)
        if decision["action"] == "discard":
            return {
                "execution_id": execution_id,
                "experience": experience,
                "decision": decision,
                "proposal": None,
                "evaluation": None,
                "promotion": None,
            }

        contract = self.contract_store.load_contract() if self.contract_store is not None else {"managed_files": []}
        managed_files = list(contract.get("managed_files") or [])
        file_patches = self._build_file_patches(
            experience=experience,
            decision=decision,
            feedback=feedback_payload,
            rollout=rollout,
            managed_files=managed_files,
            rewriter=rewriter,
        )
        active_manifest = self.version_store.load_active_manifest()
        candidate_manifest = dict(active_manifest)
        candidate_manifest["version"] = bump_patch_version(active_manifest["version"])
        candidate_manifest.setdefault("metadata", {})
        candidate_manifest["metadata"]["evolution_mode"] = "autonomous"

        experience_path = self.workspace.local_experience_bank_dir / f"{experience['experience_id']}.json"
        proposal = self.proposal_generator.generate_proposal(
            change_summary=decision["summary"],
            proposer_id=proposer_id,
            target_manifest=candidate_manifest,
            artifacts=[
                {"type": "evidence", "ref": str(experience_path.relative_to(self.workspace.root))},
            ],
            metadata={"autonomous_decision": decision["action"]},
        )

        bundle = {
            "bundle_id": generate_id("bundle"),
            "created_at": utc_now_iso(),
            "proposal_id": proposal["proposal_id"],
            "decision": decision,
            "experience_id": experience["experience_id"],
            "skill_bank": updated_skill_bank,
            "file_patches": file_patches,
        }
        bundle_path = self.knowledge_store.save_candidate_bundle(proposal["proposal_id"], bundle)
        proposal = self._attach_bundle_ref(proposal, bundle_path)

        evaluation = self.local_evaluator.evaluate_proposal(
            proposal["proposal_id"],
            source_origin="autonomous-engine",
            metadata={"autonomous": True},
        )
        repair_round = 0
        max_repair_rounds = int(contract.get("max_repair_rounds", 1)) if self.contract_store is not None else 1
        while evaluation["status"] == "fail" and repair_round < max_repair_rounds:
            followup_actions = []
            if self.repair_planner is not None:
                followup_actions = self.repair_planner.collect_evaluation_actions(evaluation)
            if not followup_actions:
                break
            repair_round += 1
            file_patches = self._build_file_patches(
                experience=experience,
                decision=decision,
                feedback=feedback_payload,
                rollout=rollout,
                managed_files=managed_files,
                rewriter=rewriter,
                extra_actions=followup_actions,
                current_patches=file_patches,
            )
            bundle["file_patches"] = file_patches
            bundle["repair_round"] = repair_round
            self.knowledge_store.save_candidate_bundle(proposal["proposal_id"], bundle)
            evaluation = self.local_evaluator.evaluate_proposal(
                proposal["proposal_id"],
                source_origin="autonomous-engine",
                metadata={"autonomous": True, "repair_round": repair_round},
            )
        promotion = None
        min_improvement = 0.0
        if self.contract_store is not None:
            min_improvement = float(self.contract_store.load_contract().get("auto_promote_min_improvement", 0.0))
        benchmark = evaluation.get("benchmark") or {}
        benchmark_improvement = float(benchmark.get("improvement", 0.0))
        should_promote = evaluation["status"] == "pass" and (
            benchmark.get("status") in (None, "not_run") or benchmark_improvement >= min_improvement
        )
        if auto_promote and should_promote and not self.local_promoter.governor_client.detect_governor():
            promotion = self.local_promoter.promote_candidate(proposal["proposal_id"])

        return {
            "execution_id": execution_id,
            "experience": experience,
            "decision": decision,
            "proposal": proposal,
            "evaluation": evaluation,
            "promotion": promotion,
        }

    def _attach_bundle_ref(self, proposal: Dict[str, Any], bundle_path) -> Dict[str, Any]:
        proposal.setdefault("artifacts", [])
        proposal["artifacts"].append({"type": "note", "ref": str(bundle_path.relative_to(self.workspace.root))})
        from skill_se_kit.common import dump_json

        dump_json(self.workspace.local_proposals_dir / f"{proposal['proposal_id']}.json", proposal)
        return proposal

    def _task_signature(self, input: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        if context and context.get("task_signature"):
            return str(context["task_signature"])
        joined = self._query_text(input, context)
        tokens = tokenize_text(joined)
        return " ".join(tokens[:8]) or "generic-task"

    @staticmethod
    def _query_text(input: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        parts = [normalize_text(input)]
        if context:
            parts.append(normalize_text(context.get("query") or context.get("goal") or ""))
        return " ".join(part for part in parts if part).strip()

    def _normalize_feedback(self, feedback: Dict[str, Any] | str) -> Dict[str, Any]:
        if isinstance(feedback, dict):
            payload = dict(feedback)
            payload.setdefault("confidence", 1.0)
            payload.setdefault("source", "explicit")
            return payload
        raw = normalize_text(feedback)
        status = "positive"
        if any(token in raw.lower() for token in ["fail", "wrong", "bad", "error", "unsafe"]):
            status = "negative"
        return {"status": status, "comment": raw, "confidence": 1.0, "source": "explicit"}

    def _extract_experience(self, rollout: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        recent = self.knowledge_store.recent_rollouts(rollout["task_signature"], limit=5)
        positive_patterns = []
        negative_patterns = []
        for item in recent:
            text = normalize_text(item.get("context", {}).get("feedback") or item.get("result"))
            if not text:
                continue
            if any(word in text.lower() for word in ["good", "pass", "success"]):
                positive_patterns.append(text)
            if any(word in text.lower() for word in ["fail", "wrong", "unsafe", "error"]):
                negative_patterns.append(text)

        lesson = normalize_text(feedback.get("lesson") or feedback.get("suggestion") or feedback.get("comment"))
        if not lesson:
            result_text = normalize_text(rollout.get("result"))
            lesson = f"When handling {rollout['task_signature']}, prefer outputs like: {result_text[:120]}"
        if feedback.get("status") == "negative" and "avoid" not in lesson.lower():
            lesson = f"Avoid this failure pattern: {lesson}"

        critique = []
        if positive_patterns:
            critique.append(f"Common success pattern: {positive_patterns[-1][:120]}")
        if negative_patterns:
            critique.append(f"Common failure pattern: {negative_patterns[-1][:120]}")

        return {
            "experience_id": generate_id("bank-exp"),
            "recorded_at": utc_now_iso(),
            "task_signature": rollout["task_signature"],
            "feedback_status": feedback.get("status", "unknown"),
            "feedback_source": feedback.get("source", "unknown"),
            "feedback_confidence": float(feedback.get("confidence", 1.0)),
            "feedback_text": lesson,
            "lesson": lesson,
            "cross_rollout_critique": critique,
            "execution_id": rollout["execution_id"],
        }

    def _decide_skill_update(self, experience: Dict[str, Any]) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        skill_bank = self.knowledge_store.load_skill_bank()

        # Delegate to intelligence backend when available.
        if self._backend is not None:
            return self._decide_via_backend(experience, skill_bank)

        # Fallback: original Jaccard-threshold logic.
        return self._decide_local(experience, skill_bank)

    def _decide_via_backend(
        self, experience: Dict[str, Any], skill_bank: List[Dict[str, Any]]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        decision = self._backend.decide_update(experience=experience, skill_bank=skill_bank)  # type: ignore[union-attr]

        if decision.action == "discard":
            return (decision.to_dict(), skill_bank)

        if decision.action == "merge" and decision.target_skill_id:
            updated = []
            for skill in skill_bank:
                if skill["skill_entry_id"] != decision.target_skill_id:
                    updated.append(skill)
                    continue
                merged = dict(skill)
                merged["version"] = bump_patch_version(skill["version"])
                merged["content"] = decision.synthesized_content or self._merge_skill_content(skill["content"], experience)
                if decision.synthesized_keywords:
                    merged["keywords"] = decision.synthesized_keywords
                merged["updated_at"] = utc_now_iso()
                merged["source_experience_ids"] = list(skill.get("source_experience_ids", [])) + [experience["experience_id"]]
                updated.append(merged)
                # Auto-synthesize if content grew large.
                self._maybe_synthesize(merged)
            return (decision.to_dict(), updated)

        if decision.action == "supersede" and decision.target_skill_id:
            updated = []
            for skill in skill_bank:
                if skill["skill_entry_id"] != decision.target_skill_id:
                    updated.append(skill)
                    continue
                replaced = dict(skill)
                replaced["version"] = bump_patch_version(skill["version"])
                replaced["content"] = decision.synthesized_content
                if decision.synthesized_title:
                    replaced["title"] = decision.synthesized_title
                if decision.synthesized_keywords:
                    replaced["keywords"] = decision.synthesized_keywords
                replaced["updated_at"] = utc_now_iso()
                replaced["source_experience_ids"] = list(skill.get("source_experience_ids", [])) + [experience["experience_id"]]
                updated.append(replaced)
            return (decision.to_dict(), updated)

        # action == "add" (or fallback)
        new_skill = {
            "skill_entry_id": generate_id("skill"),
            "title": decision.synthesized_title or self._title_from_experience(experience),
            "content": decision.synthesized_content or self._new_skill_content(experience),
            "version": "0.1.0",
            "task_signature": experience["task_signature"],
            "keywords": decision.synthesized_keywords or tokenize_text(experience["lesson"])[:8],
            "source_experience_ids": [experience["experience_id"]],
            "updated_at": utc_now_iso(),
        }
        result = decision.to_dict()
        result["skill_entry_id"] = new_skill["skill_entry_id"]
        return (result, skill_bank + [new_skill])

    def _decide_local(
        self, experience: Dict[str, Any], skill_bank: List[Dict[str, Any]]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Original Jaccard-threshold decision logic (zero-dependency fallback)."""
        lesson = experience["lesson"]
        if self._should_discard(experience):
            return (
                {
                    "action": "discard",
                    "summary": f"Discard one-off experience {experience['experience_id']}",
                },
                skill_bank,
            )

        best_match = None
        best_score = 0.0
        for skill in skill_bank:
            score = jaccard_similarity(lesson, skill.get("content", ""))
            if skill.get("task_signature") == experience["task_signature"]:
                score += 0.2
            if score > best_score:
                best_match = skill
                best_score = score

        if best_match and best_score >= 0.35:
            updated = []
            for skill in skill_bank:
                if skill["skill_entry_id"] != best_match["skill_entry_id"]:
                    updated.append(skill)
                    continue
                merged_skill = dict(skill)
                merged_skill["version"] = bump_patch_version(skill["version"])
                merged_skill["content"] = self._merge_skill_content(skill["content"], experience)
                merged_skill["updated_at"] = utc_now_iso()
                merged_skill["source_experience_ids"] = list(skill.get("source_experience_ids", [])) + [experience["experience_id"]]
                updated.append(merged_skill)
                best_match = merged_skill
            return (
                {
                    "action": "merge",
                    "summary": f"Merge experience into skill {best_match['skill_entry_id']}",
                    "skill_entry_id": best_match["skill_entry_id"],
                },
                updated,
            )

        new_skill = {
            "skill_entry_id": generate_id("skill"),
            "title": self._title_from_experience(experience),
            "content": self._new_skill_content(experience),
            "version": "0.1.0",
            "task_signature": experience["task_signature"],
            "keywords": tokenize_text(experience["lesson"])[:8],
            "source_experience_ids": [experience["experience_id"]],
            "updated_at": utc_now_iso(),
        }
        return (
            {
                "action": "add",
                "summary": f"Add new learned skill {new_skill['skill_entry_id']}",
                "skill_entry_id": new_skill["skill_entry_id"],
            },
            skill_bank + [new_skill],
        )

    def _maybe_synthesize(self, skill: Dict[str, Any]) -> None:
        """Trigger synthesis if a skill's content has grown beyond the threshold."""
        if self._backend is None:
            return
        content = skill.get("content", "")
        bullet_count = sum(1 for line in content.splitlines() if line.strip().startswith("- "))
        if bullet_count >= _AUTO_SYNTHESIS_THRESHOLD:
            result = self._backend.synthesize_skill(skill=skill)
            skill["content"] = result.content
            if result.title:
                skill["title"] = result.title
            if result.keywords:
                skill["keywords"] = result.keywords

    @staticmethod
    def _should_discard(experience: Dict[str, Any]) -> bool:
        text = experience["lesson"].lower()
        return any(
            token in text
            for token in ["one-off", "temporary", "do not reuse", "ignore this", "一次性", "临时", "不要复用", "忽略这次"]
        )

    @staticmethod
    def _merge_skill_content(existing: str, experience: Dict[str, Any]) -> str:
        additions = [experience["lesson"], *experience.get("cross_rollout_critique", [])]
        lines = [line.strip() for line in existing.splitlines() if line.strip()]
        for addition in additions:
            bullet = f"- {addition}"
            if bullet not in lines:
                lines.append(bullet)
        return "\n".join(lines)

    @staticmethod
    def _new_skill_content(experience: Dict[str, Any]) -> str:
        lines = [
            f"# Learned Rule: {experience['task_signature']}",
            "",
            f"- {experience['lesson']}",
        ]
        for critique in experience.get("cross_rollout_critique", []):
            lines.append(f"- {critique}")
        return "\n".join(lines)

    @staticmethod
    def _title_from_experience(experience: Dict[str, Any]) -> str:
        return f"Learned {experience['task_signature']}".strip()

    def _build_file_patches(
        self,
        *,
        experience: Dict[str, Any],
        decision: Dict[str, Any],
        feedback: Dict[str, Any],
        rollout: Dict[str, Any],
        managed_files: List[Dict[str, Any]],
        rewriter=None,
        extra_actions: Optional[List[Dict[str, Any]]] = None,
        current_patches: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        if self.repair_planner is None:
            return {}
        return self.repair_planner.build_file_patches(
            experience=experience,
            decision=decision,
            feedback=feedback,
            rollout=rollout,
            managed_files=managed_files,
            rewriter=rewriter,
            extra_actions=extra_actions,
            current_patches=current_patches,
        )
