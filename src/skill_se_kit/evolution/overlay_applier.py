from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from skill_se_kit.common import (
    GovernanceError,
    SUPPORTED_PROTOCOL_VERSION,
    deep_copy_json,
    dump_json,
    generate_id,
    load_json,
    remove_pointer_value,
    set_pointer_value,
    utc_now_iso,
)


class OverlayApplier:
    def __init__(self, workspace, protocol_adapter, version_store, audit_logger=None, provenance_store=None):
        self.workspace = workspace
        self.protocol_adapter = protocol_adapter
        self.version_store = version_store
        self.audit_logger = audit_logger
        self.provenance_store = provenance_store

    def build_overlay(
        self,
        *,
        overlay_type: str,
        operations: list,
        authority: str = "local",
        status: str = "draft",
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        manifest = self.version_store.load_active_manifest()
        overlay = {
            "schema_name": "Overlay",
            "schema_version": "1.0.0",
            "protocol_version": SUPPORTED_PROTOCOL_VERSION,
            "overlay_id": generate_id("overlay"),
            "target": {
                "skill_id": manifest["skill_id"],
                "base_version": manifest["version"],
            },
            "created_at": utc_now_iso(),
            "authority": authority,
            "overlay_type": overlay_type,
            "status": status,
            "payload": {
                "operations": operations,
            },
        }
        if metadata:
            overlay["metadata"] = metadata
        self.protocol_adapter.validate_overlay(overlay)
        return overlay

    def apply_overlay(self, overlay: Dict[str, Any]) -> Dict[str, Any]:
        active_manifest = self.version_store.load_active_manifest()
        self.protocol_adapter.validate_overlay(overlay)
        self.version_store.create_snapshot(f"apply overlay {overlay['overlay_id']}")
        self._guard_overlay(active_manifest, overlay)

        updated_manifest = deep_copy_json(active_manifest)
        for operation in overlay["payload"]["operations"]:
            op = operation["op"]
            path = operation["path"]
            value = operation.get("value")
            if op == "set" or op == "replace":
                set_pointer_value(updated_manifest, path, value)
            elif op == "append":
                set_pointer_value(updated_manifest, path, value, append=True)
            elif op == "remove":
                remove_pointer_value(updated_manifest, path)
            else:
                raise ValueError(f"Unsupported overlay op: {op}")

        self.protocol_adapter.validate_manifest(updated_manifest)
        self.version_store.write_active_manifest(updated_manifest)
        overlay = deep_copy_json(overlay)
        if overlay["status"] == "draft":
            overlay["status"] = "active"
        self._supersede_existing_overlay(updated_manifest, overlay)
        overlay_dir = self.workspace.local_overlays_dir if overlay["authority"] == "local" else self.workspace.governed_overlays_dir
        dump_json(overlay_dir / f"{overlay['overlay_id']}.json", overlay)
        if self.audit_logger is not None:
            audit_event = self.audit_logger.record_event(
                event_type="overlay_applied",
                subject_id=overlay["overlay_id"],
                actor_id=overlay["authority"],
                details={
                    "overlay_type": overlay["overlay_type"],
                    "target_version": overlay["target"]["base_version"],
                    "status": overlay["status"],
                },
            )
            self.audit_logger.write_summary(
                summary_type="overlay",
                subject_id=overlay["overlay_id"],
                title=f"Overlay {overlay['overlay_id']} applied",
                summary=f"Applied {overlay['overlay_type']} overlay in {overlay['authority']} scope.",
                refs=[audit_event["audit_id"]],
            )
        if self.provenance_store is not None:
            self.provenance_store.record_artifact_lineage(
                artifact_id=overlay["overlay_id"],
                artifact_kind="overlay",
                origin=overlay["authority"],
                derived_from=[overlay["target"]["base_version"]],
                metadata={"overlay_type": overlay["overlay_type"]},
            )
        return overlay

    def _guard_overlay(self, manifest: Dict[str, Any], overlay: Dict[str, Any]) -> None:
        if manifest["governance"]["mode"] != "governed":
            return
        if overlay["authority"] == "governor":
            return
        for operation in overlay["payload"]["operations"]:
            if operation["path"].startswith("/governance/official_status") and operation.get("value") == "official":
                raise GovernanceError("Local overlays cannot mark a governed skill as official")

    def _supersede_existing_overlay(self, manifest: Dict[str, Any], overlay: Dict[str, Any]) -> None:
        overlay_dir = self.workspace.local_overlays_dir if overlay["authority"] == "local" else self.workspace.governed_overlays_dir
        for path in overlay_dir.glob("*.json"):
            current = load_json(path)
            if (
                current["status"] == "active"
                and current["overlay_type"] == overlay["overlay_type"]
                and current["target"]["skill_id"] == overlay["target"]["skill_id"]
            ):
                current["status"] = "superseded"
                current["supersedes_overlay_id"] = overlay["overlay_id"]
                self.protocol_adapter.validate_overlay(current)
                dump_json(path, current)
