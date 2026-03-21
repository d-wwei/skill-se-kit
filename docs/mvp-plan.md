# Skill-SE-Kit MVP Development Plan

## Phase 1: Protocol Integration + Storage

- implement `ProtocolAdapter`
- declare supported protocol version explicitly
- implement filesystem workspace and manifest stores
- add contract tests against protocol schemas and examples

## Phase 2: Runtime + Experience

- implement `SkillRuntime`
- implement `ExperienceStore`
- support append-only experience recording under protocol validation

## Phase 3: Proposal + Overlay

- implement `ProposalGenerator`
- implement `OverlayApplier`
- persist candidate artifacts in protocol-compatible local directories

## Phase 4: Evaluator + Promoter

- implement `LocalEvaluator`
- implement `LocalPromoter`
- add snapshot-backed rollback
- keep standalone promotion local-only and protocol-safe
- require passing evaluation receipts before local promotion

## Phase 5: Governor Handshake

- implement `GovernorClient.detect_governor()`
- implement protocol version compatibility handshake
- support governed submission while forbidding official writes

## Phase 6: Audit + Provenance + Verification

- add first-class audit logs, summaries, and evidence
- add provenance source and lineage artifacts
- add pluggable verification hooks and promotion gating
