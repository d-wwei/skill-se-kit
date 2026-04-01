#!/usr/bin/env python3
"""
Lightweight workspace validator for Skill SE Kit (Agent-Native).

Validates JSON files in a skill evolution workspace against their schemas.
Uses only Python stdlib — no pip dependencies required.

Usage:
    python validate.py <skill-root>
    python validate.py <skill-root> --verbose
    python validate.py <skill-root> --file manifest.json
"""

import json
import os
import re
import sys
from pathlib import Path


# ---------- Minimal JSON Schema Validator (stdlib only) ----------

def validate_required(data, required_fields, path=""):
    """Check that all required fields are present."""
    errors = []
    for field in required_fields:
        if field not in data:
            errors.append(f"{path}: missing required field '{field}'")
    return errors


def validate_type(value, expected_type, path=""):
    """Check that a value matches the expected JSON Schema type."""
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    if expected_type in type_map:
        if not isinstance(value, type_map[expected_type]):
            return [f"{path}: expected type '{expected_type}', got '{type(value).__name__}'"]
    return []


def validate_pattern(value, pattern, path=""):
    """Check that a string matches a regex pattern."""
    if isinstance(value, str) and not re.match(pattern, value):
        return [f"{path}: value '{value}' does not match pattern '{pattern}'"]
    return []


def validate_enum(value, allowed, path=""):
    """Check that a value is one of the allowed values."""
    if value not in allowed:
        return [f"{path}: value '{value}' not in allowed values {allowed}"]
    return []


# ---------- Schema Definitions ----------

SCHEMAS = {
    "manifest": {
        "required": ["schema_name", "schema_version", "protocol_version",
                      "skill_id", "name", "version", "governance",
                      "capability", "compatibility"],
        "checks": {
            "schema_name": {"const": "SkillManifest"},
            "schema_version": {"const": "1.0.0"},
            "skill_id": {"pattern": r"^[a-z0-9][a-z0-9._-]*$"},
            "version": {"pattern": r"^\d+\.\d+\.\d+$"},
        }
    },
    "skill_bank": {
        "required": ["skills"],
        "checks": {}
    },
    "experience": {
        "required": ["experience_id", "skill_id", "recorded_at", "lesson",
                      "feedback_status", "feedback_source", "feedback_confidence"],
        "checks": {
            "experience_id": {"pattern": r"^exp-[a-f0-9]{12}$"},
            "skill_id": {"pattern": r"^[a-z0-9][a-z0-9._-]*$"},
            "feedback_status": {"enum": ["positive", "negative"]},
            "feedback_source": {"enum": ["explicit", "user_input", "execution_result", "default"]},
        }
    },
    "audit": {
        "required": ["audit_id", "created_at", "event_type", "skill_id", "details"],
        "checks": {
            "audit_id": {"pattern": r"^aud-[a-f0-9]{12}$"},
            "skill_id": {"pattern": r"^[a-z0-9][a-z0-9._-]*$"},
            "event_type": {"enum": [
                "skill_added", "skill_merged", "skill_superseded",
                "skill_discarded", "skill_synthesized", "experience_recorded",
                "snapshot_created", "rollback_executed",
                "proposal_created", "proposal_submitted",
                "proposal_accepted", "proposal_rejected",
                "governance_decision", "provenance_source", "provenance_lineage"
            ]},
        }
    },
    "snapshot": {
        "required": ["snapshot_id", "created_at", "reason", "manifest", "skill_bank"],
        "checks": {
            "snapshot_id": {"pattern": r"^snap-[a-f0-9]{12}$"},
        }
    },
}


def detect_schema(filepath, data):
    """Detect which schema a file should validate against."""
    name = os.path.basename(filepath)

    if name == "manifest.json":
        return "manifest"
    if name == "skill_bank.json":
        return "skill_bank"
    if name.startswith("exp-"):
        return "experience"
    if name.startswith("aud-"):
        return "audit"
    if name.startswith("snap-"):
        return "snapshot"

    # Fallback: check schema_name field
    if isinstance(data, dict):
        sn = data.get("schema_name", "")
        if sn == "SkillManifest":
            return "manifest"

    return None


