from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from skill_se_kit.common import dump_json, generate_id, load_json, parse_semver, utc_now_iso


class LocalEvaluator:
    def __init__(
        self,
        workspace,
        protocol_adapter,
        version_store,
        experience_store,
        audit_logger=None,
        provenance_store=None,
        verification_registry=None,
        regression_runner=None,
    ):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.version_store = version_store
        self.experience_store = experience_store
        self.audit_logger = audit_logger
        self.provenance_store = provenance_store
        self.verification_registry = verification_registry
        self.regression_runner = regression_runner

    def evaluate_proposal(
        self,
        proposal: Dict[str, Any] | str,
        *,
        source_origin: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        proposal_document = self._load_proposal(proposal)
        self.protocol_adapter.validate_proposal(proposal_document)
        result = {
            "evaluation_id": generate_id("evaluation"),
            "proposal_id": proposal_document["proposal_id"],
            "skill_id": proposal_document["skill_id"],
            "status": "pass",
            "reasons": [],
        }
        if parse_semver(proposal_document["target_version"]) < parse_semver(
            proposal_document.get("base_version", proposal_document["target_version"])
        ):
            result["status"] = "fail"
            result["reasons"].append("target_version is lower than base_version")

        for artifact in proposal_document.get("artifacts", []):
            if artifact["type"] == "manifest":
                candidate_manifest = load_json(self.workspace.root / artifact["ref"])
                self.protocol_adapter.validate_manifest(candidate_manifest)
        if not result["reasons"]:
            result["reasons"].append("protocol validation passed")

        verification_receipt = None
        if self.verification_registry is not None:
            verification_receipt = self.verification_registry.run_hooks(
                proposal_document=proposal_document,
                context={"source_origin": source_origin, **(metadata or {})},
            )
            result["verification_receipt_id"] = verification_receipt["receipt_id"]
            if verification_receipt["overall_status"] != "pass":
                result["status"] = "fail"
                result["reasons"].append("verification hooks failed")

        benchmark = None
        if self.regression_runner is not None:
            bundle = None
            bundle_path = self.workspace.local_proposals_dir / f"{proposal_document['proposal_id']}.bundle.json"
            if bundle_path.exists():
                bundle = load_json(bundle_path)
            benchmark = self.regression_runner.evaluate_candidate(proposal_document, bundle)
            result["benchmark"] = benchmark
            if benchmark["status"] == "fail":
                result["status"] = "fail"
                result["reasons"].append("candidate regressed on evaluation cases")

        result["evaluated_at"] = utc_now_iso()
        dump_json(
            self.workspace.local_evaluations_dir / f"{result['evaluation_id']}.json",
            result,
        )

        record = self.experience_store.record_experience(
            kind="evaluation",
            summary=f"Local evaluation {result['status']} for {proposal_document['proposal_id']}",
            source_origin=source_origin,
            outcome={
                "status": "positive" if result["status"] == "pass" else "negative",
                "impact": "medium",
            },
            related_ids={"proposal_id": proposal_document["proposal_id"]},
            metadata={"evaluation": result, **(metadata or {})},
        )
        result["experience_record_id"] = record["record_id"]
        if self.audit_logger is not None:
            evidence = self.audit_logger.record_evidence(
                evidence_type="evaluation_receipt",
                payload=result,
            )
            audit_event = self.audit_logger.record_event(
                event_type="proposal_evaluated",
                subject_id=proposal_document["proposal_id"],
                actor_id=source_origin,
                details={"evaluation_status": result["status"]},
                evidence_refs=[evidence["evidence_id"], record["record_id"]],
            )
            self.audit_logger.write_summary(
                summary_type="evaluation",
                subject_id=proposal_document["proposal_id"],
                title=f"Evaluation for {proposal_document['proposal_id']}",
                summary="; ".join(result["reasons"]),
                refs=[audit_event["audit_id"], evidence["evidence_id"], record["record_id"]],
            )
        if self.provenance_store is not None:
            self.provenance_store.record_artifact_lineage(
                artifact_id=result["evaluation_id"],
                artifact_kind="evaluation",
                origin=source_origin,
                derived_from=[proposal_document["proposal_id"]],
                metadata={"status": result["status"]},
            )
        return result

    def _load_proposal(self, proposal: Dict[str, Any] | str) -> Dict[str, Any]:
        if isinstance(proposal, dict):
            return proposal
        return load_json(self.workspace.local_proposals_dir / f"{proposal}.json")
