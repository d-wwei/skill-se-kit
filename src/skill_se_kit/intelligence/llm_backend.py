"""LLM-powered intelligence backend.

Delegates the four intelligence operations to a user-provided LLM callable,
giving SE-Kit genuine semantic understanding for retrieval, feedback
extraction, skill-update decisions, and content synthesis.

Usage::

    from skill_se_kit.intelligence import LLMBackend

    def my_llm(prompt: str) -> str:
        # Call any LLM API — OpenAI, Anthropic, local model, etc.
        return openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        ).choices[0].message.content

    backend = LLMBackend(llm=my_llm)
    runtime.register_intelligence_backend(backend)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from skill_se_kit.common import jaccard_similarity, normalize_text, tokenize_text

from .backend import (
    FeedbackResult,
    IntelligenceBackend,
    RetrievalResult,
    SynthesisResult,
    UpdateDecision,
)
from .local_backend import LocalBackend

logger = logging.getLogger(__name__)

# Maximum number of skills/experiences to send in prompts to keep token use bounded.
_MAX_CANDIDATES_IN_PROMPT = 20

# Bullet-count threshold for triggering synthesis inside decide_update.
_SYNTHESIS_BULLET_THRESHOLD = 15


class LLMBackend(IntelligenceBackend):
    """Intelligence backend powered by an LLM callable.

    Parameters
    ----------
    llm:
        ``Callable[[str], str]`` — takes a prompt string, returns a
        completion string.  The backend handles prompt construction
        and response parsing internally.
    fallback:
        An ``IntelligenceBackend`` to fall back to if the LLM call
        fails or returns unparseable output.  Defaults to ``LocalBackend()``.
    """

    def __init__(
        self,
        *,
        llm: Callable[[str], str],
        fallback: Optional[IntelligenceBackend] = None,
    ):
        self._llm = llm
        self._fallback = fallback or LocalBackend()

    # ------------------------------------------------------------------
    # 1. Retrieval: LLM reranks pre-filtered candidates
    # ------------------------------------------------------------------

    def retrieve(
        self,
        *,
        query_text: str,
        skills: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> RetrievalResult:
        # Stage 1: Broad Jaccard pre-filter to limit prompt size.
        pre_skills = _prefilter(query_text, skills, key_fn=_skill_text, limit=_MAX_CANDIDATES_IN_PROMPT)
        pre_experiences = _prefilter(query_text, experiences, key_fn=_experience_text, limit=_MAX_CANDIDATES_IN_PROMPT)

        if not pre_skills and not pre_experiences:
            return RetrievalResult(skills=[], experiences=[])

        # Stage 2: LLM reranks.
        prompt = _build_retrieval_prompt(query_text, pre_skills, pre_experiences, top_k)
        try:
            raw = self._llm(prompt)
            parsed = _parse_json_response(raw)
            if parsed is not None:
                return _build_retrieval_result(parsed, pre_skills, pre_experiences, top_k)
        except Exception:
            logger.debug("LLM retrieval failed, falling back to local", exc_info=True)

        return self._fallback.retrieve(
            query_text=query_text, skills=skills, experiences=experiences, top_k=top_k,
        )

    # ------------------------------------------------------------------
    # 2. Feedback extraction: LLM understands context
    # ------------------------------------------------------------------

    def extract_feedback(
        self,
        *,
        user_input: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        result: Any,
    ) -> FeedbackResult:
        prompt = _build_feedback_prompt(user_input, context, result)
        try:
            raw = self._llm(prompt)
            parsed = _parse_json_response(raw)
            if parsed is not None:
                return FeedbackResult(
                    status=str(parsed.get("status", "positive")),
                    lesson=str(parsed.get("lesson", "")),
                    source="llm",
                    confidence=float(parsed.get("confidence", 0.5)),
                    reasoning=str(parsed.get("reasoning", "")),
                )
        except Exception:
            logger.debug("LLM feedback extraction failed, falling back", exc_info=True)

        return self._fallback.extract_feedback(
            user_input=user_input, context=context, result=result,
        )

    # ------------------------------------------------------------------
    # 3. Skill update decision: LLM reasons about add/merge/discard
    # ------------------------------------------------------------------

    def decide_update(
        self,
        *,
        experience: Dict[str, Any],
        skill_bank: List[Dict[str, Any]],
    ) -> UpdateDecision:
        prompt = _build_decision_prompt(experience, skill_bank)
        try:
            raw = self._llm(prompt)
            parsed = _parse_json_response(raw)
            if parsed is not None:
                action = str(parsed.get("action", "add"))
                if action not in ("add", "merge", "discard", "supersede"):
                    action = "add"
                return UpdateDecision(
                    action=action,
                    summary=str(parsed.get("summary", "")),
                    target_skill_id=str(parsed.get("target_skill_id", "")),
                    synthesized_content=str(parsed.get("synthesized_content", "")),
                    synthesized_title=str(parsed.get("synthesized_title", "")),
                    synthesized_keywords=list(parsed.get("synthesized_keywords", [])),
                    reasoning=str(parsed.get("reasoning", "")),
                    conflicts_resolved=list(parsed.get("conflicts_resolved", [])),
                )
        except Exception:
            logger.debug("LLM decision failed, falling back", exc_info=True)

        return self._fallback.decide_update(experience=experience, skill_bank=skill_bank)

    # ------------------------------------------------------------------
    # 4. Skill synthesis: LLM compresses and resolves conflicts
    # ------------------------------------------------------------------

    def synthesize_skill(self, *, skill: Dict[str, Any]) -> SynthesisResult:
        content = skill.get("content", "")
        bullet_count = sum(1 for line in content.splitlines() if line.strip().startswith("- "))
        if bullet_count < _SYNTHESIS_BULLET_THRESHOLD:
            return self._fallback.synthesize_skill(skill=skill)

        prompt = _build_synthesis_prompt(skill)
        try:
            raw = self._llm(prompt)
            parsed = _parse_json_response(raw)
            if parsed is not None:
                return SynthesisResult(
                    content=str(parsed.get("content", content)),
                    title=str(parsed.get("title", skill.get("title", ""))),
                    keywords=list(parsed.get("keywords", skill.get("keywords", []))),
                    removed_count=int(parsed.get("removed_count", 0)),
                    conflicts_resolved=list(parsed.get("conflicts_resolved", [])),
                )
        except Exception:
            logger.debug("LLM synthesis failed, falling back", exc_info=True)

        return self._fallback.synthesize_skill(skill=skill)


# ======================================================================
# Prompt builders
# ======================================================================

def _build_retrieval_prompt(
    query: str,
    skills: List[Dict[str, Any]],
    experiences: List[Dict[str, Any]],
    top_k: int,
) -> str:
    skill_block = "\n".join(
        f"  SKILL[{i}] id={s.get('skill_entry_id','?')} title={s.get('title','')} | {s.get('content','')[:200]}"
        for i, s in enumerate(skills)
    )
    exp_block = "\n".join(
        f"  EXP[{i}] id={e.get('experience_id','?')} | {e.get('lesson','')[:200]}"
        for i, e in enumerate(experiences)
    )
    return f"""You are a semantic retrieval engine. Given a query and candidate skills/experiences, return the {top_k} most semantically relevant items from each category.

