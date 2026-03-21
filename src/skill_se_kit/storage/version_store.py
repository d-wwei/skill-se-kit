from __future__ import annotations

from typing import Any, Dict, Optional

from skill_se_kit.common import GovernanceError, dump_json, generate_id, load_json, utc_now_iso
from skill_se_kit.storage.workspace import SkillWorkspace


class VersionStore:
    def __init__(self, workspace: SkillWorkspace, protocol_adapter):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.workspace.ensure_layout()

    def load_active_manifest(self) -> Dict[str, Any]:
        manifest = load_json(self.workspace.manifest_path)
        self.protocol_adapter.validate_manifest(manifest)
        return manifest

    def load_official_manifest(self) -> Dict[str, Any]:
        manifest = load_json(self.workspace.official_manifest_path)
        self.protocol_adapter.validate_manifest(manifest)
        return manifest

    def write_active_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        self.protocol_adapter.validate_manifest(manifest)
        dump_json(self.workspace.manifest_path, manifest)
        return manifest

    def write_official_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        current = self.load_active_manifest()
        if current["governance"]["mode"] == "governed":
            raise GovernanceError("Governed mode forbids local official writes")
        self.protocol_adapter.validate_manifest(manifest)
        dump_json(self.workspace.official_manifest_path, manifest)
        return manifest

    def create_snapshot(self, reason: str, include_official: bool = True) -> str:
        snapshot_id = generate_id("snapshot")
        payload: Dict[str, Any] = {
            "snapshot_id": snapshot_id,
            "created_at": utc_now_iso(),
            "reason": reason,
            "active_manifest": self.load_active_manifest(),
        }
        if include_official and self.workspace.official_manifest_path.exists():
            payload["official_manifest"] = self.load_official_manifest()
        dump_json(self.workspace.snapshots_dir / f"{snapshot_id}.json", payload)
        return snapshot_id

    def rollback(self, snapshot_id: str) -> Dict[str, Any]:
        payload = load_json(self.workspace.snapshots_dir / f"{snapshot_id}.json")
        self.write_active_manifest(payload["active_manifest"])
        restored_official = False
        if "official_manifest" in payload and payload["active_manifest"]["governance"]["mode"] != "governed":
            dump_json(self.workspace.official_manifest_path, payload["official_manifest"])
            restored_official = True
        return {
            "snapshot_id": snapshot_id,
            "restored_active_manifest": True,
            "restored_official_manifest": restored_official,
        }
