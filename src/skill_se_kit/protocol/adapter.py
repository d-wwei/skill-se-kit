from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from jsonschema import Draft202012Validator

from skill_se_kit.common import (
    ProtocolValidationError,
    SUPPORTED_PROTOCOL_VERSION,
    load_json,
    same_major,
    version_in_range,
)


class ProtocolAdapter:
    """Read-only adapter over the shared protocol repository."""

    SCHEMA_FILES = {
        "SkillManifest": "skill_manifest.schema.json",
        "ExperienceRecord": "experience_record.schema.json",
        "SkillProposal": "skill_proposal.schema.json",
        "Overlay": "overlay.schema.json",
        "PromotionDecision": "promotion_decision.schema.json",
    }

    EXAMPLE_FILES = {
        "SkillManifest": "skill_manifest.example.json",
        "ExperienceRecord": "experience_record.example.json",
        "SkillProposal": "skill_proposal.example.json",
        "Overlay": "overlay.example.json",
        "PromotionDecision": "promotion_decision.example.json",
    }

    def __init__(self, protocol_root: str | Path):
        self.protocol_root = Path(protocol_root).expanduser().resolve()
        self._current = load_json(self.protocol_root / "versions" / "current.json")
        self._validators = {
            name: Draft202012Validator(load_json(self.protocol_root / "schemas" / filename))
            for name, filename in self.SCHEMA_FILES.items()
        }

    def get_supported_protocol_version(self) -> str:
        return SUPPORTED_PROTOCOL_VERSION

    def get_schema_set(self) -> str:
        return self._current["schema_set"]

    def get_current_protocol_metadata(self) -> Dict[str, Any]:
        return dict(self._current)

    def get_schema_path(self, schema_name: str) -> Path:
        return self.protocol_root / "schemas" / self.SCHEMA_FILES[schema_name]

    def get_example_path(self, schema_name: str) -> Path:
        return self.protocol_root / "examples" / self.EXAMPLE_FILES[schema_name]

    def load_example(self, schema_name: str) -> Dict[str, Any]:
        return load_json(self.get_example_path(schema_name))

    def iter_examples(self) -> Iterable[Tuple[str, Dict[str, Any]]]:
        for schema_name in self.EXAMPLE_FILES:
            yield schema_name, self.load_example(schema_name)

    def validate_document(self, schema_name: str, document: Dict[str, Any]) -> None:
        protocol_version = document.get("protocol_version")
        if protocol_version is None:
            raise ProtocolValidationError("Document is missing protocol_version")
        if not same_major(protocol_version, self.get_supported_protocol_version()):
            raise ProtocolValidationError(
                f"Unsupported protocol major version: {protocol_version}"
            )
        errors = sorted(self._validators[schema_name].iter_errors(document), key=lambda error: error.path)
        if errors:
            details = "; ".join(error.message for error in errors)
            raise ProtocolValidationError(f"{schema_name} validation failed: {details}")

    def validate_manifest(self, manifest: Dict[str, Any]) -> None:
        self.validate_document("SkillManifest", manifest)
        compatibility = manifest["compatibility"]
        if not version_in_range(
            self.get_supported_protocol_version(),
            compatibility["min_protocol_version"],
            compatibility["max_protocol_version"],
        ):
            raise ProtocolValidationError(
                "Active protocol version is outside the manifest compatibility range"
            )

    def validate_experience(self, document: Dict[str, Any]) -> None:
        self.validate_document("ExperienceRecord", document)

    def validate_proposal(self, document: Dict[str, Any]) -> None:
        self.validate_document("SkillProposal", document)

    def validate_overlay(self, document: Dict[str, Any]) -> None:
        self.validate_document("Overlay", document)

    def validate_decision(self, document: Dict[str, Any]) -> None:
        self.validate_document("PromotionDecision", document)

    def is_version_compatible(self, peer_min_version: str, peer_max_version: str) -> bool:
        return version_in_range(
            self.get_supported_protocol_version(),
            peer_min_version,
            peer_max_version,
        )
