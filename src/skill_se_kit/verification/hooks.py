from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from skill_se_kit.common import dump_json, generate_id, list_json_files, load_json, utc_now_iso


VerificationHook = Callable[[Dict[str, Any], Dict[str, Any]], Any]


class VerificationHookRegistry:
    def __init__(self, workspace):
        self.workspace = workspace
        self._hooks: Dict[str, VerificationHook] = {}

    def register_hook(self, name: str, hook: VerificationHook) -> None:
        self._hooks[name] = hook

    def run_hooks(
        self,
        *,
        proposal_document: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        overall_status = "pass"
        for name, hook in self._hooks.items():
            raw_result = hook(proposal_document, context or {})
            result = self._normalize_result(name, raw_result)
            if result["status"] != "pass":
                overall_status = "fail"
            results.append(result)

        receipt = {
            "receipt_id": generate_id("verification"),
            "created_at": utc_now_iso(),
            "proposal_id": proposal_document["proposal_id"],
            "skill_id": proposal_document["skill_id"],
            "overall_status": overall_status,
            "hook_results": results,
        }
        dump_json(
            self.workspace.local_evaluations_dir / f"{receipt['receipt_id']}.verification.json",
            receipt,
        )
        return receipt

    def get_latest_receipt(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        latest: Optional[Dict[str, Any]] = None
        for path in list_json_files(self.workspace.local_evaluations_dir):
            if not path.name.endswith(".verification.json"):
                continue
            receipt = load_json(path)
            if receipt["proposal_id"] != proposal_id:
                continue
            if latest is None or receipt["created_at"] > latest["created_at"]:
                latest = receipt
        return latest

    @staticmethod
    def _normalize_result(name: str, raw_result: Any) -> Dict[str, Any]:
        if isinstance(raw_result, bool):
            return {
                "hook": name,
                "status": "pass" if raw_result else "fail",
                "details": "boolean hook result",
            }
        if isinstance(raw_result, dict):
            return {
                "hook": name,
                "status": raw_result.get("status", "pass"),
                "details": raw_result.get("details", ""),
                "metadata": raw_result.get("metadata", {}),
            }
        return {
            "hook": name,
            "status": "fail",
            "details": "unsupported hook result",
        }
