from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from skill_se_kit.runtime.skill_runtime import SkillRuntime


class EasyIntegrator:
    def __init__(self, runtime: SkillRuntime):
        self.runtime = runtime

    def integrate(
        self,
        *,
        manifest: Optional[Dict[str, Any]] = None,
        executor,
        run_mode: str = "auto",
        evaluation_cases: Optional[list[Dict[str, Any]]] = None,
        managed_files: Optional[list[Dict[str, Any]]] = None,
        auto_feedback: bool = True,
        human_reports: bool = True,
        auto_promote_min_improvement: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SkillRuntime:
        if manifest is not None:
            self.runtime.workspace.bootstrap(manifest)
        else:
            self.runtime.workspace.ensure_layout()
        self.runtime.register_executor(executor)
        self.runtime.configure_integration(
            managed_files=managed_files,
            evaluation_cases=evaluation_cases,
            auto_promote_min_improvement=auto_promote_min_improvement,
            runtime_mode=run_mode,
            auto_feedback=auto_feedback,
            human_reports=human_reports,
            metadata=metadata,
        )
        return self.runtime

    @classmethod
    def one_click(
        cls,
        *,
        skill_root: str | Path,
        protocol_root: str | Path,
        manifest: Optional[Dict[str, Any]] = None,
        executor,
        run_mode: str = "auto",
        evaluation_cases: Optional[list[Dict[str, Any]]] = None,
        managed_files: Optional[list[Dict[str, Any]]] = None,
        auto_feedback: bool = True,
        human_reports: bool = True,
        auto_promote_min_improvement: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SkillRuntime:
        runtime = SkillRuntime(skill_root=skill_root, protocol_root=protocol_root)
        integrator = cls(runtime)
        return integrator.integrate(
            manifest=manifest,
            executor=executor,
            run_mode=run_mode,
            evaluation_cases=evaluation_cases,
            managed_files=managed_files,
            auto_feedback=auto_feedback,
            human_reports=human_reports,
            auto_promote_min_improvement=auto_promote_min_improvement,
            metadata=metadata,
        )
