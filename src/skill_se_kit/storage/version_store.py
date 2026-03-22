from __future__ import annotations

from typing import Any, Dict, Optional

from skill_se_kit.common import GovernanceError, dump_json, generate_id, load_json, utc_now_iso
from skill_se_kit.storage.workspace import SkillWorkspace


class VersionStore:
    def __init__(self, workspace: SkillWorkspace, protocol_adapter, contract_store=None):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.contract_store = contract_store
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
            "local_skill_bank": load_json(self.workspace.local_skill_bank_path),
        }
        if include_official and self.workspace.official_manifest_path.exists():
            payload["official_manifest"] = self.load_official_manifest()
        if include_official and self.workspace.official_skill_bank_path.exists():
            payload["official_skill_bank"] = load_json(self.workspace.official_skill_bank_path)
        payload["managed_files"] = self._snapshot_managed_files()
        dump_json(self.workspace.snapshots_dir / f"{snapshot_id}.json", payload)
        return snapshot_id

    def rollback(self, snapshot_id: str) -> Dict[str, Any]:
        payload = load_json(self.workspace.snapshots_dir / f"{snapshot_id}.json")
        self.write_active_manifest(payload["active_manifest"])
        dump_json(self.workspace.local_skill_bank_path, payload.get("local_skill_bank", {"skills": []}))
        restored_official = False
        if "official_manifest" in payload and payload["active_manifest"]["governance"]["mode"] != "governed":
            dump_json(self.workspace.official_manifest_path, payload["official_manifest"])
            if "official_skill_bank" in payload:
                dump_json(self.workspace.official_skill_bank_path, payload["official_skill_bank"])
            restored_official = True
        self._restore_managed_files(payload.get("managed_files", {}))
        return {
            "snapshot_id": snapshot_id,
            "restored_active_manifest": True,
            "restored_official_manifest": restored_official,
        }

    def _snapshot_managed_files(self) -> Dict[str, str]:
        if self.contract_store is None:
            return {}
        managed_files = {}
        contract = self.contract_store.load_contract()
        for descriptor in contract.get("managed_files", []):
            path = self.workspace.root / descriptor["path"]
            managed_files[descriptor["path"]] = path.read_text(encoding="utf-8") if path.exists() else ""
        return managed_files

    def _restore_managed_files(self, managed_files: Dict[str, str]) -> None:
        for relative_path, content in managed_files.items():
            path = self.workspace.root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
