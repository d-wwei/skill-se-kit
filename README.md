# Skill SE Kit (Agent-Native)

**Protocol-driven self-evolution for AI agent skills. Zero dependencies.**

The agent reads SKILL.md, manages JSON files, and evolves its own skill bank. No runtime, no sidecar, no package to install.

## Why Agent-Native?

Traditional skill evolution kits ship as libraries (Python, TypeScript) that agents call. This creates cross-language integration pain, deployment complexity, and inferior intelligence (Jaccard matching vs. agent semantic understanding).

The Agent-Native approach: **the agent IS the runtime.** The kit is a protocol specification + JSON schemas. The agent follows the protocol directly.

| | Library Approach | Agent-Native |
|---|---|---|
| Integration | pip install / npm install | Copy files |
| Cross-language | Sidecar + adapter needed | Works everywhere |
| Intelligence | Jaccard bag-of-words | Agent semantic understanding |
| Dependencies | Python 3.9+ / Node 18+ | None |
| Deployment | Process management | Nothing to deploy |

## Quick Start

### 1. Copy into your skill project

```
your-skill/
  SKILL.md              ← from this repo
  schemas/              ← from this repo
  manifest.json         ← from workspace-template/
  skill_bank.json       ← from workspace-template/
  experience/           ← create empty
  audit/                ← create empty
  snapshots/            ← create empty
```

### 2. Edit manifest.json

Replace `REPLACE_WITH_*` placeholders with your skill's identity.

### 3. Tell your agent to follow SKILL.md

Add to your agent's instructions:
```
Follow the skill evolution protocol in SKILL.md.
Before execution: retrieve relevant skills from skill_bank.json.
After execution: extract feedback, record experience, update skill bank.
```

### 4. Done

The agent now learns from every execution and accumulates reusable skills.

## How It Works

**Dual-loop architecture** (inspired by AutoSkill & XSKILL research):

```
Left Loop (Execution):            Right Loop (Learning):
  Read skill bank                    Extract feedback
  → Find relevant skills             → Record experience
  → Inject guidance                   → Decide: ADD / MERGE / SUPERSEDE / DISCARD
  → Execute task                      → Snapshot → Mutate skill bank → Audit
```

The agent uses its native semantic understanding for skill retrieval and feedback extraction — no Jaccard similarity, no keyword heuristics.

## Workspace Structure

```
<skill-root>/
  manifest.json        Identity + governance + contract
  skill_bank.json      Accumulated skills (the core value)
  experience/          Learning history
  audit/               Decision trail
  snapshots/           Rollback checkpoints
```

5 directories. That's it.

## Governance

- **Standalone mode**: Agent self-promotes skill changes directly.
- **Governed mode**: Agent creates proposals; an external governor approves or rejects.

Compatible with the [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol) v1.0.0.

## Documentation

- [SKILL.md](SKILL.md) — Core instruction file (English)
- [SKILL.zh-CN.md](SKILL.zh-CN.md) — Core instruction file (Chinese)
- [Integration Guide](docs/integration-guide.md) — How to integrate into any skill
- [Design Philosophy](docs/design-philosophy.md) — Why Agent-Native
- [Workspace Reference](docs/workspace-reference.md) — File format details
- [Migration Guide](docs/migration-from-runtime.md) — From the Python runtime version
- [Protocol Reference](protocol/protocol-ref.md) — Protocol compatibility

## Examples

- [Standalone Walkthrough](examples/standalone-walkthrough.md) — Complete evolution cycle
- [Governed Walkthrough](examples/governed-walkthrough.md) — Governed mode cycle
- [Example Skill Bank](examples/example-skill-bank.json) — Populated skill bank
- [Example Experience](examples/example-experience.json) — Experience record

## Research Foundations

This kit implements concepts from two 2026 research papers:

- **AutoSkill** (ECNU ICALK Lab & Shanghai AI Lab, [arXiv:2603.01145](https://arxiv.org/abs/2603.01145)) — Dual-loop architecture, add/merge/discard skill management
- **XSKILL** (HKUST, Zhejiang, HUST, [arXiv:2603.12056](https://arxiv.org/abs/2603.12056)) — Dual-stream skill library + experience bank, cross-rollout critique

The Agent-Native version extends these by replacing programmatic matching with agent semantic understanding.

## Previous Version

The Python runtime version is archived at [skill-se-kit-python](https://github.com/d-wwei/skill-se-kit-python). It provides a CLI, HTTP sidecar, and NPM adapter for scenarios requiring deterministic execution without an AI agent.

## License

MIT
