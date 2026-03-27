"""Zero-dependency intelligence backend using Jaccard similarity.

This wraps the original SE-Kit logic so it remains available as a
deterministic, zero-API-call fallback.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from skill_se_kit.common import jaccard_similarity, normalize_text, tokenize_text

from .backend import (
    FeedbackResult,
    IntelligenceBackend,
    RetrievalResult,
    SynthesisResult,
    UpdateDecision,
)

PREFERENCE_TOKENS = [
    "always", "never", "must", "should", "prefer", "do not", "don't", "avoid",
    "每次都", "一定要", "必须", "应该", "优先", "尽量", "不要", "别", "避免",
]

NEGATIVE_TOKENS = [
    "error", "exception", "failed", "unsafe", "wrong", "timeout",
    "错误", "异常", "失败", "不安全", "不对", "超时",
]

DISCARD_TOKENS = [
    "one-off", "temporary", "do not reuse", "ignore this",
    "一次性", "临时", "不要复用", "忽略这次",
]

_MERGE_THRESHOLD = 0.35
_TASK_SIGNATURE_BOOST = 0.2


class LocalBackend(IntelligenceBackend):
    """Jaccard-similarity backend (original SE-Kit behaviour)."""

    def retrieve(
        self,
        *,
        query_text: str,
        skills: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> RetrievalResult:
        scored_skills: List[tuple[float, Dict[str, Any]]] = []
        for skill in skills:
            score = jaccard_similarity(
                query_text,
                " ".join([
                    normalize_text(skill.get("title")),
                    normalize_text(skill.get("content")),
                    " ".join(skill.get("keywords", [])),
                ]),
            )
            if score > 0:
                scored_skills.append((score, skill))

        scored_experiences: List[tuple[float, Dict[str, Any]]] = []
        for exp in experiences:
            score = jaccard_similarity(
                query_text,
                " ".join([
                    normalize_text(exp.get("lesson")),
                    normalize_text(exp.get("feedback_text")),
                    normalize_text(exp.get("task_signature")),
                ]),
            )
            if score > 0:
                scored_experiences.append((score, exp))

        scored_skills.sort(key=lambda t: t[0], reverse=True)
        scored_experiences.sort(key=lambda t: t[0], reverse=True)
        return RetrievalResult(
            skills=[dict(s, retrieval_score=sc) for sc, s in scored_skills[:top_k]],
            experiences=[dict(e, retrieval_score=sc) for sc, e in scored_experiences[:top_k]],
        )

    def extract_feedback(
        self,
        *,
        user_input: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        result: Any,
    ) -> FeedbackResult:
        user_text = _collect_user_text(user_input, context)
        lesson = _extract_preference_lesson(user_text)
        outcome = _infer_outcome(result)

        if lesson:
            status = "negative" if outcome["failed"] else "positive"
            return FeedbackResult(status=status, lesson=lesson, source="user_input", confidence=0.8)

        if outcome["failed"]:
            return FeedbackResult(
                status="negative",
                lesson=f"Avoid this failure pattern: {outcome['reason']}",
                source="execution_result",
                confidence=0.7,
            )

        result_text = outcome["text"]
        if result_text:
            return FeedbackResult(
                status="positive",
                lesson=f"When handling similar requests, prefer outputs like: {result_text[:160]}",
                source="execution_result",
                confidence=0.45,
            )

        return FeedbackResult(
            status="positive",
            lesson="Keep the current execution approach for similar tasks.",
            source="default",
            confidence=0.2,
        )

    def decide_update(
        self,
        *,
        experience: Dict[str, Any],
        skill_bank: List[Dict[str, Any]],
    ) -> UpdateDecision:
        lesson = experience["lesson"]

        if _should_discard(experience):
            return UpdateDecision(
                action="discard",
                summary=f"Discard one-off experience {experience['experience_id']}",
            )

        best_match: Optional[Dict[str, Any]] = None
        best_score = 0.0
        for skill in skill_bank:
            score = jaccard_similarity(lesson, skill.get("content", ""))
            if skill.get("task_signature") == experience["task_signature"]:
                score += _TASK_SIGNATURE_BOOST
            if score > best_score:
                best_match = skill
                best_score = score

        if best_match and best_score >= _MERGE_THRESHOLD:
            merged_content = _merge_skill_content(best_match["content"], experience)
            return UpdateDecision(
                action="merge",
                summary=f"Merge experience into skill {best_match['skill_entry_id']}",
                target_skill_id=best_match["skill_entry_id"],
                synthesized_content=merged_content,
            )

        title = f"Learned {experience['task_signature']}".strip()
        content = _new_skill_content(experience)
        keywords = tokenize_text(experience["lesson"])[:8]
        return UpdateDecision(
            action="add",
            summary=f"Add new learned skill",
            synthesized_content=content,
            synthesized_title=title,
            synthesized_keywords=keywords,
        )

    def synthesize_skill(self, *, skill: Dict[str, Any]) -> SynthesisResult:
        # LocalBackend cannot truly synthesize — just deduplicate lines.
        content = skill.get("content", "")
        lines = content.splitlines()
        seen: set[str] = set()
        deduped: list[str] = []
        removed = 0
        for line in lines:
            stripped = line.strip()
            if stripped in seen and stripped.startswith("- "):
                removed += 1
                continue
            seen.add(stripped)
            deduped.append(line)
        return SynthesisResult(
            content="\n".join(deduped),
            title=skill.get("title", ""),
            keywords=list(skill.get("keywords", [])),
            removed_count=removed,
        )


# ---------------------------------------------------------------------------
# Helpers (extracted from original inline code)
# ---------------------------------------------------------------------------

def _collect_user_text(input: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
    from skill_se_kit.common import ensure_list

    parts = [normalize_text(input)]
    if context:
        parts.extend(
            normalize_text(context.get(key))
            for key in ("user_input", "query", "goal", "instruction")
            if context.get(key)
        )
        for message in ensure_list(context.get("user_messages")):
            parts.append(normalize_text(message))
    return " ".join(part for part in parts if part).strip()


def _extract_preference_lesson(user_text: str) -> str:
    lowered = user_text.lower()
    if not lowered:
        return ""
    for token in PREFERENCE_TOKENS:
        haystack = lowered if token.isascii() else user_text
        if token in haystack:
            return normalize_text(user_text)
    return ""


def _infer_outcome(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):
        text = normalize_text(result.get("text") or result.get("message") or result.get("output") or "")
        error = normalize_text(result.get("error") or "")
        status = normalize_text(result.get("status") or "")
        exit_code = result.get("exit_code")
        failed = bool(error) or status in {"fail", "failed", "error"} or (exit_code not in (None, 0))
        if not failed and any(tok in text.lower() for tok in NEGATIVE_TOKENS):
            failed = True
        reason = error or status or text
        return {"failed": failed, "reason": reason, "text": text}
    text = normalize_text(result)
    failed = any(tok in text.lower() for tok in NEGATIVE_TOKENS)
    return {"failed": failed, "reason": text, "text": text}


def _should_discard(experience: Dict[str, Any]) -> bool:
    text = experience["lesson"].lower()
    return any(token in text for token in DISCARD_TOKENS)


def _merge_skill_content(existing: str, experience: Dict[str, Any]) -> str:
    additions = [experience["lesson"], *experience.get("cross_rollout_critique", [])]
    lines = [line.strip() for line in existing.splitlines() if line.strip()]
    for addition in additions:
        bullet = f"- {addition}"
        if bullet not in lines:
            lines.append(bullet)
    return "\n".join(lines)


def _new_skill_content(experience: Dict[str, Any]) -> str:
    lines = [
        f"# Learned Rule: {experience['task_signature']}",
        "",
        f"- {experience['lesson']}",
    ]
    for critique in experience.get("cross_rollout_critique", []):
        lines.append(f"- {critique}")
    return "\n".join(lines)
