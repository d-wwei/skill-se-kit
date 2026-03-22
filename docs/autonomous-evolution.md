# Autonomous Evolution Engine

`Skill-SE-Kit` now includes a full autonomous evolution loop inspired by
AutoSkill and XSkill.

The implementation adds four missing capabilities on top of the earlier
governance runtime:

- execution-time retrieval of learned skills and experiences
- interaction-to-experience extraction
- experience-to-skill add/merge/discard management
- regression-gated candidate promotion with rollback

## Loop Structure

### Left Loop: Response Generation

At execution time, the runtime:

1. builds a task signature
2. retrieves relevant skill entries from the local skill bank
3. retrieves relevant experience items from the experience bank
4. injects both into execution context as `skill_guidance`,
   `retrieved_skills`, and `retrieved_experiences`
5. calls the integrated skill executor

### Right Loop: Skill Evolution

After execution feedback is available, the runtime:

1. stores the rollout
2. extracts a reusable experience item
3. performs lightweight cross-rollout critique from recent similar rollouts
4. decides `add`, `merge`, or `discard`
5. builds a candidate bundle with updated skill bank and optional file patches
6. creates a protocol-compatible proposal
7. evaluates the candidate against verification hooks and regression cases
8. promotes locally only if the candidate is non-regressive and policy allows it

## Core Components

- [autonomous_engine.py](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/src/skill_se_kit/evolution/autonomous_engine.py)
- [knowledge_store.py](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/src/skill_se_kit/storage/knowledge_store.py)
- [skill_contract_store.py](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/src/skill_se_kit/storage/skill_contract_store.py)
- [regression_runner.py](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/src/skill_se_kit/evaluation/regression_runner.py)

## New Runtime Integration Points

Integrated skills should now register:

- an executor via `register_executor(...)`
- optional managed files and evaluation cases via `configure_integration(...)`
- optional file rewriter via `register_rewriter(...)`
- optional verification hooks via `register_verification_hook(...)`

The runtime then supports:

- `execute(...)`
- `autonomous_improve(...)`
- `run_autonomous_cycle(...)`

## Storage Additions

The autonomous engine expands storage with:

```text
<skill-root>/
  local/
    rollouts/
    experience_bank/
    skill_bank/
  official/
    skill_bank.json
  .skill_se_kit/
    skill_contract.json
```

## Promotion Policy

Autonomous local promotion requires:

- protocol-valid proposal artifacts
- passing verification hooks
- non-regressive benchmark result, when evaluation cases are configured
- improvement meeting `auto_promote_min_improvement`
- standalone governance mode

In governed mode, the engine still learns locally, but promotion remains external.

