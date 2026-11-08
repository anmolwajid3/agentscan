"""Load the He et al. migration rules. The file is not rewritten."""

from __future__ import annotations

import csv
from pathlib import Path


def load_rules(path: Path) -> dict[tuple[str, str], dict]:
    rules: dict[tuple[str, str], dict] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            source = (row.get("fromLib") or "").strip()
            target = (row.get("toLib") or "").strip()
            if not source or not target:
                continue
            rules[(source, target)] = {
                "rule_id": str(index),
                "rule_type": (row.get("type") or "").strip(),
            }
    return rules
