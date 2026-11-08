"""Counts for P1. A missing exposure stays missing. It does not become zero."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from swap_pilot.gitrepo import parse_dt

GROUPS = ("ai_after", "ai_before", "control_same_period")


def library_family(coordinate: str | None) -> str:
    """Group id of a Maven coordinate. Several artifacts in one group are one family."""
    text = (coordinate or "").strip()
    if ":" not in text:
        return text
    return text.split(":", 1)[0]


def decision_key(row: dict) -> tuple:
    """One commit swapping several artifacts of the same two families is one decision."""
    return (
        row.get("project") or "",
        row.get("commit") or "",
        row.get("pair_commit") or "",
        row.get("detection") or "",
        library_family(row.get("lib_removed")),
        library_family(row.get("lib_added")),
    )


def collapse_decisions(rows: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    chosen: list[dict] = []
    for row in rows:
        key = decision_key(row)
        if key in seen:
            continue
        seen.add(key)
        chosen.append(row)
    return chosen


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
    population_screened: int | None = None,
    sample: bool = False,
) -> str:
    main = [row for row in swaps if _is_main(row)]
    renamed = [row for row in swaps if row.get("rule_category") == "rename"]
    by_group = {group: [row for row in main if row.get("group") == group] for group in GROUPS}
    if sample:
        intro = [
            "Interim. This file is a random sample of eligible projects. It is not the full population.",
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
        "# P1 summary" + (" (interim)" if sample else ""),
        "",
        *intro,
        "",
        "Artifact swaps count every library coordinate pair. Decisions count a commit once when it swaps several artifacts of the same two group ids.",
        "Rates and the projection use decisions. Artifact counts stay beside them.",
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
    ai_after_decisions = collapse_decisions(ai_after_same)
    ai_flagged = sum(1 for row in ai_after_same if row.get("ai") == "yes")
    ai_flagged_decisions = sum(1 for row in ai_after_decisions if row.get("ai") == "yes")
    lines.append(
        f"Same-commit main-rule ai_after artifact swaps with an AI co-author or agent author: {ai_flagged} of {len(ai_after_same)}."
    )
    lines.append(
        f"Same-commit main-rule ai_after decisions with an AI co-author or agent author: {ai_flagged_decisions} of {len(ai_after_decisions)}."
    )
    lines.append("")
    lines.extend(_pairs(by_group, "Main rules"))
    lines.append("## Same-commit main-rule decisions by quarter")
    lines.append("")
    lines.append("| Quarter | AI projects | Controls |")
    lines.append("| --- | --- | --- |")
    quarters = _quarters(collapse_decisions(main), projects, config)
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
    lines.extend(_projection(projects, main, population_eligible, population_screened))
    lines.extend(_event_time(projects, main, config))
    lines.extend(_all_pairs(swaps))
    return "\n".join(lines)


def _mode_tables(projects: list[dict], by_group: dict, config: dict, title: str) -> list[str]:
    lines = []
    for mode in ("same commit", "30-day window"):
        lines.append(f"## {title}: {mode}")
        lines.append("")
        lines.append("| Group | Artifact swaps | Decisions | Projects | Exposure (project-months) | Decisions per 100 project-months | Share from top 5 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for group in GROUPS:
            rows = [row for row in by_group[group] if row.get("detection") == mode]
            chosen = collapse_decisions(rows)
            projects_with = {row["project"] for row in chosen}
            exposure = _group_exposure(projects, group, config)
            exposure_text = "NA" if exposure is None else f"{exposure:.1f}"
            lines.append(
                f"| {group} | {len(rows)} | {len(chosen)} | {len(projects_with)} | {exposure_text} | {_rate(len(chosen), exposure)} | {_top_share(chosen)} |"
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


def _projection(
    projects: list[dict],
    main_swaps: list[dict],
    population_eligible: int | None,
    population_screened: int | None = None,
) -> list[str]:
    sample = [project for project in projects if project.get("eligible") == "yes"]
    swaps = [
        row for row in main_swaps if row.get("detection") == "same commit" and row.get("group") == "ai_after"
    ]
    chosen = collapse_decisions(swaps)
    ai_projects = [project for project in sample if project.get("ai_signal") == "yes"]
    lines = ["## Projection", ""]
    lines.append("Interim. The projection uses decisions. It is not a pass or fail.")
    lines.append("")
    if not sample or population_eligible is None:
        lines.append("Projected ai_after decisions in the full eligible population: NA.")
        lines.append("Additional AI projects needed to reach 100: NA.")
        lines.append("")
        return lines
    per_project = len(chosen) / len(sample)
    projected = per_project * population_eligible
    lines.append(f"Eligible projects in this file: {len(sample)}.")
    lines.append(f"Eligible population the projection scales to: {population_eligible}.")
    lines.append(f"Same-commit main-rule ai_after artifact swaps in the sample: {len(swaps)}.")
    lines.append(f"Same-commit main-rule ai_after decisions in the sample: {len(chosen)}.")
    lines.append(f"Projected ai_after artifact swaps in the full eligible population: {len(swaps) / len(sample) * population_eligible:.1f}.")
    lines.append(f"Projected ai_after decisions in the full eligible population: {projected:.1f}.")
    if population_screened and population_screened != population_eligible:
        screened = len(chosen) / len(sample) * population_screened
        lines.append(
            f"Projected ai_after decisions in the {population_screened} projects that passed the GitHub screen: {screened:.1f}."
        )
    if not ai_projects or not chosen:
        lines.append("Additional AI projects needed to reach 100 decisions: NA. The observed decision rate is zero or the sample has no AI project.")
    else:
        per_ai = len(chosen) / len(ai_projects)
        expected_ai = len(ai_projects) / len(sample) * population_eligible
        additional = (100 - projected) / per_ai
        lines.append(f"AI projects in the sample: {len(ai_projects)}.")
        lines.append(f"Decisions per AI project: {per_ai:.4f}.")
        lines.append(f"AI projects expected in the full eligible population: {expected_ai:.1f}.")
        lines.append(f"AI projects needed in total to reach 100 decisions at this rate: {100 / per_ai:.1f}.")
        if additional <= 0:
            lines.append("Additional AI projects, beyond those expected in that population, needed to reach 100 decisions: 0.")
        else:
            lines.append(
                f"Additional AI projects, beyond those expected in that population, needed to reach 100 decisions: {additional:.1f}."
            )
    lines.append("The projection is not a pass or fail.")
    lines.append("")
    return lines


def _event_time(projects: list[dict], main_swaps: list[dict], config: dict) -> list[str]:
    """Six-month bins around each AI project's own adoption date."""
    month_days = float(config["month_days"])
    cutoff = parse_dt(config["cutoff_date"] + "T23:59:59+00:00")
    width_days = 6 * month_days
    decisions = collapse_decisions(
        [row for row in main_swaps if row.get("detection") == "same commit"]
    )
    by_project: dict[str, list[dict]] = {}
    for row in decisions:
        by_project.setdefault(row.get("project") or "", []).append(row)
    ai = []
    for project in projects:
        if project.get("ai_signal") != "yes":
            continue
        adopted = parse_dt(project.get("adoption_date"))
        if adopted is None:
            continue
        ai.append(project)
    lines = ["## Event-time rates", ""]
    lines.append("Interim. Same-commit main-rule decisions for projects with an AI signal, in 6-month bins around each project's own adoption date.")
    lines.append("The window starts 24 months before adoption and runs through the cut-off. The rate is decisions per 100 project-months.")
    lines.append("")
    if not ai or cutoff is None:
        lines.append("No AI project with an adoption date.")
        lines.append("")
        return lines
    max_forward = 0.0
    for project in ai:
        adopted = parse_dt(project.get("adoption_date"))
        last = parse_dt(project.get("last_commit"))
        if adopted is None or last is None:
            continue
        end = min(last, cutoff)
        if end > adopted:
            max_forward = max(max_forward, (end - adopted).total_seconds() / 86400 / month_days)
    forward_bins = int(max_forward // 6) + 1
    indexes = list(range(-4, forward_bins))
    lines.append("| Months relative to adoption | Decisions | Projects | Exposure (project-months) | Decisions per 100 project-months |")
    lines.append("| --- | --- | --- | --- | --- |")
    for index in indexes:
        decisions_n = 0
        names: set[str] = set()
        exposure = 0.0
        for project in ai:
            adopted = parse_dt(project.get("adoption_date"))
            first = parse_dt(project.get("first_commit"))
            last = parse_dt(project.get("last_commit"))
            if adopted is None or first is None or last is None:
                continue
            bin_start = adopted + timedelta(days=index * width_days)
            bin_end = adopted + timedelta(days=(index + 1) * width_days)
            obs_start = max(first, adopted - timedelta(days=4 * width_days))
            obs_end = min(last, cutoff)
            start = max(bin_start, obs_start)
            finish = min(bin_end, obs_end)
            value = months_between(start, finish, month_days)
            if value:
                exposure += value
            for row in by_project.get(project.get("project") or "", []):
                when = parse_dt(row.get("date"))
                if when is None or when < bin_start or when >= bin_end:
                    continue
                if when < obs_start or when > obs_end:
                    continue
                decisions_n += 1
                names.add(project["project"])
        lines.append(
            f"| {_bin_label(index)} | {decisions_n} | {len(names)} | {exposure:.1f} | {_rate(decisions_n, exposure)} |"
        )
    lines.append("")
    return lines


def _bin_label(index: int) -> str:
    start = index * 6
    end = start + 6
    return f"{start} to {end}"


def library_pair_rows(swaps: list[dict]) -> list[dict]:
    """Every distinct coordinate pair, with artifact counts and decision counts."""
    grouped: dict[tuple, dict] = {}
    for row in swaps:
        key = (
            row.get("lib_removed") or "",
            row.get("lib_added") or "",
            row.get("rule_category") or "",
            row.get("rule_type") or "",
        )
        bucket = grouped.setdefault(key, {"artifact": 0, "decisions": set(), "same": 0, "window": 0})
        bucket["artifact"] += 1
        bucket["decisions"].add(decision_key(row))
        if row.get("detection") == "same commit":
            bucket["same"] += 1
        elif row.get("detection") == "30-day window":
            bucket["window"] += 1
    rows = []
    for (removed, added, category, rule_type), bucket in grouped.items():
        rows.append(
            {
                "lib_removed": removed,
                "lib_added": added,
                "rule_category": category,
                "rule_type": rule_type,
                "artifact_swaps": bucket["artifact"],
                "decisions": len(bucket["decisions"]),
                "same_commit": bucket["same"],
                "window": bucket["window"],
            }
        )
    rows.sort(key=lambda item: (-item["artifact_swaps"], item["lib_removed"], item["lib_added"]))
    return rows


def _all_pairs(swaps: list[dict]) -> list[str]:
    rows = library_pair_rows(swaps)
    lines = ["## Library pairs for review", ""]
    lines.append("Interim. Every distinct library pair in the detected swaps. Nothing has been removed.")
    lines.append("A relocation or a mismatch stays in this list so it can be reviewed.")
    lines.append("")
    if not rows:
        lines.append("None.")
        lines.append("")
        return lines
    lines.append("| Removed | Added | Rule | Artifact swaps | Decisions | Same commit | 30-day window |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        lines.append(
            f"| {row['lib_removed']} | {row['lib_added']} | {row['rule_category']}:{row['rule_type']} | {row['artifact_swaps']} | {row['decisions']} | {row['same_commit']} | {row['window']} |"
        )
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
