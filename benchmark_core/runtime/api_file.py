from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


def load_api_file(path: str | None) -> dict[str, Any]:
    if not path or not Path(path).exists():
        return {}
    src = Path(path)
    if src.suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML API config")
        data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    else:
        data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("API config must be an object")
    return data
