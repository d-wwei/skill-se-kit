# Skill-SE-Kit Integration Guide

## Goal

This guide shows how another skill should integrate `Skill-SE-Kit` as its
runtime substrate without copying framework internals or drifting from the
shared protocol.

The intended result is:

- the integrated skill keeps its own domain logic
- `Skill-SE-Kit` owns evolution, governance, audit, provenance, and rollback plumbing
- protocol compatibility remains centralized and testable

## What To Integrate

An integrating skill should depend on `skill-se-kit` as a library and use
`skill_se_kit.SkillRuntime` as its main entrypoint.

Do not:

- copy `Skill-SE-Kit` source files into the skill
- fork or rename protocol schemas
- write directly into `official/` in governed mode
- bypass `SkillRuntime` to reimplement promotion or handshake flows

## Responsibility Split

### The Integrated Skill Owns

- domain logic
- domain-specific prompt or execution behavior
- domain-specific evaluation rules
- optional verification hooks
- skill-specific metadata and examples

### Skill-SE-Kit Owns

- protocol validation
- experience recording
- proposal generation
- overlay application
- local evaluation receipts
- standalone promotion flow
- governed handshake and submission
- rollback snapshots
- audit artifacts
- provenance artifacts

## Required Inputs

Every integrated skill needs:

1. a protocol-compatible `manifest.json`
2. a protocol-compatible `official/manifest.json`
3. a skill workspace root
4. access to the shared `skill-evolution-protocol` repository

## Workspace Layout

The integrated skill workspace should look like this:

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

Protocol-required directories keep their protocol meaning.
`Skill-SE-Kit` adds audit, provenance, evaluations, and internal metadata areas
without redefining protocol semantics.

Legacy `.skillkit/` is still readable for compatibility, but new integrations
should use `.skill_se_kit/`.

## Minimal Integration Flow

### 1. Install

```bash
python3 -m pip install skill-se-kit
```

### 2. Create A Manifest

Start from:

- [standalone.manifest.json](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/examples/standalone.manifest.json)
- [governed.manifest.json](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/examples/governed.manifest.json)

Then replace:

- `skill_id`
- `name`
- `description`
- `capability`
- `metadata`

### 3. Bootstrap The Workspace

Use `SkillRuntime.workspace.bootstrap(manifest)` once to create the expected
workspace layout and write initial manifests.

### 4. Register Domain Verification

If the skill has domain-specific regression checks, register them through
`runtime.register_verification_hook(name, hook)`.

Hooks should return either:

- `True` / `False`
- or a dict with `status` and `details`

### 5. Use Runtime APIs

Use the runtime facade for all evolution actions:

- `record_experience(...)`
- `generate_proposal(...)`
- `apply_overlay(...)`
- `evaluate_proposal(...)`
- `promote_candidate(...)`
- `rollback(...)`

## Minimal Example

See:

- [minimal_skill_integration.py](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/examples/minimal_skill_integration.py)

This example shows a small native skill wrapper that:

- boots a standalone skill workspace
- registers a domain verification hook
- records an experience
- creates a candidate proposal
- evaluates the proposal
- promotes it locally

## Standalone Integration

Use `standalone` when the skill runs independently and may self-promote locally.

Rules:

- local experiences, overlays, proposals, and evaluation receipts are allowed
- local promotion is allowed only after a passing evaluation
- `official` in this mode is local-only, not governor-authoritative

Recommended pattern:

1. record observations
2. generate candidate proposal
3. run evaluation and verification hooks
4. self-promote locally if checks pass
5. rollback if needed

## Governed Integration

Use `governed` when a governor controls official promotion.

Rules:

- the skill may still learn, evaluate, and propose locally
- the skill must not write `official/manifest.json` locally
- proposal submission requires governor handshake compatibility
- governor decisions and governed overlays are ingested into `governed/`

Recommended pattern:

1. record local evidence
2. generate candidate proposal
3. run local evaluation and verification hooks
4. call governor handshake
5. submit candidate proposal
6. wait for governor decision

## Verification Hook Contract

Hooks receive:

- `proposal_document`
- `context`

Example:

```python
def regression_hook(proposal_document, context):
    if proposal_document["proposal_type"] == "metadata_change":
        return {"status": "pass", "details": "metadata-only change"}
    return {"status": "pass", "details": "domain regression suite passed"}
```

If any registered hook fails, promotion gating will block local promotion.

## Audit And Provenance Outputs

Integrated skills get these outputs automatically:

- `audit/decision_logs/*.json`
- `audit/summaries/*.json`
- `audit/evidence/*.json`
- `provenance/sources/*.json`
- `provenance/lineage/*.json`

Use these outputs for:

- local review
- debugging evolution history
- packaging evidence for governor review
- downstream provenance-sensitive skills

## Integration Checklist

- install `skill-se-kit` instead of copying framework internals
- keep protocol artifacts schema-valid through `SkillRuntime`
- keep domain logic outside framework internals
- register domain verification hooks if the skill has extra quality gates
- use `standalone` or `governed` mode explicitly in the manifest
- never write governed official state locally
- keep contract tests against the shared protocol repository

## Recommended Tests For Integrating Skills

- manifest validates against the protocol
- workspace bootstrap creates the expected layout
- domain verification hooks pass and fail as expected
- standalone local promotion succeeds only after evaluation
- governed mode rejects local official writes
- generated audit and provenance artifacts exist after evaluation/promotion

## Extension Boundary

External systems such as `Remix` should integrate `Skill-SE-Kit`
through:

- `SkillRuntime`
- verification hooks
- domain orchestration wrappers

They should not directly couple themselves to low-level storage internals unless
they are extending the framework itself.
