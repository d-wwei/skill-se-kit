from __future__ import annotations

from typing import Any, Dict, Optional

from skill_se_kit.common import dump_json, generate_id, utc_now_iso


class AuditLogger:
    def __init__(self, workspace, version_store):
        self.workspace = workspace
        self.version_store = version_store

    def record_event(
        self,
        *,
        event_type: str,
        subject_id: str,
        actor_id: str,
        details: Dict[str, Any],
        evidence_refs: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        manifest = self.version_store.load_active_manifest()
        event = {
            "audit_id": generate_id("audit"),
            "created_at": utc_now_iso(),
            "event_type": event_type,
            "skill_id": manifest["skill_id"],
            "governance_mode": manifest["governance"]["mode"],
            "subject_id": subject_id,
            "actor_id": actor_id,
            "details": details,
        }
        if evidence_refs:
            event["evidence_refs"] = evidence_refs
        dump_json(self.workspace.audit_decision_logs_dir / f"{event['audit_id']}.json", event)
        return event

    def write_summary(
        self,
        *,
        summary_type: str,
        subject_id: str,
        title: str,
        summary: str,
        refs: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        document = {
            "summary_id": generate_id("summary"),
            "created_at": utc_now_iso(),
            "summary_type": summary_type,
            "subject_id": subject_id,
            "title": title,
            "summary": summary,
        }
        if refs:
            document["refs"] = refs
        if metadata:
            document["metadata"] = metadata
        dump_json(self.workspace.audit_summaries_dir / f"{document['summary_id']}.json", document)
        return document

    def record_evidence(self, *, evidence_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "evidence_id": generate_id("evidence"),
            "created_at": utc_now_iso(),
            "evidence_type": evidence_type,
            "payload": payload,
        }
        dump_json(self.workspace.audit_evidence_dir / f"{record['evidence_id']}.json", record)
        return record

