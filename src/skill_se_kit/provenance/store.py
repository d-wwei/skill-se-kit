from __future__ import annotations

from typing import Any, Dict, Optional

from skill_se_kit.common import dump_json, generate_id, utc_now_iso


class ProvenanceStore:
    def __init__(self, workspace, version_store):
        self.workspace = workspace
        self.version_store = version_store

    def record_source(
        self,
        *,
        source_kind: str,
        ref: str,
        recorded_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        manifest = self.version_store.load_active_manifest()
        source = {
            "source_id": generate_id("source"),
            "recorded_at": utc_now_iso(),
            "skill_id": manifest["skill_id"],
            "source_kind": source_kind,
            "ref": ref,
            "recorded_by": recorded_by,
        }
        if metadata:
            source["metadata"] = metadata
        dump_json(self.workspace.provenance_sources_dir / f"{source['source_id']}.json", source)
        return source

    def record_artifact_lineage(
        self,
        *,
        artifact_id: str,
        artifact_kind: str,
        origin: str,
        derived_from: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        manifest = self.version_store.load_active_manifest()
        lineage = {
            "lineage_id": generate_id("lineage"),
            "recorded_at": utc_now_iso(),
            "skill_id": manifest["skill_id"],
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "origin": origin,
        }
        if derived_from:
            lineage["derived_from"] = derived_from
        if metadata:
            lineage["metadata"] = metadata
        dump_json(self.workspace.provenance_lineage_dir / f"{lineage['lineage_id']}.json", lineage)
        return lineage

