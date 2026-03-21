from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from skill_se_kit.common import SUPPORTED_PROTOCOL_VERSION, dump_json, generate_id, utc_now_iso


class ProposalGenerator:
    def __init__(self, workspace, protocol_adapter, version_store, audit_logger=None, provenance_store=None):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.version_store = version_store
        self.audit_logger = audit_logger
        self.provenance_store = provenance_store

    def generate_proposal(
        self,
        *,
        change_summary: str,
        proposer_id: str,
        proposal_type: str = "skill_update",
        target_manifest: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        active_manifest = self.version_store.load_active_manifest()
        proposal_id = generate_id("proposal")
        artifact_refs = list(artifacts or [])
        base_version = active_manifest["version"]
        target_version = base_version

        if target_manifest is not None:
            self.protocol_adapter.validate_manifest(target_manifest)
            target_version = target_manifest["version"]
            manifest_path = self.workspace.local_proposals_dir / f"{proposal_id}.manifest.json"
            dump_json(manifest_path, target_manifest)
            artifact_refs.append({"type": "manifest", "ref": str(manifest_path.relative_to(self.workspace.root))})

        proposal = {
            "schema_name": "SkillProposal",
            "schema_version": "1.0.0",
            "protocol_version": SUPPORTED_PROTOCOL_VERSION,
            "proposal_id": proposal_id,
            "skill_id": active_manifest["skill_id"],
            "created_at": utc_now_iso(),
            "proposer": {
                "authority": "local",
                "id": proposer_id,
            },
            "status": "candidate",
            "proposal_type": proposal_type,
            "base_version": base_version,
            "target_version": target_version,
            "change_summary": change_summary,
        }
        if artifact_refs:
            proposal["artifacts"] = artifact_refs
        if metadata:
            proposal["metadata"] = metadata
        self.protocol_adapter.validate_proposal(proposal)
        dump_json(self.workspace.local_proposals_dir / f"{proposal_id}.json", proposal)
        if self.audit_logger is not None:
            audit_event = self.audit_logger.record_event(
                event_type="proposal_created",
                subject_id=proposal_id,
                actor_id=proposer_id,
                details={
                    "proposal_type": proposal_type,
                    "target_version": target_version,
                    "artifact_count": len(artifact_refs),
                },
            )
            self.audit_logger.write_summary(
                summary_type="proposal",
                subject_id=proposal_id,
                title=f"Proposal {proposal_id} created",
                summary=change_summary,
                refs=[audit_event["audit_id"]],
            )
        if self.provenance_store is not None:
            self.provenance_store.record_artifact_lineage(
                artifact_id=proposal_id,
                artifact_kind="proposal",
                origin="local",
                derived_from=[base_version],
                metadata={"target_version": target_version},
            )
        return proposal
