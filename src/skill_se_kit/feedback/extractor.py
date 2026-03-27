from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from skill_se_kit.common import ensure_list, normalize_text

if TYPE_CHECKING:
    from skill_se_kit.intelligence.backend import IntelligenceBackend


class AutoFeedbackExtractor:
    PREFERENCE_TOKENS = [
        "always",
        "never",
        "must",
        "should",
        "prefer",
        "do not",
        "don't",
        "avoid",
        "每次都",
        "一定要",
        "必须",
        "应该",
        "优先",
        "尽量",
        "不要",
        "别",
        "避免",
    ]

    NEGATIVE_TOKENS = [
        "error",
        "exception",
        "failed",
        "unsafe",
        "wrong",
        "timeout",
        "错误",
        "异常",
        "失败",
        "不安全",
        "不对",
        "超时",
    ]

    def __init__(self, intelligence_backend: "IntelligenceBackend | None" = None):
        self._backend = intelligence_backend

    def set_intelligence_backend(self, backend: "IntelligenceBackend") -> None:
        self._backend = backend

    def extract(
        self,
        *,
        input: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        result: Any,
        explicit_feedback: Dict[str, Any] | str | None = None,
    ) -> Dict[str, Any]:
        if explicit_feedback is not None:
            return self._normalize_explicit(explicit_feedback)

        # Delegate to intelligence backend when available.
        if self._backend is not None:
            fb = self._backend.extract_feedback(
                user_input=input, context=context, result=result,
            )
            return fb.to_dict()

        # Fallback: keyword-based extraction.
        user_text = self._collect_user_text(input, context)
        lesson = self._extract_preference_lesson(user_text)
        outcome = self._infer_outcome(result)

        if lesson:
            status = "negative" if outcome["failed"] else "positive"
            return {
                "status": status,
                "lesson": lesson,
                "source": "user_input",
                "confidence": 0.8,
            }

        if outcome["failed"]:
            return {
                "status": "negative",
                "lesson": f"Avoid this failure pattern: {outcome['reason']}",
                "source": "execution_result",
                "confidence": 0.7,
            }

        result_text = outcome["text"]
        if result_text:
            return {
                "status": "positive",
                "lesson": f"When handling similar requests, prefer outputs like: {result_text[:160]}",
                "source": "execution_result",
                "confidence": 0.45,
            }

        return {
            "status": "positive",
            "lesson": "Keep the current execution approach for similar tasks.",
            "source": "default",
            "confidence": 0.2,
        }

    def _collect_user_text(self, input: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
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

    def _extract_preference_lesson(self, user_text: str) -> str:
        lowered = user_text.lower()
        if not lowered:
            return ""
        for token in self.PREFERENCE_TOKENS:
            haystack = lowered if token.isascii() else user_text
            if token in haystack:
                return normalize_text(user_text)
        return ""

    def _infer_outcome(self, result: Any) -> Dict[str, Any]:
        if isinstance(result, dict):
            text = normalize_text(result.get("text") or result.get("message") or result.get("output") or "")
            error = normalize_text(result.get("error") or "")
            status = normalize_text(result.get("status") or "")
            exit_code = result.get("exit_code")
            failed = bool(error) or status in {"fail", "failed", "error"} or (exit_code not in (None, 0))
            if not failed and any(token in text.lower() for token in self.NEGATIVE_TOKENS):
                failed = True
            reason = error or status or text
            return {"failed": failed, "reason": reason, "text": text}
        text = normalize_text(result)
        failed = any(token in text.lower() for token in self.NEGATIVE_TOKENS)
        return {"failed": failed, "reason": text, "text": text}

    @staticmethod
    def _normalize_explicit(feedback: Dict[str, Any] | str) -> Dict[str, Any]:
        if isinstance(feedback, dict):
            return dict(feedback)
        raw = normalize_text(feedback)
        return {"status": "positive", "lesson": raw, "source": "explicit", "confidence": 1.0}
