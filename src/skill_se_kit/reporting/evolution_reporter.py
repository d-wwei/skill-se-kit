from __future__ import annotations

from typing import Any, Dict, Optional

from skill_se_kit.common import dump_json, generate_id, utc_now_iso


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
            },
            "human_summary": self._human_summary(decision, evaluation, promotion, experience),
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
        status = evaluation.get("status", "unknown")
        if promotion is not None:
            return f"The kit learned a reusable rule by {action}, evaluation passed, and the new version was promoted. Lesson: {lesson}"
        return f"The kit learned a reusable rule by {action}. Evaluation status: {status}. Lesson: {lesson}"

    @staticmethod
    def _to_markdown(payload: Dict[str, Any]) -> str:
        summary = payload["summary"]
        return "\n".join(
            [
                "# Evolution Report",
                "",
                f"- Report ID: `{payload['report_id']}`",
                f"- Created At: `{payload['created_at']}`",
                f"- Action: `{summary['action']}`",
                f"- Evaluation Status: `{summary['evaluation_status']}`",
                f"- Benchmark Status: `{summary['benchmark_status']}`",
                f"- Improvement: `{summary['improvement']}`",
                f"- Proposal ID: `{summary['proposal_id']}`",
                f"- Promotion ID: `{summary['promotion_id']}`",
                "",
                "## Human Summary",
                "",
                payload["human_summary"],
                "",
            ]
        )

