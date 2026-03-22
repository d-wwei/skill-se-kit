from __future__ import annotations

import tempfile
import unittest

from skill_se_kit.common import jaccard_similarity, tokenize_text
from skill_se_kit.runtime.skill_runtime import SkillRuntime
from tests.test_support import PROTOCOL_ROOT, load_example_manifest


class MultilingualRetrievalTests(unittest.TestCase):
    def test_tokenize_text_includes_chinese_tokens(self) -> None:
        tokens = tokenize_text("每次都要先做安全检查")
        self.assertIn("每", tokens)
        self.assertIn("安全", tokens)

    def test_jaccard_similarity_supports_chinese_overlap(self) -> None:
        score = jaccard_similarity("每次都要先做安全检查", "安全检查步骤")
        self.assertGreater(score, 0.0)

    def test_knowledge_retrieval_finds_chinese_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = SkillRuntime(skill_root=tmpdir, protocol_root=PROTOCOL_ROOT)
            runtime.workspace.bootstrap(load_example_manifest("standalone.manifest.json"))
            runtime.knowledge_store.append_experience_item(
                {
                    "experience_id": "bank-exp-cn",
                    "recorded_at": "2026-03-22T00:00:00Z",
                    "task_signature": "检查流程",
                    "feedback_status": "positive",
                    "feedback_source": "user_input",
                    "feedback_confidence": 0.9,
                    "feedback_text": "每次都要先做安全检查",
                    "lesson": "每次都要先做安全检查",
                    "cross_rollout_critique": [],
                    "execution_id": "execution-cn",
                }
            )
            retrieved = runtime.knowledge_store.retrieve_knowledge(query_text="请做安全检查")
            self.assertEqual(len(retrieved["experiences"]), 1)
            self.assertIn("安全检查", retrieved["experiences"][0]["lesson"])


if __name__ == "__main__":
    unittest.main()
