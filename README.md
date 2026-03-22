# Skill-SE-Kit

[中文说明](README.zh-CN.md)

`Skill-SE-Kit` is a protocol-compatible runtime substrate for self-evolving, audit-ready, governable skills.
It provides the shared runtime primitives needed for standalone skill evolution and governed promotion workflows.

The public product and package name is `Skill-SE-Kit`.
The internal Python module path is `skill_se_kit`.

## Core Capabilities

- one-click easy integration for agents and skills
- `skill-se-kit init` auto-bootstrap for near zero-touch onboarding
- configurable run modes: `off`, `manual`, `auto`
- automatic feedback extraction from user input and execution results
- confidence-aware learning that skips weak signals by default
- English and Chinese preference detection
- multilingual retrieval tokens for English and Chinese knowledge reuse
- human-readable evolution reports
- autonomous dual-loop evolution for integrated skills
- automatic file patch generation, code repair, and code optimization for managed files
- execution-time retrieval from skill bank and experience bank
- interaction-to-experience extraction
- add/merge/discard skill management
- candidate rewrite bundles with regression-gated promotion
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

Bootstrap an existing skill workspace:

```bash
skill-se-kit init --skill-root /path/to/skill --protocol-root /path/to/skill-evolution-protocol
skill-se-kit run --skill-root /path/to/skill --input-json '{"task":"draft memo","user_input":"Always include a summary."}'
skill-se-kit report --skill-root /path/to/skill
skill-se-kit rollback --skill-root /path/to/skill --snapshot-id snapshot-xxxx
```

## Foolproof Usage

Use `EasyIntegrator.one_click(...)` or `SkillRuntime.enable_easy_integration(...)`
to bootstrap a skill workspace, register the executor, set the run mode, and
enable auto-feedback plus human reports in one step.

For existing skills that want an install-and-go path, use `skill-se-kit init`.
It will:

- discover the protocol repository
- bootstrap manifests and workspace layout if missing
- auto-detect a conventional executor when possible
- surface script inventory hints when a dispatcher is still needed
- create `.skill_se_kit/auto_integration.json`
- patch `SKILL.md` with a wrapper hint when `SKILL.md` exists
- enable `run` and `report` CLI entrypoints for agents and humans
- expose a CLI rollback path for operational recovery

Run modes:

- `off`: bypass the kit and call the executor directly
- `manual`: run the kit but do not auto-learn
- `auto`: run the kit and auto-trigger evolution

Auto-feedback defaults:

- explicit user preferences like `always`, `never`, `must`, `每次都`, `必须`, `不要`
- execution failures inferred from result status, stderr, or exit code
- low-confidence generic signals are stored as experience but skipped for skill-bank mutation

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
    rollouts/
    experience_bank/
    skill_bank/
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
    skill_contract.json
    auto_integration.json
  reports/
    evolution/
```

## Integration

Start with:

- [Integration Guide](docs/integration-guide.md)
- [Autonomous Evolution Guide](docs/autonomous-evolution.md)
- [Architecture](docs/architecture.md)
- [MVP Plan](docs/mvp-plan.md)
- [Minimal Integration Example](examples/minimal_skill_integration.py)
- [Easy Mode Example](examples/easy_mode_skill.py)
- [Autonomous Native Skill Example](examples/autonomous_native_skill.py)
- [Autonomous Code Repair Example](examples/autonomous_code_repair.py)
- `skill-se-kit init`, `skill-se-kit run`, `skill-se-kit report`

## Relationship To Other Repositories

- [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol): canonical contract and schemas
- [Agent Skill Governor](https://github.com/d-wwei/agent-skill-governor): external authority for governed official promotion
- [Remix](https://github.com/d-wwei/remix): independent reconstruction system that integrates `Skill-SE-Kit` when it needs self-evolution and governed handoff
