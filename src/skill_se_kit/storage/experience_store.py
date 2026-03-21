from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from skill_se_kit.common import SUPPORTED_PROTOCOL_VERSION, dump_json, generate_id, utc_now_iso
from skill_se_kit.storage.workspace import SkillWorkspace


class ExperienceStore:
    def __init__(self, workspace: SkillWorkspace, protocol_adapter, version_store):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.version_store = version_store
        self.workspace.ensure_layout()

    def record_experience(
        self,
        *,
        kind: str,
        summary: str,
        source_origin: str,
        outcome: Optional[Dict[str, Any]] = None,
        evidence: Optional[list] = None,
        related_ids: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        authority: str = "local",
    ) -> Dict[str, Any]:
        manifest = self.version_store.load_active_manifest()
        record = {
            "schema_name": "ExperienceRecord",
            "schema_version": "1.0.0",
            "protocol_version": SUPPORTED_PROTOCOL_VERSION,
            "record_id": generate_id("exp"),
            "skill_id": manifest["skill_id"],
            "recorded_at": utc_now_iso(),
            "source": {
                "authority": authority,
                "origin": source_origin,
            },
            "kind": kind,
            "summary": summary,
        }
        if evidence:
            record["evidence"] = evidence
        if outcome:
            record["outcome"] = outcome
        if related_ids:
            record["related_ids"] = related_ids
        if metadata:
            record["metadata"] = metadata
        self.protocol_adapter.validate_experience(record)
        dump_json(self.workspace.local_experiences_dir / f"{record['record_id']}.json", record)
        return record
