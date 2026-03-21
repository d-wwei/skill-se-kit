# Skill-SE-Kit

[中文说明](README.zh-CN.md)

`Skill-SE-Kit` is a protocol-compatible runtime substrate for self-evolving, audit-ready, governable skills.
It provides the shared runtime primitives needed for standalone skill evolution and governed promotion workflows.

The public product and package name is `Skill-SE-Kit`.
The internal Python module path is `skill_se_kit`.

## Core Capabilities

- experience recording
- proposal generation
- overlay application
- local evaluation
- local promotion in `standalone`
- governor handshake and governed-mode enforcement
- audit artifact generation
- provenance recording
- verification hooks and promotion gating

## Supported Protocol

- protocol version: `1.0.0`
- governance modes: `standalone`, `governed`

`Skill-SE-Kit` consumes the canonical schemas and examples from [skill-evolution-protocol](https://github.com/d-wwei/skill-evolution-protocol).

## Repository Layout

```text
skill-se-kit/
  README.md
  README.zh-CN.md
  src/skill_se_kit/
    audit/
    runtime/
    storage/
    evolution/
    evaluation/
    governance/
    provenance/
    protocol/
    verification/
  tests/
  examples/
  docs/
```

## Quick Start

```bash
python3 -m pip install .
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Skill Storage Layering

```text
<skill-root>/
  manifest.json
  official/
    manifest.json
  local/
    experiences/
    proposals/
    overlays/
    evaluations/
  governed/
    decisions/
    overlays/
  audit/
    summaries/
    decision_logs/
    evidence/
  provenance/
    sources/
    lineage/
  .skill_se_kit/
    snapshots/
    framework_policy/
```

## Integration

Start with:

- [Integration Guide](docs/integration-guide.md)
- [Architecture](docs/architecture.md)
- [MVP Plan](docs/mvp-plan.md)
- [Minimal Integration Example](examples/minimal_skill_integration.py)

## Relationship To Other Repositories

- [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol): canonical contract and schemas
- [Agent Skill Governor](https://github.com/d-wwei/agent-skill-governor): external authority for governed official promotion
- [Remix](https://github.com/d-wwei/remix): independent reconstruction system that integrates `Skill-SE-Kit` when it needs self-evolution and governed handoff