def validate_file(filepath, data, schema_name, verbose=False):
    """Validate a single JSON file against its schema."""
    schema = SCHEMAS.get(schema_name)
    if not schema:
        return [f"Unknown schema: {schema_name}"]

    errors = []

    # Check required fields
    errors.extend(validate_required(data, schema["required"], filepath))

    # Check field-level constraints
    for field, checks in schema["checks"].items():
        if field not in data:
            continue
        value = data[field]
        path = f"{filepath}.{field}"

        if "const" in checks:
            if value != checks["const"]:
                errors.append(f"{path}: expected '{checks['const']}', got '{value}'")
        if "pattern" in checks:
            errors.extend(validate_pattern(value, checks["pattern"], path))
        if "enum" in checks:
            errors.extend(validate_enum(value, checks["enum"], path))

    # Skill bank: validate individual skill entries
    if schema_name == "skill_bank" and "skills" in data:
        for i, skill in enumerate(data["skills"]):
            epath = f"{filepath}.skills[{i}]"
            for req in ["skill_entry_id", "title", "content", "version", "updated_at"]:
                if req not in skill:
                    errors.append(f"{epath}: missing required field '{req}'")
            if "skill_entry_id" in skill:
                errors.extend(validate_pattern(
                    skill["skill_entry_id"], r"^skl-[a-f0-9]{12}$",
                    f"{epath}.skill_entry_id"))
            if "version" in skill:
                errors.extend(validate_pattern(
                    skill["version"], r"^\d+\.\d+\.\d+$",
                    f"{epath}.version"))

    if verbose and not errors:
        print(f"  OK: {filepath} ({schema_name})")

    return errors


def validate_workspace(skill_root, verbose=False, target_file=None):
    """Validate all JSON files in a workspace."""
    root = Path(skill_root)
    all_errors = []
    file_count = 0

    if not root.exists():
        print(f"Error: workspace not found: {skill_root}")
        return 1

    # Collect files to validate
    files_to_check = []

    if target_file:
        fp = root / target_file
        if fp.exists():
            files_to_check.append(fp)
        else:
            print(f"Error: file not found: {fp}")
            return 1
    else:
        # Root-level files
        for name in ["manifest.json", "skill_bank.json"]:
            fp = root / name
            if fp.exists():
                files_to_check.append(fp)

        # Directory files
        for dirname in ["experience", "audit", "snapshots"]:
            dirpath = root / dirname
            if dirpath.is_dir():
                for fp in sorted(dirpath.glob("*.json")):
                    files_to_check.append(fp)

    for fp in files_to_check:
        try:
            with open(fp) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            all_errors.append(f"{fp}: invalid JSON: {e}")
            continue

        schema_name = detect_schema(str(fp), data)
        if schema_name is None:
            if verbose:
                print(f"  SKIP: {fp} (unknown schema)")
            continue

        file_count += 1
        errors = validate_file(str(fp), data, schema_name, verbose)
        all_errors.extend(errors)

    # Summary
    print(f"\nValidated {file_count} files in {skill_root}")
    if all_errors:
        print(f"Found {len(all_errors)} error(s):\n")
        for e in all_errors:
            print(f"  ERROR: {e}")
        return 1
    else:
        print("All files valid.")
        return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate.py <skill-root> [--verbose] [--file <filename>]")
        print("\nValidates JSON files in a skill evolution workspace.")
        sys.exit(1)

    skill_root = sys.argv[1]
    verbose = "--verbose" in sys.argv
    target_file = None

    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 < len(sys.argv):
            target_file = sys.argv[idx + 1]

    exit_code = validate_workspace(skill_root, verbose, target_file)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