QUERY: {query}

CANDIDATE SKILLS:
{skill_block or '  (none)'}

CANDIDATE EXPERIENCES:
{exp_block or '  (none)'}

Return a JSON object (no markdown fences) with two keys:
- "skill_indices": list of up to {top_k} integers (indices into SKILL[]) ordered by relevance, most relevant first
- "experience_indices": list of up to {top_k} integers (indices into EXP[]) ordered by relevance, most relevant first
- "reasoning": one sentence explaining your ranking

Only include genuinely relevant items. If nothing is relevant, return empty lists."""


def _build_feedback_prompt(
    user_input: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    result: Any,
) -> str:
    ctx_str = json.dumps(context, default=str, ensure_ascii=False)[:800] if context else "{}"
    result_str = json.dumps(result, default=str, ensure_ascii=False)[:800] if isinstance(result, dict) else str(result)[:800]
    return f"""You are a feedback extraction engine. Analyze the following interaction and extract structured feedback.

USER INPUT: {json.dumps(user_input, default=str, ensure_ascii=False)[:600]}

CONTEXT: {ctx_str}

EXECUTION RESULT: {result_str}

Determine:
1. Is there an actionable lesson or preference expressed? (not just casual speech)
2. Was the execution successful or failed?

Return a JSON object (no markdown fences):
- "status": "positive" or "negative"
- "lesson": a concise, reusable lesson (empty string if no real lesson found)
- "confidence": float 0.0-1.0 (how certain you are this is a genuine lesson)
- "reasoning": one sentence explaining your assessment

IMPORTANT: Do NOT extract lessons from:
- Casual questions ("I'm not sure what I should do")
- Statements about past events ("The analysis must have been wrong")
- Non-directive uses of modal verbs ("this should work")
Only extract genuine preferences, instructions, or patterns."""


def _build_decision_prompt(
    experience: Dict[str, Any],
    skill_bank: List[Dict[str, Any]],
) -> str:
    bank_block = "\n".join(
        f"  SKILL[{i}] id={s.get('skill_entry_id','?')} title={s.get('title','')}\n    content: {s.get('content','')[:300]}"
        for i, s in enumerate(skill_bank[:_MAX_CANDIDATES_IN_PROMPT])
    )
    return f"""You are a skill evolution engine. Given a new experience and the existing skill bank, decide how to update the skill bank.

