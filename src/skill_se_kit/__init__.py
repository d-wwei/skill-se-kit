__all__ = ["EasyIntegrator", "SkillRuntime", "initialize_auto_integration"]


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
    raise AttributeError(name)
