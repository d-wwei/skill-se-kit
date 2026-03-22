from __future__ import annotations

import ast
import json
from typing import Any, Dict


def replace_text(content: str, action: Dict[str, Any]) -> str:
    old = str(action.get("old", ""))
    new = str(action.get("new", ""))
    count = action.get("count")
    if not old:
        return content
    return content.replace(old, new, int(count)) if count is not None else content.replace(old, new)


def insert_after(content: str, action: Dict[str, Any]) -> str:
    marker = str(action.get("marker", ""))
    snippet = str(action.get("content", ""))
    if not marker or not snippet or snippet in content:
        return content
    index = content.find(marker)
    if index < 0:
        return content
    insert_at = index + len(marker)
    return f"{content[:insert_at]}\n{snippet}\n{content[insert_at:]}"


def append_text(content: str, action: Dict[str, Any]) -> str:
    snippet = str(action.get("content", ""))
    if not snippet or snippet in content:
        return content
    suffix = "" if content.endswith("\n") or not content else "\n"
    return f"{content}{suffix}{snippet}\n"


def python_dict_set(content: str, action: Dict[str, Any]) -> str:
    target = str(action.get("target", ""))
    key = action.get("key")
    value = action.get("value")
    if not target or key is None:
        return content
    tree = ast.parse(content)
    updated = False
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != target or not isinstance(node.value, ast.Dict):
            continue
        for index, existing_key in enumerate(node.value.keys):
            if isinstance(existing_key, ast.Constant) and existing_key.value == key:
                node.value.values[index] = _literal_to_ast(value)
                updated = True
                break
        if not updated:
            node.value.keys.append(ast.Constant(value=key))
            node.value.values.append(_literal_to_ast(value))
            updated = True
        break
    if not updated:
        return content
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def python_list_add(content: str, action: Dict[str, Any]) -> str:
    target = str(action.get("target", ""))
    value = action.get("value")
    if not target:
        return content
    tree = ast.parse(content)
    updated = False
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != target or not isinstance(node.value, ast.List):
            continue
        for item in node.value.elts:
            if isinstance(item, ast.Constant) and item.value == value:
                return content
        node.value.elts.append(_literal_to_ast(value))
        updated = True
        break
    if not updated:
        return content
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _literal_to_ast(value: Any) -> ast.AST:
    return ast.parse(json.dumps(value, ensure_ascii=False)).body[0].value