NEW EXPERIENCE:
  id: {experience.get('experience_id', '?')}
  task_signature: {experience.get('task_signature', '')}
  lesson: {experience.get('lesson', '')}
  feedback_status: {experience.get('feedback_status', '')}
  cross_rollout_critique: {experience.get('cross_rollout_critique', [])}

EXISTING SKILL BANK ({len(skill_bank)} skills):
{bank_block or '  (empty)'}

Choose ONE action:
- "add": Create a new skill (no existing skill covers this lesson)
- "merge": Merge into an existing skill (combine, don't just append — synthesize the content)
- "discard": This experience is one-off/temporary, not worth keeping
- "supersede": Replace an existing skill's content entirely (the new lesson contradicts or improves upon it fundamentally)

Return a JSON object (no markdown fences):
- "action": one of "add", "merge", "discard", "supersede"
- "target_skill_id": the skill_entry_id to merge into or supersede (empty for add/discard)
- "synthesized_content": the FULL new skill content (for add/merge/supersede). For merge, combine existing + new into coherent prose/bullets — do NOT just append.
- "synthesized_title": skill title (for add, or if the title needs updating)
- "synthesized_keywords": list of 3-8 semantic keywords
- "reasoning": one sentence explaining your decision
- "conflicts_resolved": list of any contradictions you resolved (empty if none)"""


def _build_synthesis_prompt(skill: Dict[str, Any]) -> str:
    return f"""You are a knowledge compression engine. The following skill has accumulated many bullet points and needs to be compressed into a coherent, deduplicated, non-contradictory summary.

SKILL TITLE: {skill.get('title', '')}
TASK SIGNATURE: {skill.get('task_signature', '')}

CURRENT CONTENT:
{skill.get('content', '')}

Instructions:
1. Identify and remove duplicate or near-duplicate bullets
2. Detect contradictions — resolve in favor of the more specific or recent item
3. Group related bullets into coherent principles
4. Compress into 3-8 clear, actionable rules
5. Preserve all genuinely distinct insights

Return a JSON object (no markdown fences):
- "content": the rewritten skill content (markdown with structured bullets)
- "title": updated title if needed (or original)
- "keywords": 3-8 semantic keywords
- "removed_count": number of bullets removed/merged
- "conflicts_resolved": list of any contradictions you resolved"""


# ======================================================================
# Response parsing helpers
# ======================================================================

def _parse_json_response(raw: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from an LLM response, tolerating markdown fences."""
    text = raw.strip()
    # Strip common markdown code fences.
    if text.startswith("```"):
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    return None


# ======================================================================
# Pre-filter and result building
# ======================================================================

def _skill_text(skill: Dict[str, Any]) -> str:
    return " ".join([
        normalize_text(skill.get("title")),
        normalize_text(skill.get("content")),
        " ".join(skill.get("keywords", [])),
    ])


def _experience_text(exp: Dict[str, Any]) -> str:
    return " ".join([
        normalize_text(exp.get("lesson")),
        normalize_text(exp.get("feedback_text")),
        normalize_text(exp.get("task_signature")),
    ])


def _prefilter(
    query: str,
    items: List[Dict[str, Any]],
    key_fn: Callable[[Dict[str, Any]], str],
    limit: int,
) -> List[Dict[str, Any]]:
    """Broad Jaccard pre-filter to limit prompt size."""
    if len(items) <= limit:
        return list(items)
    scored = [(jaccard_similarity(query, key_fn(item)), item) for item in items]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [item for _, item in scored[:limit]]


def _build_retrieval_result(
    parsed: Dict[str, Any],
    skills: List[Dict[str, Any]],
    experiences: List[Dict[str, Any]],
    top_k: int,
) -> RetrievalResult:
    """Build RetrievalResult from LLM-parsed indices."""
    skill_indices = parsed.get("skill_indices", [])
    exp_indices = parsed.get("experience_indices", [])

    ranked_skills = []
    for rank, idx in enumerate(skill_indices[:top_k]):
        if isinstance(idx, int) and 0 <= idx < len(skills):
            score = 1.0 - rank * 0.1  # Descending score from LLM rank
            ranked_skills.append(dict(skills[idx], retrieval_score=max(score, 0.1)))

    ranked_experiences = []
    for rank, idx in enumerate(exp_indices[:top_k]):
        if isinstance(idx, int) and 0 <= idx < len(experiences):
            score = 1.0 - rank * 0.1
            ranked_experiences.append(dict(experiences[idx], retrieval_score=max(score, 0.1)))

    return RetrievalResult(skills=ranked_skills, experiences=ranked_experiences)
