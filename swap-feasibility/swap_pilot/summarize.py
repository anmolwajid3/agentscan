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


def _is_main(row: dict) -> bool:
    return row.get("rule_category", "main") == "main"


def summarize(
    projects: list[dict],
    swaps: list[dict],
    config: dict,
    *,
    unparsed_rows: int | None = None,
    population_eligible: int | None = None,
    sample: bool = False,
) -> str:
    main = [row for row in swaps if _is_main(row)]
    renamed = [row for row in swaps if row.get("rule_category") == "rename"]
    by_group = {group: [row for row in main if row.get("group") == group] for group in GROUPS}
    if sample:
        intro = [
            "This file is a random sample of eligible projects. It is not the full population.",
            "No pass or fail is declared from the sample.",
            "",
            f"Sample seed: {config.get('sample_seed')}. Sample size target: {config.get('sample_size')}.",
        ]
    else:
        intro = [
            "This file is the five-project trial. The sample of eligible projects has not been run.",
            "No pass or fail is declared from five projects.",
        ]
    lines = [
        "# P1 summary",
        "",
        *intro,
        "",
        "The main counts use the 802 rules whose type does not start with `rename`.",
        "The 392 rename rules are reported in their own section and are not included in the main counts or the projection.",
        "",
        f"Cut-off: {config['cutoff_date']}. Control window starts {config['control_start']}.",
        f"The full-run bar, unchanged and not applied here, is at least {config['pass_ai_after_swaps']} same-commit ai_after swaps from more than {config['pass_ai_after_projects']} projects, and at least as many control_same_period swaps.",
        "",
    ]
    lines.extend(_mode_tables(projects, by_group, config, "Main rules"))
    ai_after_same = [row for row in by_group["ai_after"] if row.get("detection") == "same commit"]
    ai_flagged = sum(1 for row in ai_after_same if row.get("ai") == "yes")
    lines.append(
        f"Same-commit main-rule ai_after swaps with an AI co-author or agent author: {ai_flagged} of {len(ai_after_same)}."
    )
    lines.append("")
    lines.extend(_pairs(by_group, "Main rules"))
    lines.append("## Same-commit main-rule swaps by quarter")
    lines.append("")
    lines.append("| Quarter | AI projects | Controls |")
    lines.append("| --- | --- | --- |")
    quarters = _quarters(main, projects, config)
    for quarter in sorted(quarters):
        lines.append(f"| {quarter} | {quarters[quarter]['ai']} | {quarters[quarter]['control']} |")
    lines.append("")
    rename_groups = {group: [row for row in renamed if row.get("group") == group] for group in GROUPS}
    lines.append("## Rename rules, separate from the main count")
    lines.append("")
    lines.append(f"Rename rows in the rule file: 392. Rename swaps detected: {len(renamed)}.")
    lines.append("")
    lines.extend(_mode_tables(projects, rename_groups, config, "Rename rules"))
    if unparsed_rows is None:
        lines.append("Unparsed dependency rows: NA.")
    else:
        lines.append(f"Unparsed dependency rows after placeholder resolution: {unparsed_rows}.")
    lines.append("")
    lines.extend(_projection(projects, main, population_eligible))
    return "\n".join(lines)


def _mode_tables(projects: list[dict], by_group: dict, config: dict, title: str) -> list[str]:
    lines = []
    for mode in ("same commit", "30-day window"):
        lines.append(f"## {title}: {mode}")
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
    return lines


def _pairs(by_group: dict, title: str) -> list[str]:
    lines = []
    for group in GROUPS:
        rows = [row for row in by_group[group] if row.get("detection") == "same commit"]
        lines.append(f"## Most common same-commit pairs ({title}): {group}")
        lines.append("")
        if not rows:
            lines.append("None.")
            lines.append("")
            continue
        counts = Counter(f"{row['lib_removed']} -> {row['lib_added']}" for row in rows)
        for pair, count in counts.most_common(20):
            lines.append(f"- {count}: {pair}")
        lines.append("")
    return lines


def _projection(projects: list[dict], main_swaps: list[dict], population_eligible: int | None) -> list[str]:
    sample = [project for project in projects if project.get("eligible") == "yes"]
    swaps = [
        row for row in main_swaps if row.get("detection") == "same commit" and row.get("group") == "ai_after"
    ]
    ai_projects = [project for project in sample if project.get("ai_signal") == "yes"]
    lines = ["## Projection", ""]
    if not sample or population_eligible is None:
        lines.append("Projected ai_after swaps in the full eligible population: NA.")
        lines.append("AI projects needed to reach 100: NA.")
        lines.append("")
        return lines
    per_project = len(swaps) / len(sample)
    projected = per_project * population_eligible
    lines.append(f"Eligible projects in this file: {len(sample)}.")
    lines.append(f"Eligible population the projection scales to: {population_eligible}.")
    lines.append(f"Same-commit main-rule ai_after swaps in the sample: {len(swaps)}.")
    lines.append(f"Projected ai_after swaps in the full eligible population: {projected:.1f}.")
    if not ai_projects or not swaps:
        lines.append("AI projects needed to reach 100 such swaps: NA. The observed rate is zero or the sample has no AI project.")
    else:
        per_ai = len(swaps) / len(ai_projects)
        lines.append(f"AI projects in the sample: {len(ai_projects)}.")
        lines.append(f"Such swaps per AI project: {per_ai:.4f}.")
        lines.append(f"AI projects needed to reach 100 such swaps at this rate: {100 / per_ai:.1f}.")
    lines.append("The projection is not a pass or fail.")
    lines.append("")
    return lines


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
