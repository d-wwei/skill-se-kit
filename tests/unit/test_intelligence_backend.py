"""Tests for the intelligence backend abstraction and implementations."""

from __future__ import annotations

import json
import tempfile
import unittest

from skill_se_kit.intelligence.backend import (
    FeedbackResult,
    IntelligenceBackend,
    RetrievalResult,
    SynthesisResult,
    UpdateDecision,
)
from skill_se_kit.intelligence.local_backend import LocalBackend
from skill_se_kit.intelligence.llm_backend import LLMBackend, _parse_json_response


class TestRetrievalResult(unittest.TestCase):
    def test_to_dict(self):
        r = RetrievalResult(skills=[{"id": "s1"}], experiences=[{"id": "e1"}])
        d = r.to_dict()
        self.assertEqual(d["skills"], [{"id": "s1"}])
        self.assertEqual(d["experiences"], [{"id": "e1"}])


class TestFeedbackResult(unittest.TestCase):
    def test_to_dict_with_reasoning(self):
        fb = FeedbackResult(status="positive", lesson="test", source="llm", confidence=0.9, reasoning="clear directive")
        d = fb.to_dict()
        self.assertEqual(d["status"], "positive")
        self.assertEqual(d["reasoning"], "clear directive")

    def test_to_dict_without_reasoning(self):
        fb = FeedbackResult(status="negative", lesson="x", source="user_input", confidence=0.7)
        d = fb.to_dict()
        self.assertNotIn("reasoning", d)


class TestUpdateDecision(unittest.TestCase):
    def test_to_dict_merge(self):
        ud = UpdateDecision(action="merge", summary="merge it", target_skill_id="skill-abc")
        d = ud.to_dict()
        self.assertEqual(d["action"], "merge")
        self.assertEqual(d["skill_entry_id"], "skill-abc")

    def test_to_dict_add(self):
        ud = UpdateDecision(action="add", summary="new skill")
        d = ud.to_dict()
        self.assertNotIn("skill_entry_id", d)


class TestLocalBackend(unittest.TestCase):
    def setUp(self):
        self.backend = LocalBackend()

    def test_retrieve_returns_scored_results(self):
        skills = [
            {"skill_entry_id": "s1", "title": "Safety checks", "content": "Always run safety checks", "keywords": ["safety"]},
            {"skill_entry_id": "s2", "title": "Formatting", "content": "Use markdown formatting", "keywords": ["markdown"]},
        ]
        experiences = [
            {"experience_id": "e1", "lesson": "Safety is paramount", "feedback_text": "", "task_signature": "launch"},
        ]
        result = self.backend.retrieve(query_text="safety checks", skills=skills, experiences=experiences, top_k=2)
        self.assertGreater(len(result.skills), 0)
        self.assertEqual(result.skills[0]["skill_entry_id"], "s1")

    def test_retrieve_empty(self):
        result = self.backend.retrieve(query_text="xyz", skills=[], experiences=[], top_k=3)
        self.assertEqual(result.skills, [])
        self.assertEqual(result.experiences, [])

    def test_extract_feedback_preference(self):
        fb = self.backend.extract_feedback(
            user_input={"task": "you should always validate input"},
            context=None,
            result={"text": "ok"},
        )
        self.assertEqual(fb.source, "user_input")
        self.assertGreater(fb.confidence, 0.5)

    def test_extract_feedback_not_preference(self):
        fb = self.backend.extract_feedback(
            user_input={"task": "generate a report"},
            context=None,
            result={"text": "report done"},
        )
        self.assertIn(fb.source, ("execution_result", "default"))

    def test_extract_feedback_failure(self):
        fb = self.backend.extract_feedback(
            user_input={"task": "run test"},
            context=None,
            result={"error": "connection timeout"},
        )
        self.assertEqual(fb.status, "negative")
        self.assertGreaterEqual(fb.confidence, 0.7)

    def test_decide_update_add(self):
        exp = {
            "experience_id": "exp-1",
            "task_signature": "new task",
            "lesson": "This is a completely novel lesson about quantum computing",
            "cross_rollout_critique": [],
        }
        decision = self.backend.decide_update(experience=exp, skill_bank=[])
        self.assertEqual(decision.action, "add")
        self.assertTrue(decision.synthesized_content)

    def test_decide_update_merge(self):
        existing = {
            "skill_entry_id": "skill-abc",
            "title": "Safety",
            "content": "# Safety\n- Always check safety",
            "task_signature": "safety task",
            "keywords": ["safety", "check"],
        }
        exp = {
            "experience_id": "exp-2",
            "task_signature": "safety task",
            "lesson": "Always verify safety before launch",
            "cross_rollout_critique": [],
        }
        decision = self.backend.decide_update(experience=exp, skill_bank=[existing])
        self.assertEqual(decision.action, "merge")
        self.assertEqual(decision.target_skill_id, "skill-abc")

    def test_decide_update_discard(self):
        exp = {
            "experience_id": "exp-3",
            "task_signature": "temp",
            "lesson": "This is a one-off task, ignore this",
            "cross_rollout_critique": [],
        }
        decision = self.backend.decide_update(experience=exp, skill_bank=[])
        self.assertEqual(decision.action, "discard")

    def test_synthesize_skill_deduplicates(self):
        skill = {
            "skill_entry_id": "s1",
            "title": "Test",
            "content": "# Rule\n- always check\n- always check\n- verify first",
            "keywords": ["check"],
        }
        result = self.backend.synthesize_skill(skill=skill)
        self.assertEqual(result.removed_count, 1)
        self.assertNotIn("- always check\n- always check", result.content)


