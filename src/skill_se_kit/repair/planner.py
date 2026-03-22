from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import adapters


class RepairPlanner:
    def __init__(self, workspace, contract_store=None):
        self.workspace = workspace
        self.contract_store = contract_store
        self._adapters = {
            "replace_text": adapters.replace_text,
            "insert_after": adapters.insert_after,
            "append_text": adapters.append_text,
            "python_dict_set": adapters.python_dict_set,
            "python_list_add": adapters.python_list_add,
        }

    def register_adapter(self, name: str, adapter) -> None:
        self._adapters[name] = adapter

    def build_file_patches(
        self,
        *,
        experience: Dict[str, Any],
        decision: Dict[str, Any],
        feedback: Optional[Dict[str, Any]],
        rollout: Optional[Dict[str, Any]],
        managed_files: List[Dict[str, Any]],
        rewriter=None,
        extra_actions: Optional[List[Dict[str, Any]]] = None,
        current_patches: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        if rewriter is not None:
            return self._call_rewriter(
                rewriter,
                experience=experience,
                decision=decision,
                feedback=feedback,
                rollout=rollout,
                managed_files=managed_files,
                current_patches=current_patches or {},
            )

        actions = self.collect_actions(
            feedback=feedback,
            rollout=rollout,
            extra_actions=extra_actions,
        )
        if actions:
            return self._apply_actions(actions, managed_files, current_patches=current_patches)
        return self._default_patches(managed_files, experience["lesson"], current_patches=current_patches)

    def collect_actions(
        self,
        *,
        feedback: Optional[Dict[str, Any]],
        rollout: Optional[Dict[str, Any]],
        extra_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        for source in (feedback or {}, (rollout or {}).get("result") if isinstance((rollout or {}).get("result"), dict) else {}):
            if not isinstance(source, dict):
                continue
            for key in ("repair_actions", "optimization_actions"):
                for action in source.get(key, []) or []:
                    if isinstance(action, dict):
                        actions.append(dict(action))
        for action in extra_actions or []:
            if isinstance(action, dict):
                actions.append(dict(action))
        return actions

    @staticmethod
    def collect_evaluation_actions(evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        benchmark = evaluation.get("benchmark") or {}
        actions: List[Dict[str, Any]] = []
        for case in benchmark.get("cases", []):
            if case.get("candidate_pass", True):
                continue
            for action in case.get("repair_actions_on_fail", []) or []:
                if isinstance(action, dict):
                    actions.append(dict(action))
        return actions

    def _call_rewriter(self, rewriter, **payload) -> Dict[str, str]:
        try:
            signature = inspect.signature(rewriter)
            if len(signature.parameters) >= 6:
                return rewriter(
                    payload["experience"],
                    payload["decision"],
                    payload["managed_files"],
                    payload["feedback"],
                    payload["rollout"],
                    payload["current_patches"],
                )
        except (TypeError, ValueError):
            pass
        return rewriter(payload["experience"], payload["decision"], payload["managed_files"])

    def _apply_actions(
        self,
        actions: List[Dict[str, Any]],
        managed_files: List[Dict[str, Any]],
        *,
        current_patches: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        allowed_paths = {item["path"] for item in managed_files if item.get("path")}
        patches = dict(current_patches or {})
        for action in actions:
            path = action.get("path")
            adapter_name = action.get("adapter")
            if not path or path not in allowed_paths or adapter_name not in self._adapters:
                continue
            content = patches.get(path)
            if content is None:
                absolute = self.workspace.root / path
                content = absolute.read_text(encoding="utf-8") if absolute.exists() else ""
            updated = self._adapters[adapter_name](content, action)
            patches[path] = updated
        return patches

    def _default_patches(
        self,
        managed_files: List[Dict[str, Any]],
        lesson: str,
        *,
        current_patches: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        patches = dict(current_patches or {})
        for descriptor in managed_files:
            if descriptor.get("kind") not in {"markdown", "text"}:
                continue
            relpath = descriptor["path"]
            absolute = self.workspace.root / relpath
            current_text = patches.get(relpath)
            if current_text is None:
                current_text = absolute.read_text(encoding="utf-8") if absolute.exists() else ""
            patches[relpath] = self._append_learned_rule(current_text, lesson)
        return patches

    @staticmethod
    def _append_learned_rule(current_text: str, lesson: str) -> str:
        marker = "## Learned Evolution Rules"
        if marker not in current_text:
            suffix = "\n\n" if current_text.strip() else ""
            return f"{current_text.rstrip()}{suffix}{marker}\n- {lesson}\n"
        if lesson in current_text:
            return current_text
        return f"{current_text.rstrip()}\n- {lesson}\n"
