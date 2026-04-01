# Workspace Reference

## Directory Structure

```
<skill-root>/
├── manifest.json          Identity, governance, and contract configuration
├── skill_bank.json        Accumulated skill entries (the core value)
├── experience/            Learning history
│   └── exp-{id}.json      One file per experience record
├── audit/                 Decision audit trail
│   └── aud-{id}.json      One file per audit event
└── snapshots/             Rollback checkpoints
    └── snap-{id}.json     One file per snapshot
```

## File Descriptions

### manifest.json

The skill's identity document. Protocol-compatible SkillManifest with an embedded contract under `metadata.contract`.

- **Read** at workspace initialization and governance checks
- **Write** on version bumps and governance state changes
- **Schema**: skill-evolution-protocol `skill_manifest.schema.json` + kit `skill-contract.schema.json` (embedded)

### skill_bank.json

The accumulated knowledge base. Each skill entry is a versioned, reusable guideline.

- **Read** at the start of every execution (skill retrieval)
- **Write** after learning loop decisions (ADD, MERGE, SUPERSEDE, SYNTHESIZE)
- **NEVER write without creating a snapshot first**
- **Schema**: `schemas/skill-bank.schema.json`

### experience/

One JSON file per recorded experience. Append-only — experiences are never modified after creation.

- **Write** during learning loop (Section 5.3 of SKILL.md)
- **Read** for audit, governor evidence, cross-rollout critique
- **Schema**: `schemas/experience-item.schema.json`
- **Naming**: `exp-{12 hex chars}.json`

### audit/

One JSON file per decision event. Append-only — audit entries are never modified.

- **Write** after every decision in the evolution lifecycle
- **Read** for audit review, governance compliance, debugging
- **Schema**: `schemas/audit-entry.schema.json`
- **Naming**: `aud-{12 hex chars}.json`
- In governed mode, proposals are also written here: `prop-{12 hex chars}.json`

### snapshots/

Immutable checkpoints of workspace state. Each snapshot contains full copies of manifest.json and skill_bank.json.

- **Write** before every skill bank mutation (MANDATORY)
- **Read** during rollback operations
- **Schema**: `schemas/snapshot.schema.json`
- **Naming**: `snap-{12 hex chars}.json`

## ID Conventions

| Prefix | Entity | Example |
|--------|--------|---------|
| `skl-` | Skill entry | `skl-a1b2c3d4e5f6` |
| `exp-` | Experience record | `exp-f1e2d3c4b5a6` |
| `aud-` | Audit entry | `aud-d4e5f6a7b8c9` |
| `snap-` | Snapshot | `snap-b2c3d4e5f6a7` |
| `prop-` | Proposal (governed) | `prop-aabbccddeeff` |

All IDs are generated as `{prefix}-{uuid4().hex[:12]}` — 12 lowercase hexadecimal characters from a UUID4.

## Timestamp Format

All timestamps use ISO 8601 UTC with Z suffix:
```
2026-03-31T14:30:00Z
```

No timezone offsets. No microseconds. Always UTC.

## Version Format

Semantic versioning: `MAJOR.MINOR.PATCH`

- **Patch bump** (x.y.z → x.y.z+1): MERGE, SYNTHESIZE
- **Minor bump** (x.y.z → x.y+1.0): SUPERSEDE
- **Major bump**: Reserved for breaking changes (manual only)
