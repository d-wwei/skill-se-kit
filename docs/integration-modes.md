# Skill-SE-Kit Integration Modes

## Why This Document Exists

Not every integration of `Skill-SE-Kit` is equivalent.

Two skills may both "use the kit", but one may only record lessons into
`SKILL.md` while the other can automatically repair Python files, rerun
evaluation, and promote working fixes.

This document defines the supported integration modes and the minimum contract
for each mode so future skills do not accidentally integrate in the wrong mode.

## The Four Modes

### 1. Agent-Driven Mode

Use this mode when the host system is an LLM agent (Claude, GPT, or any
agentic framework) and the goal is zero-code integration with maximum
semantic quality.

Core idea: the agent itself is the intelligence layer. It has full
execution context, can reason about outcomes, and can construct
high-quality structured feedback. Skill-SE-Kit handles structured storage,
protocol compliance, versioning, and promotion gating.

This is the recommended mode for LLM agent hosts.

Typical setup:

- agent calls `skill-se-kit init` once to bootstrap the workspace
- after each task execution, agent constructs a feedback JSON from its own
  reasoning (not from the SDK's built-in extractor)
- agent calls `skill-se-kit run --input-json '...' --feedback-json '...'`
  with the structured feedback
- before the next task, agent reads `local/skill_bank/skills.json` and
  injects relevant skills into its own system prompt or context
- agent uses `skill-se-kit report` to review evolution history
- agent uses `skill-se-kit rollback` if a promoted skill degrades performance

Why this works better than registering an LLM backend:

- the agent has complete execution context (conversation history, tool
  outputs, page state, user intent) that an SDK-internal LLM call cannot
  access
- feedback quality is higher because the agent reasons with full context
  instead of a fixed extraction prompt
- no extra LLM API calls beyond what the agent already makes
- zero Python code needed on the host side

Minimum contract:

- `skill-se-kit` installed and accessible as a CLI command
- agent constructs feedback in the expected JSON format (see
  [Feedback JSON Reference](#feedback-json-reference) below)
- `managed_files` set appropriately for the desired learning or repair scope
- agent reads `local/skill_bank/skills.json` to close the learning loop

Result:

- the kit stores structured experiences and skills
- the kit evaluates and promotes based on its protocol
- the agent provides all semantic intelligence
- upgrade path: `pip install --upgrade skill-se-kit`, zero code changes

Agent integration pattern:

```text
Agent (LLM)
  │
  ├─ Execute task (browse, code, search, etc.)
  │
  ├─ Reflect on outcome → construct feedback JSON
  │     {
  │       "status": "positive" or "negative",
  │       "lesson": "Reusable insight from this execution",
  │       "source": "explicit",
  │       "confidence": 0.85
  │     }
  │
  ├─ skill-se-kit run --input-json '...' --feedback-json '...'
  │     → SDK stores experience, evaluates, promotes if passing
  │
  └─ Next task: read local/skill_bank/skills.json
        → inject relevant skills into agent context
```

### 2. Learning-Only Mode

Use this mode when the goal is to:

- record experience
- extract lessons
- grow the skill bank
- append guidance to markdown or text assets

This mode is acceptable for:

- low-risk prompt tuning
- documentation refinement
- early observation-only rollout
- passive onboarding of an existing skill

Typical setup:

- `managed_files` contains only `SKILL.md`, `README.md`, or other docs
- no `repair_actions`
- no `repair_actions_on_fail`
- no code files in the write scope

Result:

- the kit learns
- the kit may promote new lessons
- the kit does not fix product code

### 3. Native Repair Mode

Use this mode when the goal is to automatically land real fixes or
optimizations into code.

This is the correct mode when you expect the kit to:

- repair broken argument parsing
- update alias or constant mappings
- append missing guards or validation
- optimize managed code paths

Minimum contract:

- the real execution path goes through `SkillRuntime`
- `managed_files` includes the actual code files that may be modified
- the executor returns structured failure evidence and, when possible,
  `repair_actions` or `optimization_actions`
- `evaluation_cases` are configured
- failing cases may include `repair_actions_on_fail`
- promotion is gated by passing evaluation

Result:

- the kit learns
- the kit produces `file_patches`
- the kit reruns evaluation after repair
- the kit may promote only after a repair passes

### 4. Multi-Script Dispatcher Mode

Use this mode for skills whose real behavior lives across multiple scripts,
tools, or entrypoints.

This is the correct pattern for skills like:

- script libraries under `scripts/`
- tool collections with separate command files
- wrapper skills that route to many subcommands

Minimum contract:

- a dispatcher-style executor maps tasks to the correct script or tool
- the dispatcher returns structured execution results
- `managed_files` includes the dispatcher and any repairable target scripts
- evaluation cases are tied to the same routed tasks
- repair actions target concrete script files, not only the dispatcher

Result:

- the kit evolves the real behavior layer
- code repair is not trapped at `SKILL.md`
- failures can be mapped to script-specific fixes

## CLI Capability Boundary

The CLI (`skill-se-kit init/run/report/rollback`) uses the local Jaccard-
similarity backend for retrieval and feedback extraction. This is a zero-
dependency keyword-matching engine that works without any LLM API calls.

What the CLI can do:

- bootstrap workspaces
- run the full autonomous cycle (execute, learn, evaluate, promote)
- keyword-level skill retrieval and feedback extraction
- generate human-readable reports
- rollback to snapshots

What the CLI cannot do:

- register a custom `IntelligenceBackend` (including `LLMBackend`)
- register custom verification hooks
- register custom repair adapters

For semantic-level intelligence, you have two options:

1. **Agent-Driven mode** (recommended for LLM agent hosts): the agent
   constructs high-quality feedback itself and passes it via
   `--feedback-json`. The CLI handles storage and protocol. No Python
   code needed.

2. **Python API**: call `runtime.register_intelligence_backend(LLMBackend(llm=...))`
   for SDK-internal LLM-powered retrieval, extraction, and synthesis.
   Requires Python integration code.

## Anti-Pattern: External Test Harness Plus CLI Logger

This is the integration mistake that caused the moomoo-style mismatch.

Pattern:

1. an external harness runs the real scripts directly
2. after the test finishes, it separately calls `skill-se-kit run`
3. the kit receives only a summarized `task` and `user_input`

Why this is wrong:

- the kit does not own the real execution
- the kit sees a lesson, not the full repair context
- repair actions are usually missing
- evaluation cases are often missing
- `managed_files` tends to default to `SKILL.md`

Observed outcome:

- the skill bank grows
- `SKILL.md` gains learned rules
- real defect files remain unchanged

If your integration looks like this, you are in learning-only mode even if you
expected repair mode.

## Correct Contract By Capability

### If You Want Only Learning

Required:

- runtime facade or CLI invocation
- low-risk managed files such as markdown

Optional:

- evaluation cases
- repair adapters

### If You Want Automatic Repair

Required:

- native runtime ownership of execution
- code files in `managed_files`
- structured repair evidence
- evaluation cases
- promotion gate

Recommended:

- `max_repair_rounds >= 1`
- `repair_actions_on_fail` on high-value regression cases
- custom rewriter or repair adapters for recurring defect classes

### If You Want Repair In A Multi-Script Skill

Required:

- dispatcher executor
- script inventory mapped to explicit routes
- script files in `managed_files`
- failure-to-file mapping

Recommended:

- per-script evaluation cases
- repair actions that target concrete script paths
- route-aware logging in executor results

## What To Put In `managed_files`

### Good Examples

- `scripts/trade/modify_order.py`
- `scripts/quote/get_plate_stock.py`
- `executor.py`
- `SKILL.md`

### Bad Example For Repair Expectations

- only `SKILL.md`
- only `README.md`
- only wrapper files while all real logic lives elsewhere

If the defective file is not in `managed_files`, the kit cannot be expected to
repair it.

## What To Put In Evaluation Cases

Evaluation cases should describe the exact behaviors you want guarded.

Good repair-oriented cases usually include:

- a representative input
- `must_contain` or `must_not_contain`
- optionally `repair_actions_on_fail`

Example shape:

```json
{
  "id": "modify-order-arg-fix",
  "input": {"task": "modify order", "script": "trade/modify_order.py"},
  "must_contain": ["--price"],
  "repair_actions_on_fail": [
    {
      "adapter": "replace_text",
      "path": "scripts/trade/modify_order.py",
      "old": "parser.add_argument('--qty'",
      "new": "parser.add_argument('--price'"
    }
  ]
}
```

## What Executors Must Return In Repair Mode

Executors should return structured data whenever possible.

Recommended fields:

- `status`
- `exit_code`
- `text`
- `error`
- `script`
- `repair_actions`
- `optimization_actions`

The more precisely failures are mapped to files and actions, the more likely the
kit can land working repairs instead of only storing lessons.

## Feedback JSON Reference

When providing explicit feedback via `--feedback-json`, use this structure:

```json
{
  "status": "positive or negative (required)",
  "lesson": "A reusable insight from this execution (required)",
  "source": "explicit (required for agent-constructed feedback)",
  "confidence": 0.85,
  "reasoning": "Optional: why this lesson matters"
}
```

Field definitions:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | yes | `"positive"` or `"negative"` |
| `lesson` | string | yes | The reusable guidance extracted from this execution |
| `source` | string | yes | `"explicit"` for agent-constructed feedback, `"user_input"` for user-originated, `"execution_result"` for auto-extracted |
| `confidence` | float | no | 0.0 to 1.0. Default: 1.0 for explicit feedback. Below `min_feedback_confidence` (default 0.35), the experience is stored but skipped for skill-bank mutation |
| `reasoning` | string | no | Detailed reasoning behind the lesson |

Common mistakes:

- Using `sentiment` instead of `status` — the SDK expects `status`
- Using `detail` instead of `lesson` — the SDK expects `lesson`
- Omitting `source` — without `"explicit"`, the SDK may re-extract feedback
  from the execution result, potentially overriding your higher-quality input

## If You Want Agent-Driven Integration

Required:

- `skill-se-kit` CLI accessible to the agent host
- agent constructs feedback in the format above
- agent reads `local/skill_bank/skills.json` for skill injection

Recommended:

- set `run_mode` to `auto` for full autonomous cycle
- provide `confidence` values to let the SDK gate low-quality signals
- read `reports/evolution/latest.json` for structured evolution data
- use `skill-se-kit rollback` when a promoted skill causes regressions

Not required:

- Python bridge or wrapper script
- `register_intelligence_backend()` call
- any Python code on the host side

## Integration Checklist

Before saying a skill is "fully integrated", confirm all of these:

- the real execution path runs through `SkillRuntime` or `skill-se-kit run`
- the executor is not only passive capture
- `managed_files` includes the real behavior files
- evaluation cases exist
- repair signals exist
- promotion depends on passing evaluation

If any of those are missing, you are not yet in native repair mode.
