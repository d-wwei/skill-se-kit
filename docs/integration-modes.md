# Skill-SE-Kit Integration Modes

## Why This Document Exists

Not every integration of `Skill-SE-Kit` is equivalent.

Two skills may both "use the kit", but one may only record lessons into
`SKILL.md` while the other can automatically repair Python files, rerun
evaluation, and promote working fixes.

This document defines the supported integration modes and the minimum contract
for each mode so future skills do not accidentally integrate in the wrong mode.

## The Three Modes

### 1. Learning-Only Mode

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

### 2. Native Repair Mode

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

### 3. Multi-Script Dispatcher Mode

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

## Integration Checklist

Before saying a skill is "fully integrated", confirm all of these:

- the real execution path runs through `SkillRuntime` or `skill-se-kit run`
- the executor is not only passive capture
- `managed_files` includes the real behavior files
- evaluation cases exist
- repair signals exist
- promotion depends on passing evaluation

If any of those are missing, you are not yet in native repair mode.
