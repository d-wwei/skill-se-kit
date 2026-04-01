# Design Philosophy

## The Agent-Native Paradigm

Traditional approaches to skill evolution treat the AI agent as a **consumer** of an external runtime — the agent sends data to a Python/TypeScript library, which processes it and returns results. This creates unnecessary coupling:

- Cross-language integration pain (Python runtime in TypeScript projects)
- Deployment complexity (sidecar servers, pip/npm install)
- Inferior intelligence (Jaccard similarity vs. agent semantic understanding)

The Agent-Native paradigm inverts this: **the agent IS the runtime**. Instead of calling an external library, the agent reads a protocol specification (SKILL.md) and directly manages JSON files. The "kit" is documentation + schemas, not code.

## Why This Works

AI agents already have all the capabilities needed for skill evolution:

| Capability | External Runtime | Agent-Native |
|-----------|-----------------|--------------|
| Semantic matching | Jaccard similarity (bag-of-words) | Native semantic understanding |
| Feedback extraction | Keyword heuristics | Contextual reasoning |
| Decision making | Threshold-based rules | Judgment + rules |
| File I/O | Python file operations | Agent tool calls |
| JSON generation | Serialization libraries | Native capability |

The external runtime's core intelligence (Jaccard matching) is actually the **weakest link** — agents understand meaning, not just word overlap.

## Design Principles

### 1. Zero Dependencies
No pip install. No npm install. No binary. No sidecar. Just files that the agent reads and follows.

### 2. Protocol Over Code
Define WHAT to do (schemas, decision trees, rules), not HOW to do it (implementation code). The agent figures out the HOW.

### 3. Decision Trees Over Prose
Every branching point uses explicit IF/THEN/ELSE conditions. No ambiguous prose that different agents might interpret differently.

### 4. Explicit Constants
All thresholds, formats, and rules are stated as concrete values. No "use good judgment" — instead, "confidence < 0.35 means skip skill bank mutation."

### 5. Snapshot-Before-Mutate
Every skill bank modification is preceded by an immutable snapshot. This makes rollback trivial and audit complete.

### 6. Protocol Compatibility
All workspace artifacts conform to the Skill Evolution Protocol v1.0.0. Governed mode proposals use protocol-standard SkillProposal format.

## What We Removed (and Why)

| Removed | Why |
|---------|-----|
| Python runtime (380+ lines) | Agent handles orchestration natively |
| Jaccard similarity engine | Agent semantic understanding is superior |
| Keyword-based feedback extraction | Agent contextual reasoning is superior |
| HTTP sidecar server | No cross-process communication needed |
| NPM adapter package | No package to wrap |
| 17+ workspace directories | Simplified to 5 (manifest, skills, experience, audit, snapshots) |
| Overlay applier (JSON Pointer) | Agent edits JSON directly |
| Proposal/evaluation pipeline | Agent creates proposals directly in governed mode |

## What We Kept

| Kept | Why |
|------|-----|
| JSON Schemas | Validation and format documentation |
| Decision tree logic | Precise agent instructions |
| Confidence gating | Prevents low-quality mutations |
| Snapshot/rollback | Operational safety |
| Audit trail | Decision transparency |
| Governance modes | Enterprise-ready skill management |
| Protocol compatibility | Interoperability with governors and registries |
| Bilingual support | EN + ZH tokens and instruction files |

## Research Lineage

This kit implements concepts from two 2026 papers:

- **AutoSkill** (arXiv:2603.01145): Dual-loop architecture, add/merge/discard operations
- **XSKILL** (arXiv:2603.12056): Dual-stream skill + experience banks, cross-rollout critique

The Agent-Native version extends these by replacing programmatic matching with agent semantic understanding, achieving both simpler integration and higher quality evolution.
