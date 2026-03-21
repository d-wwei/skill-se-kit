# Skill-SE-Kit MVP Architecture

## Modules

- `SkillRuntime`: orchestration facade exposing the required public API.
- `ExperienceStore`: validates and persists `ExperienceRecord` objects.
- `ProposalGenerator`: builds protocol-compatible `SkillProposal` documents and candidate manifests.
- `OverlayApplier`: validates and applies protocol `Overlay` payload operations to the active manifest.
- `LocalEvaluator`: performs local-only evaluation and records evaluation evidence.
- `LocalPromoter`: performs local promotion in `standalone` mode without minting a protocol `PromotionDecision`.
- `VersionStore`: owns the active manifest, official baseline, snapshots, and rollback.
- `GovernorClient`: handles governor detection, handshake semantics, and governed submission state changes.
- `ProtocolAdapter`: reads canonical schemas, examples, and version metadata from the protocol repository.
- `AuditLogger`: emits first-class audit logs, summaries, and evidence receipts.
- `ProvenanceStore`: tracks source attribution and artifact lineage for local and governed flows.
- `VerificationHookRegistry`: provides pluggable verification hooks and persisted verification receipts.

## Core Interfaces

The runtime facade provides:

- `execute(input, context)`
- `record_experience(...)`
- `generate_proposal(...)`
- `apply_overlay(...)`
- `evaluate_proposal(...)`
- `promote_candidate(...)`
- `rollback(...)`
- `detect_governor(...)`
- `get_supported_protocol_version(...)`

## Protocol Integration

### Schema Loading

`ProtocolAdapter` reads:

- `README.md`
- `schemas/*.json`
- `examples/*.json`
- `docs/capability-levels.md`
- `docs/governance-modes.md`
- `docs/state-transitions.md`
- `docs/versioning-policy.md`
- `versions/current.json`

directly from the frozen protocol repository. This library never stores duplicate schema copies in its own tree.

### Validation

`ProtocolAdapter` validates:

- `SkillManifest`
- `ExperienceRecord`
- `SkillProposal`
- `Overlay`
- `PromotionDecision`

through the canonical JSON Schemas.

### Governed Official Write Guard

`VersionStore.write_official_manifest()` refuses writes when the active governance mode is `governed`.

`LocalPromoter.promote_candidate()` also refuses to promote when `can_self_promote` is false.
It now also requires a passing local evaluation receipt before standalone promotion.

### Protocol Examples As Fixtures

Contract tests iterate over the protocol repository's `examples/` directory and validate every fixture against its matching schema. This proves compatibility without re-encoding fixtures locally.

## Execution Sequences

### Standalone

1. Load `manifest.json` and `official/manifest.json`.
2. Record experiences into `local/experiences/`.
3. Generate candidate proposals into `local/proposals/`.
4. Apply local overlays from `local/overlays/` to the active manifest.
5. Run verification hooks and persist receipts into `local/evaluations/`.
6. Evaluate locally, emit evaluation experiences, and write audit/provenance artifacts.
7. Promote locally only after a passing evaluation, then update `manifest.json` and `official/manifest.json`.
8. Roll back via `VersionStore` snapshots when needed.

### Governed

1. Load `manifest.json` and detect `governance.mode=governed`.
2. Record local experiences and candidate proposals locally.
3. Perform handshake compatibility checks through `GovernorClient`.
4. Submit proposals by moving shared artifact state from `candidate` to `submitted`.
5. Accept governor overlays and decisions into `governed/`.
6. Emit governed audit/provenance artifacts for submissions and decisions.
7. Refuse any unauthorized write to `official/manifest.json`.
8. Allow rollback of local active state, but do not rewrite governed official state locally.
