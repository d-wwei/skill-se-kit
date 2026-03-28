__version__ = "0.2.0"

__all__ = [
    "EasyIntegrator",
    "IntelligenceBackend",
    "LLMBackend",
    "LocalBackend",
    "SkillRuntime",
    "__version__",
    "initialize_auto_integration",
]


def __getattr__(name: str):
    if name == "SkillRuntime":
        from skill_se_kit.runtime.skill_runtime import SkillRuntime

        return SkillRuntime
    if name == "EasyIntegrator":
        from skill_se_kit.integration.easy_mode import EasyIntegrator

        return EasyIntegrator
    if name == "initialize_auto_integration":
        from skill_se_kit.integration.auto_bootstrap import initialize_auto_integration

        return initialize_auto_integration
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
