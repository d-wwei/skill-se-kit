from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from skill_se_kit.audit.logger import AuditLogger
from skill_se_kit.evaluation.local_evaluator import LocalEvaluator
from skill_se_kit.evaluation.regression_runner import RegressionRunner
from skill_se_kit.evolution.autonomous_engine import AutonomousEvolutionEngine
from skill_se_kit.evolution.overlay_applier import OverlayApplier
from skill_se_kit.evolution.proposal_generator import ProposalGenerator
from skill_se_kit.governance.governor_client import GovernorClient
from skill_se_kit.governance.local_promoter import LocalPromoter
from skill_se_kit.provenance.store import ProvenanceStore
from skill_se_kit.protocol.adapter import ProtocolAdapter
from skill_se_kit.storage.experience_store import ExperienceStore
from skill_se_kit.storage.knowledge_store import KnowledgeStore
from skill_se_kit.storage.skill_contract_store import SkillContractStore
from skill_se_kit.storage.version_store import VersionStore
from skill_se_kit.storage.workspace import SkillWorkspace
from skill_se_kit.verification.hooks import VerificationHookRegistry


class SkillRuntime:
    def __init__(self, *, skill_root: str | Path, protocol_root: str | Path):
        self.workspace = SkillWorkspace(skill_root)
        self.protocol_adapter = ProtocolAdapter(protocol_root)
        self.contract_store = SkillContractStore(self.workspace)
        self.version_store = VersionStore(self.workspace, self.protocol_adapter, self.contract_store)
        self.audit_logger = AuditLogger(self.workspace, self.version_store)
        self.provenance_store = ProvenanceStore(self.workspace, self.version_store)
        self.verification_registry = VerificationHookRegistry(self.workspace)
        self.knowledge_store = KnowledgeStore(self.workspace)
        self._executor = None
        self._rewriter = None
        self.experience_store = ExperienceStore(self.workspace, self.protocol_adapter, self.version_store)
        self.proposal_generator = ProposalGenerator(
            self.workspace,
            self.protocol_adapter,
            self.version_store,
            self.audit_logger,
            self.provenance_store,
        )
        self.overlay_applier = OverlayApplier(
            self.workspace,
            self.protocol_adapter,
            self.version_store,
            self.audit_logger,
            self.provenance_store,
        )
        self.governor_client = GovernorClient(
            self.workspace,
            self.protocol_adapter,
            self.version_store,
            self.audit_logger,
            self.provenance_store,
        )
        self.local_evaluator = LocalEvaluator(
            self.workspace,
            self.protocol_adapter,
            self.version_store,
            self.experience_store,
            self.audit_logger,
            self.provenance_store,
            self.verification_registry,
            RegressionRunner(self.workspace, self.contract_store, self.knowledge_store, self._get_executor),
        )
        self.local_promoter = LocalPromoter(
            self.workspace,
            self.protocol_adapter,
            self.version_store,
            self.governor_client,
            self.audit_logger,
            self.provenance_store,
            self.knowledge_store,
            self.contract_store,
        )
        self.autonomous_engine = AutonomousEvolutionEngine(
            self.workspace,
            self.version_store,
            self.knowledge_store,
            self.proposal_generator,
            self.local_evaluator,
            self.local_promoter,
            self.audit_logger,
            self.provenance_store,
            self.contract_store,
        )

    def execute(self, input: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._executor is not None:
            execution = self.autonomous_engine.execute(input, context, self._executor)
            if context and context.get("auto_learn") and context.get("feedback"):
                execution["autonomous_cycle"] = self.autonomous_improve(
                    execution["execution_id"],
                    feedback=context["feedback"],
                    auto_promote=context.get("auto_promote", True),
                )
            return execution
        manifest = self.version_store.load_active_manifest()
        response = {
            "skill_id": manifest["skill_id"],
            "active_version": manifest["version"],
            "governance_mode": manifest["governance"]["mode"],
            "can_self_promote": not self.detect_governor(),
            "input": input,
            "context": context or {},
        }
        if context and context.get("record_experience"):
            response["experience"] = self.record_experience(
                kind=context.get("experience_kind", "observation"),
                summary=context["record_experience"],
                source_origin=context.get("source_origin", "runtime"),
                metadata={"input": input},
            )
        return response

    def record_experience(self, **kwargs) -> Dict[str, Any]:
        return self.experience_store.record_experience(**kwargs)

    def generate_proposal(self, **kwargs) -> Dict[str, Any]:
        return self.proposal_generator.generate_proposal(**kwargs)

    def apply_overlay(self, overlay: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        if overlay is None:
            overlay = self.overlay_applier.build_overlay(**kwargs)
        return self.overlay_applier.apply_overlay(overlay)

    def evaluate_proposal(self, proposal: Dict[str, Any] | str, **kwargs) -> Dict[str, Any]:
        return self.local_evaluator.evaluate_proposal(proposal, **kwargs)

    def promote_candidate(self, proposal_id: str) -> Dict[str, Any]:
        return self.local_promoter.promote_candidate(proposal_id)

    def rollback(self, snapshot_id: str) -> Dict[str, Any]:
        return self.version_store.rollback(snapshot_id)

    def detect_governor(self) -> bool:
        return self.governor_client.detect_governor()

    def get_supported_protocol_version(self) -> str:
        return self.protocol_adapter.get_supported_protocol_version()

    def register_verification_hook(self, name: str, hook) -> None:
        self.verification_registry.register_hook(name, hook)

    def run_verification_hooks(self, proposal: Dict[str, Any] | str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        proposal_document = proposal
        if isinstance(proposal, str):
            proposal_document = self.local_evaluator._load_proposal(proposal)
        return self.verification_registry.run_hooks(proposal_document=proposal_document, context=context or {})

    def configure_integration(
        self,
        *,
        managed_files: Optional[list[Dict[str, Any]]] = None,
        evaluation_cases: Optional[list[Dict[str, Any]]] = None,
        auto_promote_min_improvement: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.contract_store.save_contract(
            managed_files=managed_files,
            evaluation_cases=evaluation_cases,
            auto_promote_min_improvement=auto_promote_min_improvement,
            metadata=metadata,
        )

    def register_executor(self, executor) -> None:
        self._executor = executor

    def register_rewriter(self, rewriter) -> None:
        self._rewriter = rewriter

    def autonomous_improve(
        self,
        execution_id: str,
        *,
        feedback: Dict[str, Any] | str,
        proposer_id: str = "autonomous-engine",
        auto_promote: bool = True,
    ) -> Dict[str, Any]:
        return self.autonomous_engine.learn_from_interaction(
            execution_id=execution_id,
            feedback=feedback,
            proposer_id=proposer_id,
            rewriter=self._rewriter,
            auto_promote=auto_promote,
        )

    def run_autonomous_cycle(
        self,
        input: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
        feedback: Dict[str, Any] | str,
        auto_promote: bool = True,
    ) -> Dict[str, Any]:
        execution = self.execute(input, context or {})
        execution["autonomous_cycle"] = self.autonomous_improve(
            execution["execution_id"],
            feedback=feedback,
            auto_promote=auto_promote,
        )
        return execution

    def _get_executor(self):
        return self._executor
