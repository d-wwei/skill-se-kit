# Protocol Reference

This kit is compatible with **Skill Evolution Protocol v1.0.0**.

## Protocol Repository

- Source: [skill-evolution-protocol](https://github.com/d-wwei/skill-evolution-protocol)
- Version: 1.0.0
- Status: MVP-frozen

## Schema Ownership

| Schema | Owner | Location |
|--------|-------|----------|
| SkillManifest | Protocol | `skill-evolution-protocol/schemas/skill_manifest.schema.json` |
| ExperienceRecord | Protocol | `skill-evolution-protocol/schemas/experience_record.schema.json` |
| SkillProposal | Protocol | `skill-evolution-protocol/schemas/skill_proposal.schema.json` |
| Overlay | Protocol | `skill-evolution-protocol/schemas/overlay.schema.json` |
| PromotionDecision | Protocol | `skill-evolution-protocol/schemas/promotion_decision.schema.json` |
| Feedback | **Kit** | `schemas/feedback.schema.json` |
| SkillBank | **Kit** | `schemas/skill-bank.schema.json` |
| ExperienceItem | **Kit** | `schemas/experience-item.schema.json` |
| Snapshot | **Kit** | `schemas/snapshot.schema.json` |
| AuditEntry | **Kit** | `schemas/audit-entry.schema.json` |
| SkillContract | **Kit** | `schemas/skill-contract.schema.json` |

## Relationship

Protocol schemas define the **inter-system contract** — how skills, governors, and registries communicate. Kit schemas define the **intra-workspace format** — how the agent manages its local evolution state.

The kit's `manifest.json` is a valid SkillManifest (protocol-compatible). The kit's experience items can be promoted to protocol ExperienceRecords when needed for cross-system communication. Governed mode proposals use protocol SkillProposal format.

## Governance Modes

- **Standalone**: Agent has full authority. Self-promote after learning.
- **Governed**: Agent creates proposals. Governor makes promotion decisions.

## Capability Levels

| Level | Description |
|-------|-------------|
| static | No evolution capability |
| wrapped | External evolution wrapper |
| native | Built-in evolution (this kit) |
| federated | Multi-agent evolution |
