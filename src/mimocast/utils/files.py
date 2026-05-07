"""Filesystem helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def hash_source(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    payload = data.model_dump(mode="json") if hasattr(data, "model_dump") else data
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
