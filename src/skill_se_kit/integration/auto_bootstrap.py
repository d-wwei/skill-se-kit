from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from skill_se_kit.common import dump_json, load_json, normalize_text, utc_now_iso
from skill_se_kit.storage.workspace import SkillWorkspace


AUTO_SKILL_BLOCK_START = "<!-- skill-se-kit:auto-runtime:start -->"
AUTO_SKILL_BLOCK_END = "<!-- skill-se-kit:auto-runtime:end -->"


def discover_protocol_root(start: str | Path) -> Optional[Path]:
    current = Path(start).expanduser().resolve()
    search_roots = [current, *current.parents]
    candidate_names = ("skill-evolution-protocol", "protocol")
    for root in search_roots:
        for candidate in candidate_names:
            path = root / candidate
            if _is_protocol_root(path):
                return path
        for sibling in root.iterdir() if root.exists() else []:
            if sibling.is_dir() and _is_protocol_root(sibling):
                return sibling
    return None


def discover_executor_spec(skill_root: str | Path) -> Dict[str, Any]:
    root = Path(skill_root).expanduser().resolve()
    for candidate in _python_candidates(root):
        functions = _discover_callable_names(candidate)
        for name in ("execute", "run", "main"):
            if name in functions:
                return {
                    "kind": "python_file",
                    "path": str(candidate.relative_to(root)),
                    "callable": name,
                    "discovered_by": "python_entrypoint",
                }

    command = _discover_shell_command(root)
    if command is not None:
        return {
            "kind": "shell_command",
            "command": command,
            "discovered_by": "shell_entrypoint",
        }

    return {
        "kind": "passive",
        "discovered_by": "passive_capture",
        "notes": "No conventional entrypoint was found. The kit will observe user intent and execution context until an executor is configured.",
    }


def load_executor_from_spec(skill_root: str | Path, executor_spec: Dict[str, Any]):
    root = Path(skill_root).expanduser().resolve()
    kind = executor_spec.get("kind")
    if kind == "python_file":
        path = root / executor_spec["path"]
        callable_name = executor_spec.get("callable", "execute")
        module_name = f"skill_se_kit_auto_{path.stem}_{abs(hash(str(path)))}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load executor module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        executor = getattr(module, callable_name, None)
        if executor is None:
            raise RuntimeError(f"Executor callable '{callable_name}' not found in {path}")
        return executor

    if kind == "shell_command":
        command = list(executor_spec.get("command") or [])

        def _shell_executor(input_payload, context):
            env = dict(os.environ)
            env["SKILL_SE_KIT_INPUT_JSON"] = json.dumps(input_payload, ensure_ascii=False)
            env["SKILL_SE_KIT_CONTEXT_JSON"] = json.dumps(context or {}, ensure_ascii=False)
            process = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                env=env,
            )
            return {
                "status": "ok" if process.returncode == 0 else "failed",
                "exit_code": process.returncode,
                "text": normalize_text(process.stdout),
                "error": normalize_text(process.stderr),
                "command": command,
            }

        return _shell_executor

    def _passive_executor(input_payload, context):
        user_text = normalize_text((context or {}).get("user_input") or input_payload)
        return {
            "status": "passive",
            "text": user_text or "Passive capture recorded.",
            "message": "Skill-SE-Kit is active in passive observation mode.",
        }

    return _passive_executor


def initialize_auto_integration(
    *,
    skill_root: str | Path,
    protocol_root: str | Path,
    runtime_mode: str = "auto",
    executor_spec: Optional[Dict[str, Any]] = None,
    auto_feedback: bool = True,
    human_reports: bool = True,
    managed_files: Optional[list[Dict[str, Any]]] = None,
    evaluation_cases: Optional[list[Dict[str, Any]]] = None,
    auto_promote_min_improvement: float = 0.0,
    min_feedback_confidence: float = 0.35,
    patch_skill_markdown: bool = True,
) -> Dict[str, Any]:
    workspace = SkillWorkspace(skill_root)
    workspace.ensure_layout()
    executor = executor_spec or discover_executor_spec(skill_root)
    managed = managed_files or _discover_managed_files(skill_root)
    payload = {
        "configured_at": utc_now_iso(),
        "skill_root": str(Path(skill_root).expanduser().resolve()),
        "protocol_root": str(Path(protocol_root).expanduser().resolve()),
        "runtime_mode": runtime_mode,
        "auto_feedback": bool(auto_feedback),
        "human_reports": bool(human_reports),
        "auto_promote_min_improvement": float(auto_promote_min_improvement),
        "min_feedback_confidence": float(min_feedback_confidence),
        "managed_files": managed,
        "evaluation_cases": evaluation_cases or [],
        "executor": executor,
    }
    dump_json(workspace.auto_integration_path, payload)
    if patch_skill_markdown:
        _patch_skill_markdown(workspace.root, payload)
    return payload


def load_auto_integration_config(skill_root: str | Path) -> Dict[str, Any]:
    workspace = SkillWorkspace(skill_root)
    return load_json(workspace.auto_integration_path)


def _is_protocol_root(path: Path) -> bool:
    return path.is_dir() and (path / "versions" / "current.json").exists() and (path / "schemas").exists()


def _python_candidates(root: Path):
    candidates = [
        root / "executor.py",
        root / "main.py",
        root / "run.py",
        root / "app.py",
        root / "scripts" / "executor.py",
        root / "scripts" / "main.py",
        root / "scripts" / "run.py",
    ]
    return [path for path in candidates if path.exists() and path.is_file()]


def _discover_callable_names(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _discover_shell_command(root: Path) -> Optional[list[str]]:
    candidates = [
        root / "main.sh",
        root / "run.sh",
        root / "scripts" / "run.sh",
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return ["/bin/sh", str(path.relative_to(root))]
    single_script = sorted((root / "scripts").glob("*.py")) if (root / "scripts").exists() else []
    if len(single_script) == 1:
        return [sys.executable, str(single_script[0].relative_to(root))]
    return None


def _discover_managed_files(skill_root: str | Path) -> list[Dict[str, Any]]:
    root = Path(skill_root).expanduser().resolve()
    managed = []
    if (root / "SKILL.md").exists():
        managed.append({"path": "SKILL.md", "kind": "markdown"})
    if (root / "README.md").exists():
        managed.append({"path": "README.md", "kind": "markdown"})
    return managed


def _patch_skill_markdown(skill_root: Path, payload: Dict[str, Any]) -> None:
    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        return
    block = "\n".join(
        [
            AUTO_SKILL_BLOCK_START,
            "## Skill-SE-Kit Auto Runtime",
            "",
            "This skill is auto-managed by Skill-SE-Kit.",
            f"- Runtime mode: `{payload['runtime_mode']}`",
            f"- Wrapper command: `skill-se-kit run --skill-root {skill_root}`",
            "- Human evolution summary: `reports/evolution/latest.md`",
            "- If a task result or user preference implies a reusable lesson, keep routing execution through the wrapper so the kit can learn automatically.",
            AUTO_SKILL_BLOCK_END,
        ]
    )
    current = skill_md.read_text(encoding="utf-8")
    if AUTO_SKILL_BLOCK_START in current and AUTO_SKILL_BLOCK_END in current:
        before, _, tail = current.partition(AUTO_SKILL_BLOCK_START)
        _, _, after = tail.partition(AUTO_SKILL_BLOCK_END)
        updated = f"{before.rstrip()}\n\n{block}\n{after.lstrip()}"
    else:
        updated = f"{current.rstrip()}\n\n{block}\n"
    skill_md.write_text(updated, encoding="utf-8")
