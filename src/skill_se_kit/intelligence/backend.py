"""Abstract intelligence backend for pluggable semantic capabilities.

The IntelligenceBackend defines the contract for the four "intelligence"
operations that SE-Kit delegates to:

1. **retrieve** – semantic retrieval of relevant skills and experiences
2. **extract_feedback** – structured feedback extraction from interaction
3. **decide_update** – skill add/merge/discard/supersede decision with content synthesis
4. **synthesize_skill** – compress, deduplicate, and resolve conflicts in skill content
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class RetrievalResult:
    """Result of a retrieval operation."""

    __slots__ = ("skills", "experiences")

    def __init__(
        self,
        skills: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
    ):
        self.skills = skills
        self.experiences = experiences

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {"skills": self.skills, "experiences": self.experiences}


class FeedbackResult:
    """Result of feedback extraction."""

    __slots__ = ("status", "lesson", "source", "confidence", "reasoning")

    def __init__(
        self,
        *,
        status: str,
        lesson: str,
        source: str,
        confidence: float,
        reasoning: str = "",
    ):
        self.status = status
        self.lesson = lesson
        self.source = source
        self.confidence = confidence
        self.reasoning = reasoning

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": self.status,
            "lesson": self.lesson,
            "source": self.source,
            "confidence": self.confidence,
        }
        if self.reasoning:
            result["reasoning"] = self.reasoning
        return result


class UpdateDecision:
    """Result of a skill-update decision."""

    __slots__ = (
        "action",
        "summary",
        "target_skill_id",
        "synthesized_content",
        "synthesized_title",
        "synthesized_keywords",
        "reasoning",
        "conflicts_resolved",
    )

    def __init__(
        self,
        *,
        action: str,
        summary: str,
        target_skill_id: str = "",
        synthesized_content: str = "",
        synthesized_title: str = "",
        synthesized_keywords: Optional[List[str]] = None,
        reasoning: str = "",
        conflicts_resolved: Optional[List[str]] = None,
    ):
        self.action = action
        self.summary = summary
        self.target_skill_id = target_skill_id
        self.synthesized_content = synthesized_content
        self.synthesized_title = synthesized_title
        self.synthesized_keywords = synthesized_keywords or []
        self.reasoning = reasoning
        self.conflicts_resolved = conflicts_resolved or []

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"action": self.action, "summary": self.summary}
        if self.target_skill_id:
            result["skill_entry_id"] = self.target_skill_id
        if self.reasoning:
            result["reasoning"] = self.reasoning
        if self.conflicts_resolved:
            result["conflicts_resolved"] = self.conflicts_resolved
        return result


class SynthesisResult:
    """Result of skill content synthesis/compression."""

    __slots__ = ("content", "title", "keywords", "removed_count", "conflicts_resolved")

    def __init__(
        self,
        *,
        content: str,
        title: str = "",
        keywords: Optional[List[str]] = None,
        removed_count: int = 0,
        conflicts_resolved: Optional[List[str]] = None,
    ):
        self.content = content
        self.title = title
        self.keywords = keywords or []
        self.removed_count = removed_count
        self.conflicts_resolved = conflicts_resolved or []


class IntelligenceBackend(ABC):
    """Abstract base for intelligence backends.

    Implementations:
    - ``LocalBackend``:  Zero-dependency, Jaccard-based (current behavior).
    - ``LLMBackend``:    Delegates to a user-provided LLM callable.
    """

    @abstractmethod
    def retrieve(
        self,
        *,
        query_text: str,
        skills: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> RetrievalResult:
        """Return the most relevant skills and experiences for *query_text*."""

    @abstractmethod
    def extract_feedback(
        self,
        *,
        user_input: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        result: Any,
    ) -> FeedbackResult:
        """Extract structured feedback from an interaction."""

    @abstractmethod
    def decide_update(
        self,
        *,
        experience: Dict[str, Any],
        skill_bank: List[Dict[str, Any]],
    ) -> UpdateDecision:
        """Decide how to incorporate *experience* into *skill_bank*.

        Possible actions: ``add``, ``merge``, ``discard``, ``supersede``.
        When action is ``merge`` or ``supersede``, *synthesized_content*
        should contain the rewritten (compressed, conflict-free) skill body.
        """

    @abstractmethod
    def synthesize_skill(
        self,
        *,
        skill: Dict[str, Any],
    ) -> SynthesisResult:
        """Compress and deduplicate a skill's accumulated content.

        Called periodically or when bullet count exceeds a threshold.
        """

    # ------------------------------------------------------------------
    # Optional: embedding support (only meaningful for vector backends)
    # ------------------------------------------------------------------

    def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Return embedding vectors for *texts*, or ``None`` if unsupported."""
        return None
