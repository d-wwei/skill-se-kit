from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PROTOCOL_ROOT = ROOT.parent / "skill-evolution-protocol"


def load_example_manifest(name: str = "standalone.manifest.json"):
    with (ROOT / "examples" / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)

