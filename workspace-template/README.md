# Workspace Template

Copy this directory as the starting point for a new skill evolution workspace.

## Structure

```
<skill-root>/
  manifest.json        Identity, governance, and contract configuration
  skill_bank.json      Accumulated skill entries (the core value)
  experience/          Learning history (one JSON file per experience)
  audit/               Decision audit trail (one JSON file per event)
  snapshots/           Rollback checkpoints (one JSON file per snapshot)
```

## Setup

1. Copy `manifest.json` and `skill_bank.json` to your skill root
2. Create the three directories: `experience/`, `audit/`, `snapshots/`
3. Edit `manifest.json`: replace all `REPLACE_WITH_*` placeholders
4. Follow SKILL.md for the complete evolution lifecycle

## Files

- **manifest.json** — Protocol-compatible SkillManifest with embedded contract. Edit the `REPLACE_WITH_*` fields.
- **skill_bank.json** — Empty skill bank. Will be populated through the learning loop.
