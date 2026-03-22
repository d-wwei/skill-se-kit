from __future__ import annotations

from pathlib import Path

from skill_se_kit.common import dump_json


class SkillWorkspace:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    @property
    def official_manifest_path(self) -> Path:
        return self.root / "official" / "manifest.json"

    @property
    def local_overlays_dir(self) -> Path:
        return self.root / "local" / "overlays"

    @property
    def local_experiences_dir(self) -> Path:
        return self.root / "local" / "experiences"

    @property
    def local_proposals_dir(self) -> Path:
        return self.root / "local" / "proposals"

    @property
    def local_evaluations_dir(self) -> Path:
        return self.root / "local" / "evaluations"

    @property
    def local_rollouts_dir(self) -> Path:
        return self.root / "local" / "rollouts"

    @property
    def local_experience_bank_dir(self) -> Path:
        return self.root / "local" / "experience_bank"

    @property
    def local_skill_bank_dir(self) -> Path:
        return self.root / "local" / "skill_bank"

    @property
    def local_skill_bank_path(self) -> Path:
        return self.local_skill_bank_dir / "skills.json"

    @property
    def official_skill_bank_path(self) -> Path:
        return self.root / "official" / "skill_bank.json"

    @property
    def governed_overlays_dir(self) -> Path:
        return self.root / "governed" / "overlays"

    @property
    def governed_decisions_dir(self) -> Path:
        return self.root / "governed" / "decisions"

    @property
    def snapshots_dir(self) -> Path:
        return self._metadata_root / "snapshots"

    @property
    def local_promotions_dir(self) -> Path:
        return self._metadata_root / "local_promotions"

    @property
    def compatibility_log_path(self) -> Path:
        return self._metadata_root / "compatibility_issues.log"

    @property
    def framework_policy_dir(self) -> Path:
        return self._metadata_root / "framework_policy"

    @property
    def skill_contract_path(self) -> Path:
        return self._metadata_root / "skill_contract.json"

    @property
    def audit_summaries_dir(self) -> Path:
        return self.root / "audit" / "summaries"

    @property
    def audit_decision_logs_dir(self) -> Path:
        return self.root / "audit" / "decision_logs"

    @property
    def audit_evidence_dir(self) -> Path:
        return self.root / "audit" / "evidence"

    @property
    def provenance_sources_dir(self) -> Path:
        return self.root / "provenance" / "sources"

    @property
    def provenance_lineage_dir(self) -> Path:
        return self.root / "provenance" / "lineage"

    @property
    def _metadata_root(self) -> Path:
        current = self.root / ".skill_se_kit"
        legacy = self.root / ".skillkit"
        if current.exists() or not legacy.exists():
            return current
        return legacy

    @property
    def metadata_root(self) -> Path:
        return self._metadata_root

    def ensure_layout(self) -> None:
        required_dirs = [
            self.root / "official",
            self.root / "local" / "overlays",
            self.root / "local" / "experiences",
            self.root / "local" / "proposals",
            self.root / "local" / "evaluations",
            self.root / "local" / "rollouts",
            self.root / "local" / "experience_bank",
            self.root / "local" / "skill_bank",
            self.root / "governed" / "overlays",
            self.root / "governed" / "decisions",
            self.root / "audit" / "summaries",
            self.root / "audit" / "decision_logs",
            self.root / "audit" / "evidence",
            self.root / "provenance" / "sources",
            self.root / "provenance" / "lineage",
            self.snapshots_dir,
            self.local_promotions_dir,
            self.framework_policy_dir,
        ]
        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def bootstrap(self, manifest: dict) -> None:
        self.ensure_layout()
        if not self.manifest_path.exists():
            dump_json(self.manifest_path, manifest)
        if not self.official_manifest_path.exists():
            dump_json(self.official_manifest_path, manifest)
        if not self.local_skill_bank_path.exists():
            dump_json(self.local_skill_bank_path, {"skills": []})
        if not self.official_skill_bank_path.exists():
            dump_json(self.official_skill_bank_path, {"skills": []})
