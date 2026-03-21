# Skill-SE-Kit

`Skill-SE-Kit` is the standard runtime foundation for protocol-compatible,
audit-ready, self-evolving skills.
The external product and package name is `Skill-SE-Kit`, and the internal
Python module path is `skill_se_kit`.

This implementation consumes the shared protocol repository at:

- `/Users/admin/Documents/AI/skill self-evolution/skill-evolution-protocol`

It does not copy or redefine the shared schemas. All protocol validation flows read the canonical schema and example files directly from that repository through `ProtocolAdapter`.

## Supported Protocol

- declared protocol version: `1.0.0`
- schema set: `2026-03-20`
- governance modes: `standalone`, `governed`

## Core Capabilities

- experience recording
- proposal generation
- overlay application
- local evaluation
- local promotion in `standalone`
- rollback
- governor detection and protocol-version handshake in `governed`
- first-class audit artifacts
- provenance artifacts
- pluggable verification hooks with promotion gating

## Remix Integration

`Remix` is a separate product that integrates `Skill-SE-Kit` when it wants
runtime self-evolution, audit, provenance, verification, and governed handoff
capabilities for artifact remix workflows.

`Skill-SE-Kit` remains the substrate. `Remix` remains an independent system
that may target skills, protocols, modules, features, products, and compound
artifact bundles through its own target profiles.

## Project Layout

```text
skill-se-kit/
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
    contract/
    unit/
    integration/
  examples/
  docs/
```

## Running Tests

```bash
python3 -m pip install .
python3 -m unittest discover -s tests -p 'test_*.py'
```

The install step makes `skill_se_kit` importable from a clean checkout while the
test suite runs against the source tree.

## Integration

For integrating another skill on top of `Skill-SE-Kit`, start with:

- [Integration Guide](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/docs/integration-guide.md)
- [Minimal Integration Example](/Users/admin/Documents/AI/skill%20self-evolution/skill-se-kit/examples/minimal_skill_integration.py)

## Storage Layering

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
