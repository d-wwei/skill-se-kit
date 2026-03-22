from __future__ import annotations

from typing import Any, Dict, List, Optional

from skill_se_kit.common import dump_json, load_json


class SkillContractStore:
    def __init__(self, workspace):
        self.workspace = workspace
        self.workspace.ensure_layout()

    def load_contract(self) -> Dict[str, Any]:
        if not self.workspace.skill_contract_path.exists():
            return {
                "managed_files": [],
                "evaluation_cases": [],
                "auto_promote_min_improvement": 0.0,
            }
        return load_json(self.workspace.skill_contract_path)

    def save_contract(
        self,
        *,
        managed_files: Optional[List[Dict[str, Any]]] = None,
        evaluation_cases: Optional[List[Dict[str, Any]]] = None,
        auto_promote_min_improvement: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        contract = self.load_contract()
        if managed_files is not None:
            contract["managed_files"] = managed_files
        if evaluation_cases is not None:
            contract["evaluation_cases"] = evaluation_cases
        contract["auto_promote_min_improvement"] = float(auto_promote_min_improvement)
        if metadata is not None:
            contract["metadata"] = metadata
        dump_json(self.workspace.skill_contract_path, contract)
        return contract

