from __future__ import annotations

from typing import Any, Dict, Optional

from skill_se_kit.common import dump_json, generate_id, list_json_files, load_json, normalize_text, utc_now_iso


class EvolutionReporter:
    def __init__(self, workspace):
        self.workspace = workspace
        self.workspace.ensure_layout()

    def write_report(self, cycle: Dict[str, Any]) -> Dict[str, Any]:
        report_id = generate_id("report")
        payload = self._build_payload(report_id, cycle)
        json_path = self.workspace.evolution_reports_dir / f"{report_id}.json"
        md_path = self.workspace.evolution_reports_dir / f"{report_id}.md"
        latest_md_path = self.workspace.evolution_reports_dir / "latest.md"
        latest_json_path = self.workspace.evolution_reports_dir / "latest.json"
        dump_json(json_path, payload)
        dump_json(latest_json_path, payload)
        md = self._to_markdown(payload)
        md_path.write_text(md, encoding="utf-8")
        latest_md_path.write_text(md, encoding="utf-8")
        return {
            "report_id": report_id,
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "summary": payload["summary"],
        }

    def _build_payload(self, report_id: str, cycle: Dict[str, Any]) -> Dict[str, Any]:
        decision = cycle.get("decision") or {}
        evaluation = cycle.get("evaluation") or {}
        promotion = cycle.get("promotion")
        experience = cycle.get("experience") or {}
        benchmark = evaluation.get("benchmark") or {}
        bundle = {}
        proposal = cycle.get("proposal") or {}
        for artifact in proposal.get("artifacts", []):
            if artifact.get("ref", "").endswith(".bundle.json"):
                bundle = load_json(self.workspace.root / artifact["ref"])
                break
        current_skill_bank = []
        if self.workspace.local_skill_bank_path.exists():
            current_skill_bank = load_json(self.workspace.local_skill_bank_path).get("skills", [])
        return {
            "report_id": report_id,
            "created_at": utc_now_iso(),
            "summary": {
                "action": decision.get("action"),
                "proposal_id": (cycle.get("proposal") or {}).get("proposal_id"),
                "promotion_id": promotion.get("promotion_id") if promotion else None,
                "experience_id": experience.get("experience_id"),
                "evaluation_status": evaluation.get("status"),
                "benchmark_status": benchmark.get("status"),
                "improvement": benchmark.get("improvement"),
                "feedback_confidence": experience.get("feedback_confidence"),
                "feedback_source": experience.get("feedback_source"),
            },
            "human_summary": self._human_summary(decision, evaluation, promotion, experience),
            "skill_bank": {
                "current_count": len(current_skill_bank),
                "candidate_count": len(bundle.get("skill_bank", []) or current_skill_bank),
                "latest_skill_entry_id": decision.get("skill_entry_id"),
            },
            "trend": self._recent_trend(),
            "details": cycle,
        }

    @staticmethod
    def _human_summary(
        decision: Dict[str, Any],
        evaluation: Dict[str, Any],
        promotion: Optional[Dict[str, Any]],
        experience: Dict[str, Any],
    ) -> str:
        action = decision.get("action", "unknown")
        lesson = experience.get("lesson", "")
        confidence = experience.get("feedback_confidence")
        status = evaluation.get("status", "unknown")
        if action == "skip":
            return (
                f"The kit observed a possible lesson but skipped promotion because feedback confidence "
                f"was {confidence}. Lesson candidate: {lesson}"
            )
        if promotion is not None:
            return (
                f"The kit learned a reusable rule by {action}, evaluation passed, and the new version was promoted. "
                f"Lesson: {lesson}"
            )
        return f"The kit learned a reusable rule by {action}. Evaluation status: {status}. Lesson: {lesson}"

    def _to_markdown(self, payload: Dict[str, Any]) -> str:
        summary = payload["summary"]
        details = payload.get("details") or {}
        experience = details.get("experience") or {}
        critique = experience.get("cross_rollout_critique") or []
        trend = payload.get("trend") or {}
        skill_bank = payload.get("skill_bank") or {}
        lines = [
            "# Evolution Report",
            "",
            f"- Report ID: `{payload['report_id']}`",
            f"- Created At: `{payload['created_at']}`",
            f"- Action: `{summary['action']}`",
            f"- Evaluation Status: `{summary['evaluation_status']}`",
            f"- Benchmark Status: `{summary['benchmark_status']}`",
            f"- Improvement: `{summary['improvement']}`",
            f"- Feedback Confidence: `{summary['feedback_confidence']}`",
            f"- Feedback Source: `{summary['feedback_source']}`",
            f"- Proposal ID: `{summary['proposal_id']}`",
            f"- Promotion ID: `{summary['promotion_id']}`",
            "",
            "## Human Summary",
            "",
            payload["human_summary"],
            "",
            "## Learned Lesson",
            "",
            normalize_text(experience.get("lesson")) or "No lesson recorded.",
            "",
            "## Cross-Rollout Critique",
            "",
        ]
        if critique:
            lines.extend(f"- {item}" for item in critique)
        else:
            lines.append("- No critique patterns recorded yet.")
        lines.extend(
            [
                "",
                "## Skill Bank Snapshot",
                "",
                f"- Current Skills: `{skill_bank.get('current_count')}`",
                f"- Candidate Skills: `{skill_bank.get('candidate_count')}`",
                f"- Latest Skill Entry: `{skill_bank.get('latest_skill_entry_id')}`",
                "",
                "## Recent Trend",
                "",
                f"- Recent Reports: `{trend.get('recent_reports')}`",
                f"- Promotions: `{trend.get('promotions')}`",
                f"- Passes: `{trend.get('passes')}`",
                f"- Action Mix: `{trend.get('action_mix')}`",
                "",
            ]
        )
        return "\n".join(lines)

    def _recent_trend(self) -> Dict[str, Any]:
        reports = []
        for path in list_json_files(self.workspace.evolution_reports_dir):
            if path.name == "latest.json":
                continue
            try:
                reports.append(load_json(path))
            except Exception:
                continue
        reports = reports[-5:]
        action_mix: Dict[str, int] = {}
        promotions = 0
        passes = 0
        for report in reports:
            action = normalize_text(report.get("summary", {}).get("action"))
            if action:
                action_mix[action] = action_mix.get(action, 0) + 1
            if report.get("summary", {}).get("promotion_id"):
                promotions += 1
            if report.get("summary", {}).get("evaluation_status") == "pass":
                passes += 1
        return {
            "recent_reports": len(reports),
            "promotions": promotions,
            "passes": passes,
            "action_mix": action_mix,
        }