class TestLLMBackend(unittest.TestCase):
    def test_retrieve_with_llm(self):
        def mock_llm(prompt):
            return json.dumps({
                "skill_indices": [1, 0],
                "experience_indices": [0],
                "reasoning": "semantic match",
            })

        backend = LLMBackend(llm=mock_llm)
        skills = [
            {"skill_entry_id": "s1", "title": "A", "content": "alpha", "keywords": []},
            {"skill_entry_id": "s2", "title": "B", "content": "beta", "keywords": []},
        ]
        experiences = [{"experience_id": "e1", "lesson": "test", "feedback_text": "", "task_signature": "x"}]
        result = backend.retrieve(query_text="anything", skills=skills, experiences=experiences, top_k=2)
        self.assertEqual(result.skills[0]["skill_entry_id"], "s2")
        self.assertEqual(len(result.experiences), 1)

    def test_retrieve_falls_back_on_error(self):
        def bad_llm(prompt):
            raise RuntimeError("API down")

        backend = LLMBackend(llm=bad_llm)
        skills = [{"skill_entry_id": "s1", "title": "Safety", "content": "safety check", "keywords": ["safety"]}]
        result = backend.retrieve(query_text="safety", skills=skills, experiences=[], top_k=1)
        # Falls back to LocalBackend Jaccard
        self.assertEqual(len(result.skills), 1)

    def test_extract_feedback_with_llm(self):
        def mock_llm(prompt):
            return json.dumps({
                "status": "positive",
                "lesson": "Always validate inputs",
                "confidence": 0.95,
                "reasoning": "Clear directive from user",
            })

        backend = LLMBackend(llm=mock_llm)
        fb = backend.extract_feedback(
            user_input={"task": "validate inputs"},
            context=None,
            result={"text": "ok"},
        )
        self.assertEqual(fb.status, "positive")
        self.assertEqual(fb.confidence, 0.95)
        self.assertEqual(fb.source, "llm")

    def test_extract_feedback_rejects_non_directive(self):
        """LLM should reject non-directive speech that keyword matching would catch."""
        def mock_llm(prompt):
            return json.dumps({
                "status": "positive",
                "lesson": "",
                "confidence": 0.1,
                "reasoning": "Not a genuine directive",
            })

        backend = LLMBackend(llm=mock_llm)
        fb = backend.extract_feedback(
            user_input={"task": "I'm not sure what I should do"},
            context=None,
            result={"text": "ok"},
        )
        # LLM gives low confidence / empty lesson, vs keyword matching giving 0.8
        self.assertLess(fb.confidence, 0.5)

    def test_decide_update_merge_with_synthesis(self):
        def mock_llm(prompt):
            return json.dumps({
                "action": "merge",
                "target_skill_id": "skill-abc",
                "synthesized_content": "# Safety Protocol\n- Always validate before launch\n- Run safety checks on all inputs",
                "synthesized_title": "Safety Protocol",
                "synthesized_keywords": ["safety", "validation", "launch"],
                "reasoning": "New experience is related to existing safety skill",
                "conflicts_resolved": [],
            })

        backend = LLMBackend(llm=mock_llm)
        decision = backend.decide_update(
            experience={"experience_id": "e1", "task_signature": "safety", "lesson": "validate before launch"},
            skill_bank=[{"skill_entry_id": "skill-abc", "title": "Safety", "content": "- check safety"}],
        )
        self.assertEqual(decision.action, "merge")
        self.assertEqual(decision.target_skill_id, "skill-abc")
        self.assertIn("Safety Protocol", decision.synthesized_content)

    def test_decide_update_supersede(self):
        def mock_llm(prompt):
            return json.dumps({
                "action": "supersede",
                "target_skill_id": "skill-old",
                "synthesized_content": "# Updated Rule\n- New approach replaces old",
                "synthesized_title": "Updated Rule",
                "synthesized_keywords": ["update"],
                "reasoning": "New lesson contradicts existing",
                "conflicts_resolved": ["Old rule said X, new evidence shows Y"],
            })

        backend = LLMBackend(llm=mock_llm)
        decision = backend.decide_update(
            experience={"experience_id": "e1", "task_signature": "task", "lesson": "new approach"},
            skill_bank=[{"skill_entry_id": "skill-old", "title": "Old", "content": "old approach"}],
        )
        self.assertEqual(decision.action, "supersede")
        self.assertEqual(decision.conflicts_resolved, ["Old rule said X, new evidence shows Y"])

    def test_synthesize_skill_compresses(self):
        bullets = "\n".join(f"- lesson {i}" for i in range(20))

        def mock_llm(prompt):
            return json.dumps({
                "content": "# Compressed\n- Core principle 1\n- Core principle 2\n- Core principle 3",
                "title": "Compressed Skill",
                "keywords": ["core", "principle"],
                "removed_count": 17,
                "conflicts_resolved": ["Lesson 3 contradicted lesson 15"],
            })

        backend = LLMBackend(llm=mock_llm)
        result = backend.synthesize_skill(skill={
            "skill_entry_id": "s1",
            "title": "Big Skill",
            "content": f"# Big Skill\n{bullets}",
            "task_signature": "task",
            "keywords": [],
        })
        self.assertEqual(result.removed_count, 17)
        self.assertIn("Core principle", result.content)

    def test_synthesize_skill_small_skill_falls_back(self):
        """Skills below threshold should use LocalBackend (no LLM call)."""
        call_count = [0]

        def mock_llm(prompt):
            call_count[0] += 1
            return "{}"

        backend = LLMBackend(llm=mock_llm)
        result = backend.synthesize_skill(skill={
            "skill_entry_id": "s1",
            "title": "Small",
            "content": "# Small\n- one\n- two",
            "keywords": [],
        })
        self.assertEqual(call_count[0], 0)  # LLM should NOT be called


