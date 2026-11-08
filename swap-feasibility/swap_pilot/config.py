"""Read config.yaml without a third-party YAML library."""

from __future__ import annotations

from pathlib import Path


def load_config(path: Path) -> dict:
    data: dict = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current:
            data.setdefault(current, []).append(line.split("-", 1)[1].strip())
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip("\"'")
        if value == "":
            current = key
            data[key] = []
        else:
            current = None
            data[key] = _coerce(value)
    return data


def _coerce(value: str):
    if value.isdigit():
        return int(value)
    try:
        if "." in value:
            return float(value)
    except ValueError:
        return value
    return value
