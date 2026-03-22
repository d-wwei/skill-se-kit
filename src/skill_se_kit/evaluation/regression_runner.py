from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from skill_se_kit.common import ensure_list


class RegressionRunner:
    def __init__(self, workspace, contract_store, knowledge_store, executor_provider: Callable[[], Any]):
        self.workspace = workspace
        self.contract_store = contract_store
        self.knowledge_store = knowledge_store
        self.executor_provider = executor_provider

    def evaluate_candidate(self, proposal_document: Dict[str, Any], bundle: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        contract = self.contract_store.load_contract()
        cases = list(contract.get("evaluation_cases") or [])
        executor = self.executor_provider()
        if executor is None or not cases:
            return {
                "status": "not_run",
                "baseline_pass_rate": 0.0,
                "candidate_pass_rate": 0.0,
                "improvement": 0.0,
                "cases": [],
            }

        candidate_skill_bank = None
        candidate_file_patches = {}
        if bundle:
            candidate_skill_bank = list(bundle.get("skill_bank") or [])
            candidate_file_patches = dict(bundle.get("file_patches") or {})

        case_results: List[Dict[str, Any]] = []
        baseline_passes = 0
        candidate_passes = 0
        repairable_failures = 0
        strict_failures = 0
        for case in cases:
            case_context = dict(case.get("context") or {})
            query_text = str(case.get("input") or "")

            baseline_knowledge = self.knowledge_store.retrieve_knowledge(query_text=query_text)
            candidate_knowledge = self.knowledge_store.retrieve_knowledge(
                query_text=query_text,
                skill_bank=candidate_skill_bank,
            )

            baseline_output = executor(
                case.get("input"),
                {
                    **case_context,
                    "retrieved_skills": baseline_knowledge["skills"],
                    "retrieved_experiences": baseline_knowledge["experiences"],
                    "skill_guidance": "\n".join(skill["content"] for skill in baseline_knowledge["skills"]),
                },
            )
            candidate_output = executor(
                case.get("input"),
                {
                    **case_context,
                    "candidate_mode": True,
                    "candidate_file_patches": candidate_file_patches,
                    "retrieved_skills": candidate_knowledge["skills"],
                    "retrieved_experiences": candidate_knowledge["experiences"],
                    "skill_guidance": "\n".join(skill["content"] for skill in candidate_knowledge["skills"]),
                },
            )

            baseline_pass = self._case_passed(baseline_output, case)
            candidate_pass = self._case_passed(candidate_output, case)
            baseline_passes += 1 if baseline_pass else 0
            candidate_passes += 1 if candidate_pass else 0
            if not candidate_pass and case.get("repair_actions_on_fail"):
                repairable_failures += 1
            if not candidate_pass and case.get("require_candidate_pass"):
                strict_failures += 1
            case_results.append(
                {
                    "case_id": case["id"],
                    "baseline_pass": baseline_pass,
                    "candidate_pass": candidate_pass,
                    "baseline_output": baseline_output,
                    "candidate_output": candidate_output,
                    "repair_actions_on_fail": list(case.get("repair_actions_on_fail") or []),
                }
            )

        baseline_rate = baseline_passes / len(cases)
        candidate_rate = candidate_passes / len(cases)
        improvement = candidate_rate - baseline_rate
        status = "pass" if candidate_rate >= baseline_rate else "fail"
        if repairable_failures or strict_failures:
            status = "fail"
        return {
            "status": status,
            "baseline_pass_rate": baseline_rate,
            "candidate_pass_rate": candidate_rate,
            "improvement": improvement,
            "repairable_failures": repairable_failures,
            "strict_failures": strict_failures,
            "cases": case_results,
        }

    @staticmethod
    def _case_passed(output: Any, case: Dict[str, Any]) -> bool:
        text = str(output.get("text") if isinstance(output, dict) else output or "")
        must_contain = [item.lower() for item in ensure_list(case.get("must_contain"))]
        must_not_contain = [item.lower() for item in ensure_list(case.get("must_not_contain"))]
        lowered = text.lower()
        return all(item in lowered for item in must_contain) and all(item not in lowered for item in must_not_contain)