class TestParseJsonResponse(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(_parse_json_response('{"a": 1}'), {"a": 1})

    def test_fenced_json(self):
        self.assertEqual(_parse_json_response('```json\n{"a": 1}\n```'), {"a": 1})

    def test_embedded_json(self):
        self.assertEqual(_parse_json_response('Here is the result: {"a": 1} done'), {"a": 1})

    def test_invalid(self):
        self.assertIsNone(_parse_json_response("not json at all"))


class TestIntegrationWithRuntime(unittest.TestCase):
    """Test that the intelligence backend integrates correctly with SkillRuntime."""

    def test_register_intelligence_backend_propagates(self):
        from skill_se_kit.runtime.skill_runtime import SkillRuntime
        from tests.test_support import PROTOCOL_ROOT, load_example_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.workspace.bootstrap(load_example_manifest("standalone.manifest.json"))

            backend = LocalBackend()
            runtime.register_intelligence_backend(backend)

            self.assertIs(runtime.knowledge_store._backend, backend)
            self.assertIs(runtime.feedback_extractor._backend, backend)
            self.assertIs(runtime.autonomous_engine._backend, backend)

    def test_llm_backend_full_cycle(self):
        """Run a full autonomous cycle with a mock LLM backend."""
        from skill_se_kit.runtime.skill_runtime import SkillRuntime
        from tests.test_support import PROTOCOL_ROOT, load_example_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.workspace.bootstrap(load_example_manifest("standalone.manifest.json"))
            runtime.configure_integration(
                evaluation_cases=[
                    {"id": "test-case", "input": {"task": "plan"}, "must_contain": ["plan"]},
                ],
            )

            # Mock LLM that always returns valid JSON.
            def mock_llm(prompt):
                if "semantic retrieval" in prompt.lower():
                    return json.dumps({"skill_indices": [], "experience_indices": [], "reasoning": "no match"})
                if "feedback extraction" in prompt.lower():
                    return json.dumps({
                        "status": "positive",
                        "lesson": "Always include a plan section",
                        "confidence": 0.9,
                        "reasoning": "Clear directive",
                    })
                if "skill evolution" in prompt.lower():
                    return json.dumps({
                        "action": "add",
                        "summary": "Add new learned skill for planning",
                        "synthesized_content": "# Planning\n- Always include a plan section",
                        "synthesized_title": "Planning Best Practices",
                        "synthesized_keywords": ["plan", "section", "include"],
                        "reasoning": "New skill",
                        "target_skill_id": "",
                        "conflicts_resolved": [],
                    })
                return "{}"

            backend = LLMBackend(llm=mock_llm)
            runtime.register_intelligence_backend(backend)

            def executor(input, context):
                guidance = context.get("skill_guidance", "")
                text = f"Task: {input['task']}."
                if "plan" in guidance.lower():
                    text += " Here is a plan section."
                return {"text": text}

            runtime.register_executor(executor)

            result = runtime.run_autonomous_cycle(
                {"task": "prepare a plan"},
                feedback={"status": "positive", "lesson": "Always include a plan section."},
            )
            cycle = result["autonomous_cycle"]
            self.assertEqual(cycle["decision"]["action"], "add")
            self.assertIsNotNone(cycle["proposal"])


if __name__ == "__main__":
    unittest.main()
