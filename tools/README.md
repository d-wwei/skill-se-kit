# Validation Tools

Optional utilities for validating workspace files. **Not required for normal operation** — the agent manages files directly via SKILL.md.

## validate.py

Lightweight JSON validator using only Python stdlib (no pip dependencies).

### Usage

```bash
# Validate entire workspace
python tools/validate.py /path/to/skill-root

# Verbose output (show OK files too)
python tools/validate.py /path/to/skill-root --verbose

# Validate a single file
python tools/validate.py /path/to/skill-root --file manifest.json
```

### What It Checks

- Required fields present
- Field types correct
- ID patterns match (skl-, exp-, aud-, snap-)
- Enum values valid
- Version format (semver)
- Skill bank entry structure

### Requirements

- Python 3.6+ (stdlib only, no pip install needed)
