from __future__ import annotations

from typing import Any, Dict

from skill_se_kit.common import GovernanceError, dump_json, generate_id, list_json_files, load_json, utc_now_iso


class LocalPromoter:
    def __init__(
        self,
        workspace,
        protocol_adapter,
        version_store,
        governor_client,
        audit_logger=None,
        provenance_store=None,
    ):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.version_store = version_store
        self.governor_client = governor_client
        self.audit_logger = audit_logger
        self.provenance_store = provenance_store

    def promote_candidate(self, proposal_id: str) -> Dict[str, Any]:
        if not self.governor_client.can_self_promote():
            raise GovernanceError("Governed mode forbids self-promotion")
        proposal = load_json(self.workspace.local_proposals_dir / f"{proposal_id}.json")
        self.protocol_adapter.validate_proposal(proposal)
        evaluation = self._latest_passed_evaluation(proposal_id)
        if evaluation is None:
            raise GovernanceError("Local promotion requires a passing evaluation receipt")
        manifest_artifact = self._find_manifest_artifact(proposal)
        if manifest_artifact is None:
            raise GovernanceError("Local promotion requires a manifest artifact")
        candidate_manifest = load_json(self.workspace.root / manifest_artifact["ref"])
        self.protocol_adapter.validate_manifest(candidate_manifest)
        snapshot_id = self.version_store.create_snapshot(f"promote candidate {proposal_id}")

        candidate_manifest["governance"]["official_status"] = "official"
        candidate_manifest.setdefault("metadata", {})
        candidate_manifest["metadata"]["official_scope"] = "local"

        self.version_store.write_active_manifest(candidate_manifest)
        self.version_store.write_official_manifest(candidate_manifest)

        receipt = {
            "promotion_id": generate_id("local-promotion"),
            "proposal_id": proposal_id,
            "skill_id": proposal["skill_id"],
            "promoted_at": utc_now_iso(),
            "snapshot_id": snapshot_id,
            "target_version": candidate_manifest["version"],
            "official_scope": "local",
        }
        dump_json(self.workspace.local_promotions_dir / f"{receipt['promotion_id']}.json", receipt)
        if self.audit_logger is not None:
            audit_event = self.audit_logger.record_event(
                event_type="local_promotion",
                subject_id=receipt["promotion_id"],
                actor_id="local-promoter",
                details={"proposal_id": proposal_id, "target_version": candidate_manifest["version"]},
                evidence_refs=[evaluation["evaluation_id"]],
            )
            self.audit_logger.write_summary(
                summary_type="promotion",
                subject_id=receipt["promotion_id"],
                title=f"Local promotion {receipt['promotion_id']}",
                summary=f"Promoted proposal {proposal_id} to local official version {candidate_manifest['version']}.",
                refs=[audit_event["audit_id"], evaluation["evaluation_id"]],
            )
        if self.provenance_store is not None:
            self.provenance_store.record_artifact_lineage(
                artifact_id=receipt["promotion_id"],
                artifact_kind="local_promotion",
                origin="local",
                derived_from=[proposal_id, evaluation["evaluation_id"]],
                metadata={"target_version": candidate_manifest["version"]},
            )
        return receipt

    @staticmethod
    def _find_manifest_artifact(proposal: Dict[str, Any]) -> Dict[str, Any] | None:
        for artifact in proposal.get("artifacts", []):
            if artifact["type"] == "manifest":
                return artifact
        return None

    def _latest_passed_evaluation(self, proposal_id: str) -> Dict[str, Any] | None:
        latest = None
        for path in list_json_files(self.workspace.local_evaluations_dir):
            if path.name.endswith(".verification.json"):
                continue
            receipt = load_json(path)
            if receipt.get("proposal_id") != proposal_id:
                continue
            if latest is None or receipt["evaluated_at"] > latest["evaluated_at"]:
                latest = receipt
        if latest and latest["status"] == "pass":
            return latest
        return None
