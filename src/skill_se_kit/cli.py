from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from skill_se_kit.common import normalize_text
from skill_se_kit.integration.auto_bootstrap import (
    discover_protocol_root,
    initialize_auto_integration,
)
from skill_se_kit.runtime.skill_runtime import SkillRuntime


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return int(handler(args) or 0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skill-se-kit")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Auto-bootstrap a skill workspace for Skill-SE-Kit.")
    init_parser.add_argument("--skill-root", default=".")
    init_parser.add_argument("--protocol-root")
    init_parser.add_argument("--run-mode", default="auto", choices=["off", "manual", "auto"])
    init_parser.add_argument("--min-feedback-confidence", type=float, default=0.35)
    init_parser.add_argument("--no-skill-md-patch", action="store_true")
    init_parser.set_defaults(handler=_handle_init)

    run_parser = subparsers.add_parser("run", help="Run a skill through the auto-integration wrapper.")
    run_parser.add_argument("--skill-root", default=".")
    run_parser.add_argument("--input-json", required=True)
    run_parser.add_argument("--context-json")
    run_parser.add_argument("--feedback-json")
    run_parser.add_argument("--run-mode", choices=["off", "manual", "auto"])
    run_parser.add_argument("--auto-promote", dest="auto_promote", action="store_true", default=None)
    run_parser.add_argument("--no-auto-promote", dest="auto_promote", action="store_false")
    run_parser.set_defaults(handler=_handle_run)

    report_parser = subparsers.add_parser("report", help="Print the latest human-readable evolution summary.")
    report_parser.add_argument("--skill-root", default=".")
    report_parser.set_defaults(handler=_handle_report)

    rollback_parser = subparsers.add_parser("rollback", help="Rollback to a recorded snapshot.")
    rollback_parser.add_argument("--skill-root", default=".")
    rollback_parser.add_argument("--snapshot-id", required=True)
    rollback_parser.set_defaults(handler=_handle_rollback)
    return parser


def _handle_init(args) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    protocol_root = args.protocol_root or discover_protocol_root(skill_root)
    if protocol_root is None:
        raise SystemExit("Could not discover protocol root. Pass --protocol-root explicitly.")

    runtime = SkillRuntime(skill_root=skill_root, protocol_root=protocol_root)
    manifest = None
    if runtime.workspace.manifest_path.exists():
        from skill_se_kit.common import load_json

        manifest = load_json(runtime.workspace.manifest_path)
    else:
        manifest = _default_manifest(skill_root.name, runtime.get_supported_protocol_version())
    runtime.workspace.bootstrap(manifest)

    config = initialize_auto_integration(
        skill_root=skill_root,
        protocol_root=protocol_root,
        runtime_mode=args.run_mode,
        min_feedback_confidence=args.min_feedback_confidence,
        patch_skill_markdown=not args.no_skill_md_patch,
    )
    runtime.configure_integration(
        managed_files=config["managed_files"],
        evaluation_cases=config["evaluation_cases"],
        auto_promote_min_improvement=config["auto_promote_min_improvement"],
        runtime_mode=config["runtime_mode"],
        auto_feedback=config["auto_feedback"],
        human_reports=config["human_reports"],
        min_feedback_confidence=config["min_feedback_confidence"],
        metadata={"auto_init": True, "executor": config["executor"]},
    )

    print(
        json.dumps(
            {
                "status": "initialized",
                "skill_root": str(skill_root),
                "protocol_root": str(protocol_root),
                "runtime_mode": config["runtime_mode"],
                "executor_kind": config["executor"]["kind"],
                "auto_integration_config": str(runtime.workspace.auto_integration_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _handle_run(args) -> int:
    runtime = SkillRuntime.from_auto_integration(args.skill_root)
    result = runtime.run_integrated_skill(
        _parse_json(args.input_json),
        context=_parse_optional_json(args.context_json),
        feedback=_parse_optional_json(args.feedback_json),
        auto_promote=args.auto_promote,
        run_mode=args.run_mode,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _handle_report(args) -> int:
    runtime = SkillRuntime.from_auto_integration(args.skill_root)
    summary = runtime.get_latest_evolution_summary()
    print(normalize_text(summary) or "No evolution report is available yet.")
    return 0


def _handle_rollback(args) -> int:
    runtime = SkillRuntime.from_auto_integration(args.skill_root)
    result = runtime.rollback(args.snapshot_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _parse_json(value: str) -> Dict[str, Any]:
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def _parse_optional_json(value: str | None):
    if value is None:
        return None
    return _parse_json(value)


def _default_manifest(skill_name: str, protocol_version: str) -> Dict[str, Any]:
    skill_id = skill_name.replace(" ", ".").replace("_", ".").lower() or "auto.initialized.skill"
    return {
        "schema_name": "SkillManifest",
        "schema_version": "1.0.0",
        "protocol_version": protocol_version,
        "skill_id": skill_id,
        "name": skill_name or "Auto Initialized Skill",
        "version": "0.1.0",
        "description": "Auto-initialized Skill-SE-Kit workspace.",
        "governance": {"mode": "standalone", "official_status": "local"},
        "capability": {"level": "native", "summary": "Auto-bootstrapped by Skill-SE-Kit."},
        "compatibility": {
            "min_protocol_version": protocol_version,
            "max_protocol_version": protocol_version,
        },
        "metadata": {"owner": "skill-se-kit", "auto_initialized": True},
    }
