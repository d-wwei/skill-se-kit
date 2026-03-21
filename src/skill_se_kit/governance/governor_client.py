from __future__ import annotations

from typing import Any, Dict, Optional

from skill_se_kit.common import GovernanceError, dump_json, load_json, utc_now_iso


class GovernorClient:
    def __init__(self, workspace, protocol_adapter, version_store, audit_logger=None, provenance_store=None):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.version_store = version_store
        self._handshake: Optional[Dict[str, Any]] = None
        self.audit_logger = audit_logger
        self.provenance_store = provenance_store

    def detect_governor(self) -> bool:
        manifest = self.version_store.load_active_manifest()
        governance = manifest["governance"]
        return governance["mode"] == "governed" and bool(governance.get("governor_id"))

    def can_self_promote(self) -> bool:
        return not self.detect_governor()

    def handshake(
        self,
        *,
        governor_id: str,
        supported_min_version: str,
        supported_max_version: str,
        intended_mode: str = "governed",
    ) -> Dict[str, Any]:
        manifest = self.version_store.load_active_manifest()
        if manifest["governance"]["mode"] != "governed":
            raise GovernanceError("Handshake is only required in governed mode")
        protocol_version = self.protocol_adapter.get_supported_protocol_version()
        compatible = self.protocol_adapter.is_version_compatible(supported_min_version, supported_max_version)
        self._handshake = {
            "participant_id": manifest["skill_id"],
            "target_skill_id": manifest["skill_id"],
            "governor_id": governor_id,
            "protocol_version": protocol_version,
            "supported_range": [supported_min_version, supported_max_version],
            "intended_mode": intended_mode,
            "compatible": compatible,
            "checked_at": utc_now_iso(),
        }
        return dict(self._handshake)

    def submit_proposal(self, proposal_id: str) -> Dict[str, Any]:
        if not self.detect_governor():
            raise GovernanceError("Proposal submission requires governed mode")
        if not self._handshake or not self._handshake["compatible"]:
            raise GovernanceError("Cannot submit proposal before a compatible handshake")
        proposal_path = self.workspace.local_proposals_dir / f"{proposal_id}.json"
        proposal = load_json(proposal_path)
        if proposal["status"] != "candidate":
            raise GovernanceError("Only candidate proposals can be submitted")
        proposal["status"] = "submitted"
        proposal["submitted_at"] = utc_now_iso()
        self.protocol_adapter.validate_proposal(proposal)
        dump_json(proposal_path, proposal)
        if self.audit_logger is not None:
            self.audit_logger.record_event(
                event_type="proposal_submitted",
                subject_id=proposal_id,
                actor_id=self._handshake["governor_id"],
                details={"intended_mode": self._handshake["intended_mode"]},
            )
        return proposal

    def record_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        self.protocol_adapter.validate_decision(decision)
        dump_json(self.workspace.governed_decisions_dir / f"{decision['decision_id']}.json", decision)
        if self.audit_logger is not None:
            audit_event = self.audit_logger.record_event(
                event_type="governed_decision_recorded",
                subject_id=decision["decision_id"],
                actor_id=decision["decider"]["id"],
                details={"outcome": decision["outcome"], "proposal_id": decision["proposal_id"]},
                evidence_refs=decision.get("evidence_refs"),
            )
            self.audit_logger.write_summary(
                summary_type="governed_decision",
                subject_id=decision["decision_id"],
                title=f"Governor decision {decision['decision_id']}",
                summary=decision["reason"],
                refs=[audit_event["audit_id"], *decision.get("evidence_refs", [])],
            )
        if self.provenance_store is not None:
            self.provenance_store.record_artifact_lineage(
                artifact_id=decision["decision_id"],
                artifact_kind="promotion_decision",
                origin="governor",
                derived_from=[decision["proposal_id"]],
                metadata={"outcome": decision["outcome"]},
            )
        return decision
