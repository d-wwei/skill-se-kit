__all__ = ["IntelligenceBackend", "LocalBackend", "LLMBackend"]


def __getattr__(name: str):
    if name == "IntelligenceBackend":
        from skill_se_kit.intelligence.backend import IntelligenceBackend

        return IntelligenceBackend
    if name == "LocalBackend":
        from skill_se_kit.intelligence.local_backend import LocalBackend

        return LocalBackend
    if name == "LLMBackend":
        from skill_se_kit.intelligence.llm_backend import LLMBackend

        return LLMBackend
    raise AttributeError(name)
