from __future__ import annotations

import unittest

from tests.test_support import PROTOCOL_ROOT
from skill_se_kit.protocol.adapter import ProtocolAdapter


class ProtocolContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = ProtocolAdapter(PROTOCOL_ROOT)

    def test_supported_protocol_version_is_explicit(self) -> None:
        self.assertEqual(self.adapter.get_supported_protocol_version(), "1.0.0")

    def test_all_protocol_examples_validate(self) -> None:
        validators = {
            "SkillManifest": self.adapter.validate_manifest,
            "ExperienceRecord": self.adapter.validate_experience,
            "SkillProposal": self.adapter.validate_proposal,
            "Overlay": self.adapter.validate_overlay,
            "PromotionDecision": self.adapter.validate_decision,
        }
        for schema_name, document in self.adapter.iter_examples():
            with self.subTest(schema_name=schema_name):
                validators[schema_name](document)


if __name__ == "__main__":
    unittest.main()
