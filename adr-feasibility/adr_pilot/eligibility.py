"""Check 1 eligibility.

A project is eligible from its history before AI adoption. Activity after
2026 is not required, so a project that went quiet still counts. ADRs written
after the AI signal do not count toward the "at least 5" bar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

PASS_AI_PROJECTS = 50
PASS_NON_AI_PROJECTS = 50
PASS_SUPERSEDED = 100


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class Eligibility:
    group: str
    adr_count: int
    adr_count_before_signal: int
    superseded: int
    counts_toward_ai: bool
    counts_toward_non_ai: bool
    reason: str


def classify_project(
    *,
    adr_dates: list[str | None],
    superseded_flags: list[bool],
    signal_date: str | None,
    likely_template: bool,
    clone_ok: bool,
) -> Eligibility:
    if not clone_ok:
        return Eligibility("unavailable", 0, 0, 0, False, False, "clone-failed")
    if likely_template:
        return Eligibility("template", len(adr_dates), 0, 0, False, False, "template-or-catalog")

    signal = parse_dt(signal_date)
    before = 0
    superseded_before = 0
    superseded_all = 0
    for date, superseded in zip(adr_dates, superseded_flags):
        if superseded:
            superseded_all += 1
        written = parse_dt(date)
        if signal is None or (written is not None and written < signal):
            before += 1
            if superseded:
                superseded_before += 1
        elif written is None and signal is None:
            before += 1

    total = len(adr_dates)
    # Superseded decisions that belong to the eligible window.
    superseded = superseded_before if signal is not None else superseded_all

    if signal is not None and before >= 5:
        return Eligibility(
            "ai-eligible",
            total,
            before,
            superseded,
            True,
            False,
            "at-least-5-adrs-before-signal",
        )
    if signal is not None and before < 5:
        group = "ai-native" if before == 0 else "ai-too-few-before"
        return Eligibility(group, total, before, superseded_all, False, False, group)
    if before >= 5:
        return Eligibility(
            "non-ai-eligible",
            total,
            before,
            superseded,
            False,
            True,
            "at-least-5-adrs-no-signal",
        )
    return Eligibility("too-few-adrs", total, before, superseded_all, False, False, "fewer-than-5-adrs")


def check1_passed(ai_projects: int, non_ai_projects: int, superseded: int) -> bool:
    return (
        ai_projects >= PASS_AI_PROJECTS
        and non_ai_projects >= PASS_NON_AI_PROJECTS
        and superseded >= PASS_SUPERSEDED
    )
