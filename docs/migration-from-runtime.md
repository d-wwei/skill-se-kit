# Migration from Python Runtime

This guide helps you migrate from the Python runtime version ([skill-se-kit-python](https://github.com/d-wwei/skill-se-kit-python)) to the Agent-Native version.

## What Changes

| Aspect | Python Runtime | Agent-Native |
|--------|---------------|--------------|
| Integration | `pip install skill-se-kit` | Copy SKILL.md + schemas |
| Execution | `skill-se-kit run --input-json ...` | Agent follows SKILL.md |
| Sidecar | `skill-se-kit serve --port 9780` | Not needed |
| NPM adapter | `@skill-se-kit/adapter` | Not needed |
| Workspace dirs | 17+ directories | 5 directories |
| Intelligence | Jaccard similarity | Agent semantic understanding |
| Dependencies | Python 3.9+, jsonschema | None |

## Migration Steps

### 1. Extract Skill Bank

From the old workspace, copy the skill bank content:

```bash
# Old location
cat <old-skill-root>/local/skill_bank/skills.json

# Copy to new location
cp <old-skill-root>/local/skill_bank/skills.json <new-skill-root>/skill_bank.json
```

### 2. Extract Manifest

The manifest format is compatible. Copy and add the contract section:

```bash
cp <old-skill-root>/manifest.json <new-skill-root>/manifest.json
```

Then edit `manifest.json` to add the contract under `metadata`:

```json
{
  "metadata": {
    "contract": {
      "min_feedback_confidence": 0.35,
      "synthesis_threshold": 15,
      "auto_promote": true,
      "managed_files": [{"path": "SKILL.md", "kind": "markdown"}]
    }
  }
}
```

### 3. Migrate Experiences (Optional)

Old experience records in `local/experiences/` and `local/experience_bank/` can be copied to the new `experience/` directory. The format is slightly different:

**Old format** (protocol ExperienceRecord):
```json
{
  "schema_name": "ExperienceRecord",
  "record_id": "exp-...",
  "kind": "feedback",
  "summary": "...",
  "outcome": {"status": "positive"}
}
```

**New format** (kit ExperienceItem):
```json
{
  "experience_id": "exp-...",
  "lesson": "...",
  "feedback_status": "positive",
  "feedback_confidence": 0.7
}
```

You can convert records or start fresh — the skill bank already contains the accumulated knowledge.

### 4. Create New Workspace Structure

```bash
mkdir -p <new-skill-root>/experience
mkdir -p <new-skill-root>/audit
mkdir -p <new-skill-root>/snapshots
```

### 5. Remove Python Runtime

```bash
pip uninstall skill-se-kit
# Remove old workspace directories
rm -rf <old-skill-root>/local/
rm -rf <old-skill-root>/official/
rm -rf <old-skill-root>/governed/
rm -rf <old-skill-root>/audit/
rm -rf <old-skill-root>/provenance/
rm -rf <old-skill-root>/reports/
rm -rf <old-skill-root>/.skill_se_kit/
```

### 6. Update Agent Instructions

Replace any references to CLI commands or sidecar URLs with SKILL.md references.

**Before:**
```
Run: skill-se-kit run --input-json '...' --feedback-json '...'
```

**After:**
```
Follow the evolution protocol in SKILL.md:
1. Retrieve relevant skills from skill_bank.json
2. After execution, extract feedback and update skill bank
```

## What You Keep

- **Skill bank content** — Your accumulated knowledge transfers directly
- **Manifest** — Same protocol-compatible format
- **Experience history** — Optional, can convert or start fresh

## What You Lose

- **Deterministic execution** — The agent follows SKILL.md rules, but may occasionally deviate. Use `tools/validate.py` if strict validation is needed.
- **HTTP sidecar** — Non-agent consumers cannot access the kit. For CI/CD automation without an agent, keep the Python runtime.
- **Regression runner** — The Python runtime had built-in test case execution. In Agent-Native mode, the agent can run tests directly.
