"""Counts for P1. A missing exposure stays missing. It does not become zero."""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from swap_pilot.gitrepo import parse_dt

GROUPS = ("ai_after", "ai_before", "control_same_period")


def months_between(start: datetime | None, end: datetime | None, month_days: float) -> float | None:
    if start is None or end is None:
        return None
    days = (end - start).total_seconds() / 86400
    if days < 0:
        return 0.0
    return days / month_days


def exposure_months(project: dict, group: str, config: dict) -> float | None:
    cutoff = parse_dt(config["cutoff_date"] + "T00:00:00+00:00")
    control_start = parse_dt(config["control_start"] + "T00:00:00+00:00")
    first = parse_dt(project.get("first_commit"))
    last = parse_dt(project.get("last_commit"))
    adopted = parse_dt(project.get("adoption_date"))
    end = last if cutoff is None or last is None else min(last, cutoff)
    if group == "ai_after":
        return months_between(adopted, end, float(config["month_days"]))
    if group == "ai_before":
        return months_between(first, adopted, float(config["month_days"]))
    if group == "control_same_period":
        start = control_start if first is None else max(first, control_start) if control_start else first
        return months_between(start, end, float(config["month_days"]))
    return None


def _rate(swaps: int, exposure: float | None) -> str:
    if exposure is None or exposure == 0:
        return "NA"
    return f"{swaps / exposure * 100:.3f}"


def summarize(projects: list[dict], swaps: list[dict], config: dict) -> str:
    by_group = {group: [row for row in swaps if row.get("group") == group] for group in GROUPS}
    lines = [
        "# P1 summary",
        "",
        "This file is the five-project trial. The full population has not been run.",
        "The pass rule is not applied to five projects, and the thresholds were not changed.",
        "",
        "**Full-run result: not run.** Waiting for approval before cloning the He et al. list.",
        "",
        f"Cut-off: {config['cutoff_date']}. Control window starts {config['control_start']}.",
        f"Same-commit pass bar: at least {config['pass_ai_after_swaps']} ai_after swaps from more than {config['pass_ai_after_projects']} projects, and at least as many control_same_period swaps.",
        "",
    ]
    for mode in ("same commit", "30-day window"):
        lines.append(f"## {mode}")
        lines.append("")
        lines.append("| Group | Swaps | Projects | Exposure (project-months) | Swaps per 100 project-months | Share from top 5 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for group in GROUPS:
            rows = [row for row in by_group[group] if row.get("detection") == mode]
            projects_with = {row["project"] for row in rows}
            exposure = _group_exposure(projects, group, config)
            exposure_text = "NA" if exposure is None else f"{exposure:.1f}"
            lines.append(
                f"| {group} | {len(rows)} | {len(projects_with)} | {exposure_text} | {_rate(len(rows), exposure)} | {_top_share(rows)} |"
            )
        lines.append("")
    ai_after_same = [
        row for row in by_group["ai_after"] if row.get("detection") == "same commit"
    ]
    ai_flagged = sum(1 for row in ai_after_same if row.get("ai") == "yes")
    lines.append(f"Same-commit ai_after swaps with an AI co-author or agent author: {ai_flagged} of {len(ai_after_same)}.")
    lines.append("")
    for group in GROUPS:
        rows = [row for row in by_group[group] if row.get("detection") == "same commit"]
        lines.append(f"## Most common same-commit pairs: {group}")
        lines.append("")
        if not rows:
            lines.append("None.")
            lines.append("")
            continue
        counts = Counter(f"{row['lib_removed']} -> {row['lib_added']}" for row in rows)
        for pair, count in counts.most_common(20):
            lines.append(f"- {count}: {pair}")
        lines.append("")
    lines.append("## Same-commit swaps by quarter")
    lines.append("")
    lines.append("| Quarter | AI projects | Controls |")
    lines.append("| --- | --- | --- |")
    quarters = _quarters(swaps, projects, config)
    for quarter in sorted(quarters):
        lines.append(f"| {quarter} | {quarters[quarter]['ai']} | {quarters[quarter]['control']} |")
    lines.append("")
    return "\n".join(lines)


def _group_exposure(projects: list[dict], group: str, config: dict) -> float | None:
    total = 0.0
    seen = False
    for project in projects:
        belongs = False
        if group in {"ai_after", "ai_before"} and project.get("ai_signal") == "yes":
            belongs = True
        if group == "control_same_period" and project.get("ai_signal") == "no" and project.get("eligible") == "yes":
            belongs = True
        if not belongs:
            continue
        value = exposure_months(project, group, config)
        if value is None:
            return None
        total += value
        seen = True
    if not seen:
        return None
    return total


def _top_share(rows: list[dict]) -> str:
    if not rows:
        return "NA"
    counts = Counter(row["project"] for row in rows)
    top = sum(count for _, count in counts.most_common(5))
    return f"{top / len(rows):.1%}"


def _quarter_labels(config: dict) -> list[str]:
    start = parse_dt(str(config["quarter_start"]) + "T00:00:00+00:00")
    end = parse_dt(str(config["cutoff_date"]) + "T00:00:00+00:00")
    if start is None or end is None:
        return []
    labels = []
    year, month = start.year, ((start.month - 1) // 3) * 3 + 1
    while (year, month) <= (end.year, ((end.month - 1) // 3) * 3 + 1):
        labels.append(f"{year} Q{(month - 1) // 3 + 1}")
        month += 3
        if month > 12:
            month = 1
            year += 1
    return labels


def _quarters(swaps: list[dict], projects: list[dict], config: dict) -> dict[str, dict[str, int]]:
    ai_projects = {project["project"] for project in projects if project.get("ai_signal") == "yes"}
    control = {project["project"] for project in projects if project.get("ai_signal") == "no"}
    found: dict[str, dict[str, int]] = {label: {"ai": 0, "control": 0} for label in _quarter_labels(config)}
    for row in swaps:
        if row.get("detection") != "same commit":
            continue
        when = parse_dt(row.get("date"))
        if when is None or when.year < 2022:
            continue
        quarter = f"{when.year} Q{(when.month - 1) // 3 + 1}"
        bucket = found.setdefault(quarter, {"ai": 0, "control": 0})
        if row["project"] in ai_projects:
            bucket["ai"] += 1
        elif row["project"] in control:
            bucket["control"] += 1
    return found
