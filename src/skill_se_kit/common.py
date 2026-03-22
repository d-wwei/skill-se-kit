from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4


SUPPORTED_PROTOCOL_VERSION = "1.0.0"


class SkillSEKitError(Exception):
    """Base error for Skill-SE-Kit."""


class GovernanceError(SkillSEKitError):
    """Raised when governance rules forbid an operation."""


class ProtocolValidationError(SkillSEKitError):
    """Raised when a document fails protocol validation."""


# Backward-compatible alias for older integrations that may still import it.
SkillKitError = SkillSEKitError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def parse_semver(version: str) -> Tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def bump_patch_version(version: str) -> str:
    major, minor, patch = parse_semver(version)
    return f"{major}.{minor}.{patch + 1}"


def same_major(left: str, right: str) -> bool:
    return parse_semver(left)[0] == parse_semver(right)[0]


def version_in_range(version: str, min_version: str, max_version: str) -> bool:
    current = parse_semver(version)
    return parse_semver(min_version) <= current <= parse_semver(max_version)


def deep_copy_json(value: Any) -> Any:
    return copy.deepcopy(value)


def _decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def json_pointer_tokens(pointer: str) -> List[str]:
    if not pointer:
        return []
    if pointer == "/":
        return []
    if not pointer.startswith("/"):
        raise ValueError(f"Unsupported JSON pointer: {pointer}")
    return [_decode_pointer_token(token) for token in pointer.lstrip("/").split("/")]


def get_pointer_value(document: Dict[str, Any], pointer: str) -> Any:
    current: Any = document
    for token in json_pointer_tokens(pointer):
        if isinstance(current, list):
            current = current[int(token)]
        else:
            current = current[token]
    return current


def set_pointer_value(document: Dict[str, Any], pointer: str, value: Any, append: bool = False) -> None:
    tokens = json_pointer_tokens(pointer)
    if not tokens:
        raise ValueError("Root document replacement is not supported")
    current: Any = document
    for token in tokens[:-1]:
        if isinstance(current, list):
            current = current[int(token)]
        else:
            if token not in current or not isinstance(current[token], (dict, list)):
                current[token] = {}
            current = current[token]
    leaf = tokens[-1]
    if isinstance(current, list):
        index = int(leaf)
        if append and index == len(current):
            current.append(value)
        else:
            current[index] = value
        return
    if append:
        bucket = current.setdefault(leaf, [])
        if not isinstance(bucket, list):
            raise ValueError(f"Cannot append to non-list pointer: {pointer}")
        bucket.append(value)
        return
    current[leaf] = value


def remove_pointer_value(document: Dict[str, Any], pointer: str) -> None:
    tokens = json_pointer_tokens(pointer)
    if not tokens:
        raise ValueError("Removing the root document is not supported")
    current: Any = document
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]
    leaf = tokens[-1]
    if isinstance(current, list):
        del current[int(leaf)]
    else:
        current.pop(leaf, None)


def list_json_files(directory: Path) -> Iterable[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix == ".json")


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).strip()


def tokenize_text(value: Any) -> List[str]:
    text = normalize_text(value)
    if not text:
        return []
    lowered = text.lower()
    tokens = [token for token in re.findall(r"[A-Za-z0-9_]+", lowered) if token]
    han_chars = re.findall(r"[\u4e00-\u9fff]", text)
    if han_chars:
        tokens.extend(han_chars)
        if len(han_chars) >= 2:
            tokens.extend("".join(han_chars[index : index + 2]) for index in range(len(han_chars) - 1))
    return tokens


def jaccard_similarity(left: Any, right: Any) -> float:
    left_tokens = set(tokenize_text(left))
    right_tokens = set(tokenize_text(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
