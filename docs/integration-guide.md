# Integration Guide

How to add self-evolution capability to any AI agent skill.

## Prerequisites

- A skill with a defined task scope
- An AI agent that can read files and write JSON
- That's it. No runtime, no dependencies.

## Integration Steps

### 1. Copy Files

Copy into your skill project:

```
your-skill/
  SKILL.md              ← Copy from skill-se-kit/SKILL.md (or SKILL.zh-CN.md)
  schemas/              ← Copy from skill-se-kit/schemas/
  manifest.json         ← Copy from skill-se-kit/workspace-template/manifest.json
  skill_bank.json       ← Copy from skill-se-kit/workspace-template/skill_bank.json
  experience/           ← Create empty directory
  audit/                ← Create empty directory
  snapshots/            ← Create empty directory
```

### 2. Configure manifest.json

Edit the `REPLACE_WITH_*` placeholders:

```json
{
  "skill_id": "your-skill-id",
  "name": "Your Skill Name",
  "description": "What your skill does",
  "metadata": {
    "owner": "your-team",
    "contract": {
      "min_feedback_confidence": 0.35,
      "synthesis_threshold": 15,
      "auto_promote": true,
      "managed_files": [
        {"path": "SKILL.md", "kind": "markdown"}
      ]
    }
  }
}
```

### 3. Instruct Your Agent

Add to your agent's instructions (system prompt, CLAUDE.md, or equivalent):

```
When executing tasks for this skill, follow the evolution protocol in SKILL.md:
1. Before execution: retrieve relevant skills from skill_bank.json
2. After execution: extract feedback, record experience, update skill bank
3. Always create a snapshot before modifying skill_bank.json
```

### 4. Done

The agent now self-evolves. Each execution potentially adds, merges, or refines skills.

## Integration Patterns

### Superpowers / Claude Code Skills (.md files)

For skills that are primarily markdown instruction files:

1. Add a reference to SKILL.md in your skill's main instruction file
2. Include the `schemas/` directory
3. The agent reads SKILL.md as part of its skill loading process

### Standalone Agent Skills

For agent skills with their own executor:

1. Copy the full workspace template
2. Configure manifest.json with your skill metadata
3. The agent follows SKILL.md during execution

### Governed Skills

For skills under governance control:

1. Set `governance.mode` to `"governed"` in manifest.json
2. Set `governance.governor_id` to your governor's ID
3. Set `governance.handshake_required` to `true`
4. The agent creates proposals instead of directly mutating the skill bank

## What NOT to Do

- Do NOT install any package. There is nothing to install.
- Do NOT run a sidecar server. There is no server.
- Do NOT add Python or Node.js dependencies. The agent IS the runtime.
- Do NOT duplicate the protocol schemas. Reference them from the protocol repo.

## FAQ

**Q: Does the skill bank grow forever?**
A: No. The SYNTHESIZE action compresses skills when they exceed the synthesis threshold (default: 15 bullets). The agent can also SUPERSEDE outdated skills and DISCARD one-off lessons.

**Q: What if the agent writes invalid JSON?**
A: Use the optional `tools/validate.py` script to check workspace files. Or rely on your agent's ability to self-correct — most modern agents write valid JSON consistently.

**Q: Can I use this with non-AI automation?**
A: The kit is designed for AI agents. For pure automation without an agent, consider the [Python runtime version](https://github.com/d-wwei/skill-se-kit-python).

**Q: How do I migrate from the Python runtime?**
A: See `docs/migration-from-runtime.md`.
