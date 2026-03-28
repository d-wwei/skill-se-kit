# Skill-SE-Kit

[中文说明](README.zh-CN.md)

`Skill-SE-Kit` is a protocol-compatible runtime substrate for self-evolving, audit-ready, governable skills.
It provides the shared runtime primitives needed for standalone skill evolution and governed promotion workflows.

The public product and package name is `Skill-SE-Kit`.
The internal Python module path is `skill_se_kit`.

## Core Capabilities

- one-click easy integration for agents and skills
- **agent-driven integration mode**: LLM agents use the CLI for structured storage while providing their own intelligence — zero Python code required on the host side
- pluggable intelligence backends: built-in local Jaccard engine or bring-your-own LLM via `LLMBackend`
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
- SDK version compatibility check on workspace load

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
    feedback/
    governance/
    intelligence/
    integration/
    provenance/
    protocol/
    repair/
    reporting/
    verification/
  schemas/             # JSON Schemas for feedback input and run result output
  tests/
  examples/
  docs/
```

## Integration Decision Tree

```text
What is your host system?
├─ LLM Agent (Claude, GPT, agentic framework)
│   ├─ Zero-code integration? → Agent-Driven Mode (recommended)
│   │     CLI for storage + agent provides all intelligence
│   └─ Deep SDK customization? → Python API + register_intelligence_backend()
├─ Automated pipeline (CI/CD, scripts, non-agent code)
│   ├─ Only record lessons? → Learning-Only Mode
│   ├─ Automatic code repair? → Native Repair Mode
│   └─ Multiple scripts/tools? → Multi-Script Dispatcher Mode
└─ CLI manual mode → for human oversight, debugging, auditing
```

See [Integration Modes](docs/integration-modes.md) for details on each mode.

## Quick Start

```bash
python3 -m pip install .
python3 -m pytest tests/
```

Bootstrap an existing skill workspace:

```bash
skill-se-kit init --skill-root /path/to/skill --protocol-root /path/to/skill-evolution-protocol
skill-se-kit run --skill-root /path/to/skill --input-json '{"task":"draft memo","user_input":"Always include a summary."}'
skill-se-kit report --skill-root /path/to/skill
skill-se-kit rollback --skill-root /path/to/skill --snapshot-id snapshot-xxxx
```

For agent-driven integration, pass structured feedback directly:

```bash
skill-se-kit run --skill-root /path/to/skill \
  --input-json '{"task":"browse","url":"https://example.com"}' \
  --feedback-json '{"status":"positive","lesson":"Use page.evaluate() to pierce shadow DOM","source":"explicit","confidence":0.9}'
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

- [Integration Guide](docs/integration-guide.md) — decision tree, responsibility split, checklist
- [Integration Modes](docs/integration-modes.md) — agent-driven, learning-only, native repair, multi-script dispatcher
- [Autonomous Evolution Guide](docs/autonomous-evolution.md)
- [Architecture](docs/architecture.md)

Contract schemas:

- [Feedback JSON Schema](schemas/feedback.schema.json) — input format for `--feedback-json`
- [Run Result JSON Schema](schemas/run-result.schema.json) — output format of `skill-se-kit run`

Examples:

- [Minimal Integration](examples/minimal_skill_integration.py)
- [Easy Mode](examples/easy_mode_skill.py)
- [Autonomous Native Skill](examples/autonomous_native_skill.py)
- [Autonomous Code Repair](examples/autonomous_code_repair.py)

If you want the kit to repair code, not just learn rules, read
[Integration Modes](docs/integration-modes.md) first and make sure you are
using native repair mode instead of a post-execution logging setup.

## Relationship To Other Repositories

- [Skill Evolution Protocol](https://github.com/d-wwei/skill-evolution-protocol): canonical contract and schemas
- [Agent Skill Governor](https://github.com/d-wwei/agent-skill-governor): external authority for governed official promotion
- [Remix](https://github.com/d-wwei/remix): independent reconstruction system that integrates `Skill-SE-Kit` when it needs self-evolution and governed handoff
