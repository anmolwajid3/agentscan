"""Build the pilot samples and the scorecard from collected repositories.

Manual files, when present, are joined in. Missing manual files leave that
check marked as waiting, which is the honest state for a second rater or a
maintainer who has not replied yet.
"""

from __future__ import annotations

import csv
import json
import random
import re
from datetime import timezone
from pathlib import Path

from adr_pilot.eligibility import PASS_AI_PROJECTS, PASS_NON_AI_PROJECTS, PASS_SUPERSEDED, check1_passed, parse_dt
from adr_pilot.kappa import cohens_kappa, weighted_kappa

TIMING_PASS_FRACTION = 0.5
COMMIT_PASS_FRACTION = 0.8
ENDING_PASS_FRACTION = 0.85
CONFIRMED_USE_PASS = 16
TIMING_GAP_DAYS = 92
KAPPA_PASS = 0.6

DECISION_TYPES = (
    "data-storage",
    "interface",
    "integration",
    "deployment",
    "code-structure",
    "other",
)
ENDING_LABELS = (
    "replaced",
    "no-longer-needed",
    "rejected-before-use",
    "cleanup-or-rename",
)


def load_projects(repo_dir: Path) -> list[dict]:
    projects = []
    for path in sorted(repo_dir.glob("*.json")):
        if path.name.endswith(".tmp"):
            continue
        try:
            projects.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return projects


def _days(first: str | None, last: str | None) -> int | None:
    start, end = parse_dt(first), parse_dt(last)
    if not start or not end:
        return None
    return int((end - start).total_seconds() // 86400)


def _eligible(project: dict) -> bool:
    return project.get("group") in {"ai-eligible", "non-ai-eligible"}


def _strict(project: dict) -> bool:
    if not _eligible(project):
        return False
    authors = project.get("n_authors")
    if authors is not None and authors < 2:
        return False
    span = _days(project.get("first_commit"), project.get("last_commit"))
    if span is not None and span < 365:
        return False
    return True


def check1(projects: list[dict]) -> dict:
    ai = [p for p in projects if p.get("group") == "ai-eligible"]
    non = [p for p in projects if p.get("group") == "non-ai-eligible"]
    superseded = sum(int(p.get("superseded_in_window") or 0) for p in ai + non)
    strict_ai = sum(1 for p in ai if _strict(p))
    strict_non = sum(1 for p in non if _strict(p))
    strict_superseded = sum(int(p.get("superseded_in_window") or 0) for p in ai + non if _strict(p))
    return {
        "frame_rows": None,
        "analyzed": len(projects),
        "clone_failures": sum(1 for p in projects if not p.get("clone_ok", True)),
        "ai_eligible": len(ai),
        "non_ai_eligible": len(non),
        "ai_native": sum(1 for p in projects if p.get("group") == "ai-native"),
        "ai_too_few_before": sum(1 for p in projects if p.get("group") == "ai-too-few-before"),
        "too_few_adrs": sum(1 for p in projects if p.get("group") == "too-few-adrs"),
        "templates": sum(1 for p in projects if p.get("group") == "template"),
        "superseded_in_eligible_windows": superseded,
        "strict_ai_eligible": strict_ai,
        "strict_non_ai_eligible": strict_non,
        "strict_superseded": strict_superseded,
        "pass_bar": {
            "ai_projects": PASS_AI_PROJECTS,
            "non_ai_projects": PASS_NON_AI_PROJECTS,
            "superseded": PASS_SUPERSEDED,
        },
        "passed": check1_passed(len(ai), len(non), superseded),
        "passed_strict_real_project_filter": check1_passed(strict_ai, strict_non, strict_superseded),
    }


def _uses(project: dict) -> list[dict]:
    found = []
    for event in project.get("ai_signals") or []:
        if event.get("kind") in {"coauthor", "agent-author"} and event.get("date"):
            found.append(event)
    for mention in (project.get("mentions") or {}).get("strict") or []:
        # Re-apply the mention rule so a tightened pattern does not keep a
        # false hit that was stored by an earlier run.
        from adr_pilot.signals import mention_kind
        if mention_kind(mention.get("subject") or "") != "strict":
            continue
        if mention.get("date"):
            found.append(
                {
                    "kind": "mention",
                    "date": mention["date"],
                    "commit": mention.get("sha"),
                    "evidence": mention.get("subject") or "",
                    "name": "mention",
                }
            )
    return found


def _signal_file_commits(project: dict) -> set[str]:
    commits = set()
    for event in project.get("ai_signals") or []:
        if str(event.get("kind") or "").startswith("file:") and event.get("commit"):
            commits.add(event["commit"])
    return commits


def _qualifying_uses(project: dict) -> list[tuple]:
    """Uses that are not just the commit message of the instruction file itself."""
    signal_commits = _signal_file_commits(project)
    found = []
    for item in _uses(project):
        when = parse_dt(item.get("date"))
        if when is None:
            continue
        if item.get("kind") == "mention" and item.get("commit") in signal_commits:
            continue
        found.append((when, item))
    return found


def _confirmed(project: dict) -> tuple[bool, str | None, float | None]:
    """Return confirmed-use, earliest use date, and absolute gap in days.

    The instruction file is the signal, not the proof of use. A mention inside
    the commit that adds that file does not count. Co-author lines, agent
    authors, and mentions in other commits do.
    """
    signal = parse_dt(project.get("signal_date"))
    uses = _qualifying_uses(project)
    if not uses:
        return False, None, None
    earliest, _item = min(uses, key=lambda pair: pair[0])
    if signal is not None:
        confirmed = any(when >= signal for when, _item in uses)
        gap = abs((earliest - signal).total_seconds()) / 86400
    else:
        confirmed = True
        gap = None
    return confirmed, earliest.astimezone(timezone.utc).isoformat(), gap


def check2(projects: list[dict], rng: random.Random) -> dict:
    flagged_pool = [p for p in projects if p.get("signal_date") and p.get("clone_ok") and not p.get("likely_template")]
    quiet_pool = [
        p for p in projects
        if not p.get("signal_date") and p.get("clone_ok") and not p.get("likely_template") and int(p.get("adr_count") or 0) >= 5
    ]
    flagged = _sample(flagged_pool, 20, rng)
    quiet = _sample(quiet_pool, 20, rng)
    flagged_rows = [_check2_row(p, flagged=True) for p in flagged]
    quiet_rows = [_check2_row(p, flagged=False) for p in quiet]
    confirmed = sum(1 for row in flagged_rows if row["confirmed_use"])
    dated = [row for row in flagged_rows if row["abs_gap_days"] is not None]
    within = [row for row in dated if row["abs_gap_days"] <= TIMING_GAP_DAYS]
    hidden = sum(1 for row in quiet_rows if row["hidden_use"])
    timing_pass = len(dated) >= 10 and (len(within) / len(dated) >= 0.8 if dated else False)
    return {
        "flagged_n": len(flagged_rows),
        "confirmed_use": confirmed,
        "confirmed_pass": confirmed >= CONFIRMED_USE_PASS and len(flagged_rows) >= 20,
        "with_observable_start": len(dated),
        "within_92_days": len(within),
        "timing_pass": timing_pass,
        "hidden_use": hidden,
        "unflagged_n": len(quiet_rows),
        "passed": confirmed >= CONFIRMED_USE_PASS and len(flagged_rows) >= 20 and timing_pass,
        "flagged": flagged_rows,
        "unflagged": quiet_rows,
        "rule": (
            "Pass if at least 16 of 20 flagged projects have an AI co-author, agent author, "
            "or a strict tool mention on or after the signal date, and at least 80% of flagged "
            "projects that have an observable use date are within 92 days of the signal, "
            "with at least 10 such dates. The instruction file alone is not counted as use."
        ),
    }


def _check2_row(project: dict, flagged: bool) -> dict:
    confirmed, earliest, gap = _confirmed(project)
    hidden = (not flagged) and bool(_qualifying_uses(project))
    return {
        "repo": project.get("repo"),
        "signal_date": project.get("signal_date"),
        "signal_kind": project.get("signal_kind"),
        "earliest_observable_use": earliest,
        "abs_gap_days": None if gap is None else round(gap, 1),
        "confirmed_use": confirmed if flagged else "",
        "hidden_use": hidden if not flagged else "",
        "evidence": _evidence_snippet(project),
    }


def _evidence_snippet(project: dict) -> str:
    bits = []
    for event in (project.get("ai_signals") or [])[:3]:
        if event.get("kind") in {"coauthor", "agent-author", "file:primary"}:
            bits.append(f"{event.get('kind')}: {event.get('name') or ''} @ {event.get('date')}")
    for mention in ((project.get("mentions") or {}).get("strict") or [])[:2]:
        bits.append(f"mention: {mention.get('subject')} @ {mention.get('date')}")
    return " | ".join(bits)[:400]


def _sample(pool: list[dict], size: int, rng: random.Random) -> list[dict]:
    if len(pool) <= size:
        return list(pool)
    return rng.sample(pool, size)


def _link(repo: str, sha: str | None = None, path: str | None = None) -> str:
    base = "https://github.com/" + repo
    if sha and path:
        return f"{base}/blob/{sha}/{path}"
    if sha:
        return f"{base}/commit/{sha}"
    if path:
        return f"{base}/blob/HEAD/{path}"
    return base


def build_check3(projects: list[dict], rng: random.Random) -> list[dict]:
    pool = []
    for project in projects:
        if not _eligible(project):
            continue
        for adr in project.get("adrs") or []:
            text = adr.get("text") or ""
            if len(text) < 180:
                continue
            pool.append((project, adr))
    picked = pool if len(pool) <= 30 else rng.sample(pool, 30)
    rows = []
    for index, (project, adr) in enumerate(sorted(picked, key=lambda item: (item[0].get("repo") or "", item[1].get("path") or "")), start=1):
        impl = adr.get("implementation") or {}
        rows.append(
            {
                "case_id": f"C3-{index:02d}",
                "repo": project.get("repo"),
                "path": adr.get("path"),
                "title": adr.get("title"),
                "status": adr.get("status"),
                "first_commit": adr.get("first_commit"),
                "first_sha": adr.get("first_sha"),
                "adr_url": _link(project.get("repo") or "", adr.get("first_sha"), adr.get("path")),
                "discussion_refs": adr.get("discussion_refs") or [],
                "mentioned_paths": adr.get("mentioned_paths") or [],
                "script_commit": impl.get("sha"),
                "script_commit_date": impl.get("date"),
                "script_commit_subject": impl.get("subject"),
                "script_reason": impl.get("reason"),
                "script_paths": impl.get("paths") or [],
                "text": adr.get("text") or "",
                "author": adr.get("author"),
                "email": adr.get("email"),
            }
        )
    return rows


def _real_endings(projects: list[dict]) -> list[dict]:
    rows = []
    for project in projects:
        if not project.get("clone_ok") or project.get("likely_template"):
            continue
        for change in project.get("status_changes") or []:
            if change.get("script_rule") in {"not-an-ending", "status-unchanged"}:
                continue
            if change.get("new_state") == change.get("old_state") and not change.get("renamed") and change.get("new_state") != "deleted":
                continue
            adr = _adr_for(project, change)
            rows.append({"project": project, "change": change, "adr": adr})
    return rows


def _adr_for(project: dict, change: dict) -> dict:
    identity = change.get("identity")
    for adr in project.get("adrs") or []:
        if adr.get("identity") == identity or adr.get("path") == change.get("path"):
            return adr
    return {}


def relabel_change(change: dict) -> dict:
    """Apply the current ending rules to a stored transition.

    Collected JSON keeps the label from the run that cloned the repository.
    Check 4 scores the rules in this file, including pointer phrases added
    after that clone. The stored object is not mutated, so earlier samples
    that were drawn from the old labels stay stable.
    """
    from adr_pilot.endings import classify_ending
    from adr_pilot.status import find_replacement

    updated = dict(change)
    deleted = (change.get("new_state") or "") == "deleted"
    pointer = (
        change.get("replacement")
        or find_replacement(change.get("new_raw") or "")
        or find_replacement(change.get("message") or "")
    )
    ending = classify_ending(
        change.get("old_state"),
        change.get("old_state") if deleted else change.get("new_state"),
        old_raw=change.get("old_raw") or "",
        new_raw="" if deleted else (change.get("new_raw") or ""),
        message=change.get("message") or "",
        replacement=pointer,
        renamed=bool(change.get("renamed")),
        deleted=deleted,
    )
    updated["replacement"] = pointer or change.get("replacement")
    updated["script_label"] = ending.label
    updated["script_rule"] = ending.rule
    return updated


def build_check4(
    projects: list[dict],
    rng: random.Random,
    *,
    exclude: set[tuple[str, str]] | None = None,
) -> list[dict]:
    """About 30 endings, up to 8 of each script label.

    ``exclude`` holds (repository, path) pairs from the sample that was used
    to find a rule gap. Those rows must not be drawn again.
    """
    pool = []
    held = exclude or set()
    for row in _real_endings(projects):
        project = row["project"]
        key = (project.get("repo") or "", row["change"].get("path") or "")
        if key in held:
            continue
        row = {"project": project, "change": relabel_change(row["change"]), "adr": row["adr"]}
        if row["change"].get("script_rule") in {"not-an-ending", "status-unchanged"}:
            continue
        pool.append(row)
    by_label: dict[str, list[dict]] = {label: [] for label in ENDING_LABELS}
    for row in pool:
        by_label.setdefault(row["change"].get("script_label") or "cleanup-or-rename", []).append(row)
    picked: list[dict] = []
    for label in ENDING_LABELS:
        group = by_label.get(label) or []
        rng.shuffle(group)
        picked.extend(group[:8])
    if len(picked) < 30:
        rest = [row for row in pool if row not in picked]
        rng.shuffle(rest)
        picked.extend(rest[: 30 - len(picked)])
    picked = picked[:30]
    cases = []
    for index, row in enumerate(picked, start=1):
        project, change, adr = row["project"], row["change"], row["adr"]
        cases.append(
            {
                "case_id": f"C4-{index:02d}",
                "repo": project.get("repo"),
                "path": change.get("path"),
                "title": (adr or {}).get("title") or "",
                "date": change.get("date"),
                "commit": change.get("commit"),
                "commit_url": _link(project.get("repo") or "", change.get("commit")),
                "old_state": change.get("old_state"),
                "new_state": change.get("new_state"),
                "old_raw": change.get("old_raw"),
                "new_raw": change.get("new_raw"),
                "replacement": change.get("replacement"),
                "message": change.get("message"),
                "renamed": change.get("renamed"),
                "script_label": change.get("script_label"),
                "script_rule": change.get("script_rule"),
                "text": (adr or {}).get("text") or "",
                "author": change.get("author") or (adr or {}).get("author"),
                "email": change.get("email") or (adr or {}).get("email"),
            }
        )
    return cases


def build_check5(projects: list[dict], rng: random.Random) -> list[dict]:
    """15 reversals, one per repository when possible, mixing hard-looking and code-only cases."""
    pool = []
    for project in projects:
        if not project.get("clone_ok") or project.get("likely_template"):
            continue
        seen_paths = set()
        for change in project.get("status_changes") or []:
            if change.get("script_label") != "replaced":
                continue
            path = change.get("path") or ""
            if path in seen_paths:
                continue
            seen_paths.add(path)
            adr = _adr_for(project, change)
            pool.append(
                {
                    "case_id": "",
                    "repo": project.get("repo"),
                    "path": path,
                    "title": (adr or {}).get("title") or "",
                    "date": change.get("date"),
                    "commit": change.get("commit"),
                    "commit_url": _link(project.get("repo") or "", change.get("commit")),
                    "old_state": change.get("old_state"),
                    "new_state": change.get("new_state"),
                    "old_raw": change.get("old_raw"),
                    "new_raw": change.get("new_raw"),
                    "replacement": change.get("replacement"),
                    "message": change.get("message"),
                    "renamed": change.get("renamed"),
                    "script_label": change.get("script_label"),
                    "script_rule": change.get("script_rule"),
                    "text": (adr or {}).get("text") or "",
                    "author": change.get("author") or (adr or {}).get("author"),
                    "email": change.get("email") or (adr or {}).get("email"),
                }
            )
    rng.shuffle(pool)
    hardish = [case for case in pool if _hard_clues((case.get("text") or "") + " " + (case.get("new_raw") or ""))]
    soft = [case for case in pool if case not in hardish]

    def take(groups: list[list[dict]], limit: int) -> list[dict]:
        picked: list[dict] = []
        seen_repos: set[str] = set()
        for group in groups:
            for case in group:
                repo = case.get("repo") or ""
                if repo in seen_repos:
                    continue
                picked.append(case)
                seen_repos.add(repo)
                if len(picked) >= limit:
                    return picked
        for group in groups:
            for case in group:
                if case in picked:
                    continue
                picked.append(case)
                if len(picked) >= limit:
                    return picked
        return picked

    mixed = take([hardish, soft], 15)
    cases = []
    for index, case in enumerate(mixed, start=1):
        cases.append({**case, "case_id": f"C5-{index:02d}", "source_case": "", "clues": _clue_list(case)})
    return cases


def build_check6(check5_cases: list[dict]) -> list[dict]:
    with_email = [case for case in check5_cases if case.get("email")]
    chosen = (with_email or check5_cases)[:10]
    rows = []
    for index, case in enumerate(chosen, start=1):
        rows.append({**case, "case_id": f"C6-{index:02d}", "source_case": case["case_id"]})
    return rows


_CLUE_PATTERNS = {
    "data": re.compile(r"(?i)\b(migrat\w*|backfill|schema|existing data|dump)\b"),
    "outside": re.compile(r"(?i)\b(breaking change|public api|deprecat\w*|clients? must|external)\b"),
    "transition": re.compile(r"(?i)\b(next release|compatib\w*|until version|parallel run|transition period)\b"),
    "spread": re.compile(r"(?i)\b(service|repository|module|package)s?\b"),
}


def _hard_clues(text: str) -> bool:
    return bool(_CLUE_PATTERNS["data"].search(text) or _CLUE_PATTERNS["outside"].search(text) or _CLUE_PATTERNS["transition"].search(text))


def _clue_list(case: dict) -> str:
    text = (case.get("text") or "") + "\n" + (case.get("new_raw") or "")
    hits = [name for name, pattern in _CLUE_PATTERNS.items() if pattern.search(text)]
    return ",".join(hits)


def write_packets(path: Path, cases: list[dict], kind: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for case in cases:
        body = _packet_markdown(case, kind)
        (path / f"{case['case_id']}.md").write_text(body, encoding="utf-8")


def _packet_markdown(case: dict, kind: str) -> str:
    lines = [
        f"# {case['case_id']}",
        "",
        f"- Repository: `{case.get('repo')}`",
        f"- File: `{case.get('path')}`",
        f"- Title: {case.get('title') or '(no title)'}",
        f"- When: {case.get('first_commit') or case.get('date') or ''}",
    ]
    if case.get("adr_url"):
        lines.append(f"- Link: {case['adr_url']}")
    if case.get("commit_url"):
        lines.append(f"- Commit: {case['commit_url']}")
    if kind == "check3":
        lines += [
            "",
            "## What to decide before reading the script answer",
            "",
            "1. Was this record written first (before or during the discussion), written after the decision and the code already existed, or can't you tell?",
            "2. Which commit, if any, put the decision into the code? Use none if the record does not name code and you cannot see an implementing commit from the links.",
            "",
            f"Discussion refs: {json.dumps(case.get('discussion_refs') or [], ensure_ascii=False)}",
            f"Paths named in the record: {', '.join(case.get('mentioned_paths') or []) or '(none)'}",
            "",
            "## Record",
            "",
            case.get("text") or "(empty)",
            "",
            "## Script answer (read second)",
            "",
            f"- Implementation commit: `{case.get('script_commit') or 'none'}`",
            f"- Date: {case.get('script_commit_date') or ''}",
            f"- Subject: {case.get('script_commit_subject') or ''}",
            f"- Reason: {case.get('script_reason') or ''}",
            f"- Paths: {', '.join(case.get('script_paths') or [])}",
        ]
    elif kind == "check4":
        lines += [
            "",
            "Label this ending as one of: replaced, no-longer-needed, rejected-before-use, cleanup-or-rename.",
            "Decide from the text below. The script label is stored outside this packet.",
            "",
            f"- Status before: `{case.get('old_state')}` {case.get('old_raw') or ''}",
            f"- Status after: `{case.get('new_state')}` {case.get('new_raw') or ''}",
            f"- Commit message: {case.get('message') or ''}",
            f"- Git recorded a rename: {case.get('renamed')}",
            "",
            "## Record",
            "",
            case.get("text") or "(empty)",
        ]
    else:
        lines += [
            "",
            "Label decision type, the yes/no hard dimension, and the five scores.",
            "Use the classification guide. Do not discuss the case with the other rater.",
            "",
            f"- Status before: `{case.get('old_state')}`",
            f"- Status after: `{case.get('new_state')}` {case.get('new_raw') or ''}",
            f"- Commit message: {case.get('message') or ''}",
            f"- Words the extractor noticed (evidence, not a label): {case.get('clues') or '(none)'}",
            "",
            "## Record",
            "",
            case.get("text") or "(empty)",
        ]
    lines.append("")
    return "\n".join(lines)


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def score_manual(check3: list[dict], check4: list[dict], check5: list[dict], manual_dir: Path) -> dict:
    labels3 = {row["case_id"]: row for row in _read_csv(manual_dir / "check3_labels.csv")}
    labels4 = {row["case_id"]: row for row in _read_csv(manual_dir / "check4_labels.csv")}
    rater_a = _read_csv(manual_dir / "check5_rater_a.csv")
    rater_b = [row for row in _read_csv(manual_dir / "check5_rater_b.csv") if (row.get("decision_type") or "").strip()]
    replies = [row for row in _read_csv(manual_dir / "check6_replies.csv") if (row.get("hard_1_to_5") or "").strip()]
    maintainer = [row for row in _read_csv(manual_dir / "check2_replies.csv") if (row.get("maintainer_start") or "").strip()]

    judged_timing = []
    for case in check3:
        manual = labels3.get(case["case_id"])
        if not manual or not (manual.get("timing") or "").strip():
            continue
        judged_timing.append(manual["timing"].strip())
    placed = sum(1 for label in judged_timing if label in {"written-first", "written-after"})
    timing_rate = (placed / len(judged_timing)) if judged_timing else None

    commit_pairs = []
    for case in check3:
        manual = labels3.get(case["case_id"])
        if not manual or (manual.get("implementation_correct") or "").strip() == "":
            continue
        commit_pairs.append(manual["implementation_correct"].strip().lower() in {"yes", "y", "true", "1"})
    commit_rate = (sum(commit_pairs) / len(commit_pairs)) if commit_pairs else None

    agreements = []
    for case in check4:
        manual = labels4.get(case["case_id"])
        if not manual or not (manual.get("label") or "").strip():
            continue
        agreements.append(manual["label"].strip() == case.get("script_label"))
    ending_rate = (sum(agreements) / len(agreements)) if agreements else None

    kappa = None
    hard_kappa = None
    weighted = {}
    if rater_a and rater_b:
        by_b = {row["case_id"]: row for row in rater_b}
        type_pairs = []
        hard_pairs = []
        score_pairs = {key: [] for key in ("d1", "d2", "d3", "d4", "d5")}
        for row in rater_a:
            other = by_b.get(row.get("case_id") or "")
            if not other:
                continue
            if (row.get("decision_type") or "").strip() and (other.get("decision_type") or "").strip():
                type_pairs.append((row["decision_type"].strip(), other["decision_type"].strip()))
            if (row.get("hard") or "").strip() and (other.get("hard") or "").strip():
                hard_pairs.append((row["hard"].strip().lower(), other["hard"].strip().lower()))
            for key in score_pairs:
                if (row.get(key) or "").strip() and (other.get(key) or "").strip():
                    score_pairs[key].append((int(row[key]), int(other[key])))
        kappa = cohens_kappa(type_pairs)
        hard_kappa = cohens_kappa(hard_pairs)
        weighted = {key: weighted_kappa(pairs, categories=[0, 1, 2]) for key, pairs in score_pairs.items() if pairs}

    reality = None
    if replies:
        # A label of hard=yes should agree with a maintainer score of 4 or 5,
        # or with a yes on data movement or outside change. Compared in the
        # scorecard text; the numeric match is computed when rater A exists.
        by_a = {row["case_id"]: row for row in rater_a}
        matches = []
        for reply in replies:
            ours = by_a.get(reply.get("source_case") or reply.get("case_id") or "")
            if not ours:
                continue
            our_hard = (ours.get("hard") or "").strip().lower() in {"yes", "y", "true", "1"}
            try:
                score = int(reply.get("hard_1_to_5") or "")
            except ValueError:
                continue
            their_hard = score >= 4 or (reply.get("data_moved") or "").strip().lower() in {"yes", "y"} or (
                reply.get("outsiders_changed") or ""
            ).strip().lower() in {"yes", "y"}
            matches.append(our_hard == their_hard)
        reality = {
            "replies": len(replies),
            "compared": len(matches),
            "matches": sum(matches),
        }

    return {
        "check3": {
            "labeled": len(judged_timing),
            "placed_in_first_two_groups": placed,
            "placement_rate": timing_rate,
            "placement_pass": timing_rate is not None and timing_rate > TIMING_PASS_FRACTION,
            "implementation_judged": len(commit_pairs),
            "implementation_correct": sum(commit_pairs),
            "implementation_rate": commit_rate,
            "implementation_pass": commit_rate is not None and len(commit_pairs) >= 10 and commit_rate >= COMMIT_PASS_FRACTION,
        },
        "check4": {
            "labeled": len(agreements),
            "agreements": sum(agreements),
            "rate": ending_rate,
            "passed": ending_rate is not None and len(agreements) >= 15 and ending_rate >= ENDING_PASS_FRACTION,
        },
        "check5": {
            "rater_a": len([row for row in rater_a if (row.get("decision_type") or "").strip()]),
            "rater_b": len(rater_b),
            "decision_type_kappa": None if not kappa else kappa.get("kappa"),
            "hard_kappa": None if not hard_kappa else hard_kappa.get("kappa"),
            "weighted": {key: value.get("kappa") for key, value in weighted.items()},
            "passed": bool(
                kappa
                and hard_kappa
                and kappa.get("kappa") is not None
                and hard_kappa.get("kappa") is not None
                and kappa["kappa"] >= KAPPA_PASS
                and hard_kappa["kappa"] >= KAPPA_PASS
            ),
            "waiting_for_second_rater": len(rater_b) == 0,
        },
        "check6": {
            "replies": 0 if not reality else reality["replies"],
            "compared": 0 if not reality else reality["compared"],
            "matches": 0 if not reality else reality["matches"],
            "passed": bool(reality and reality["compared"] and reality["matches"] / reality["compared"] > 0.5),
            "waiting_for_replies": not replies,
        },
        "check2_maintainer_replies": len(maintainer),
    }


def write_project_table(projects: list[dict], path: Path) -> None:
    fields = [
        "repo", "group", "adr_count", "adr_count_before_signal", "superseded_in_window",
        "signal_date", "signal_kind", "first_commit", "last_commit", "n_authors", "n_commits",
        "n_code_files", "likely_template", "clone_ok", "error", "stars", "sources", "ai_file_probe",
    ]
    _write_csv(path, projects, fields)


def render_scorecard(summary: dict) -> str:
    c1 = summary["check1"]
    c2 = summary["check2"]
    manual = summary["manual"]
    lines = [
        "# Pilot scorecard",
        "",
        f"Run: {summary['generated']}",
        "",
        "The pass bars were fixed in the scripts before the counts were read.",
        "",
        "| Check | Result | Pass | If it fails |",
        "| --- | --- | --- | --- |",
        _row(
            "1. Enough data",
            f"{c1['ai_eligible']} projects with an AI signal and at least 5 earlier ADRs; "
            f"{c1['non_ai_eligible']} without a signal and at least 5 ADRs; "
            f"{c1['superseded_in_eligible_windows']} superseded decisions in those windows.",
            c1["passed"],
            "Stop or change the study. The full design is not possible in this form.",
        ),
        _row(
            "2. AI signal",
            f"{c2['confirmed_use']} of {c2['flagged_n']} flagged projects show use after the signal. "
            f"{c2['within_92_days']} of {c2['with_observable_start']} observable start dates fall within 92 days. "
            f"{c2['hidden_use']} of {c2['unflagged_n']} unflagged projects have a hidden trace. "
            f"Maintainer replies so far: {manual['check2_maintainer_replies']}.",
            c2["passed"],
            "Use only the strongest signal, or call projects AI-configured rather than AI-using.",
        ),
        _row(
            "3. Decision date",
            _check3_text(manual["check3"]),
            bool(manual["check3"]["placement_pass"] and manual["check3"]["implementation_pass"]),
            "Drop the timing question if most records were written after the decision.",
        ),
        _row(
            "4. Endings",
            _check4_text(manual["check4"]),
            bool(manual["check4"]["passed"]),
            "Tighten the rules, or check every reversal by hand.",
        ),
        _row(
            "5. Two raters",
            _check5_text(manual["check5"]),
            bool(manual["check5"]["passed"]),
            "Keep the yes/no hard dimension and drop the cheap/moderate/expensive scale.",
        ),
        _row(
            "6. Developers",
            _check6_text(manual["check6"]),
            bool(manual["check6"]["passed"]),
            "Rethink the complexity measure. Five replies are already useful.",
        ),
        "",
        "## Check 1 detail",
        "",
        f"- Repositories in the sampling frame: {c1.get('frame_rows') or 'unknown'}. "
        f"AI-file hits in that frame: {c1.get('frame_ai_probe') or 'unknown'}. "
        f"Measured in this run: {c1['analyzed']}. Not measured yet: {c1.get('frame_unmeasured') if c1.get('frame_unmeasured') is not None else 'unknown'}.",
        f"- Clone failures among the measured set: {c1['clone_failures']}.",
        "- Pass counts use the measured repositories. The first slice is every repository in the January 2022 census with at least 5 ADRs. A pass on that slice means at least that many projects qualify. Rows of the 2026 index that were not cloned are not in the pass count.",
        f"- AI-native (signal before any ADR, so no before period): {c1['ai_native']}.",
        f"- AI signal but fewer than 5 earlier ADRs: {c1['ai_too_few_before']}.",
        f"- Fewer than 5 ADRs and no signal: {c1['too_few_adrs']}.",
        f"- Templates and catalogs set aside: {c1['templates']}.",
        "- Stricter project filter (at least two authors and one year of history), not required by the pass bar: "
        f"{c1['strict_ai_eligible']} AI, {c1['strict_non_ai_eligible']} non-AI, {c1['strict_superseded']} superseded. "
        f"That stricter bar {'passes' if c1['passed_strict_real_project_filter'] else 'does not pass'}.",
        "",
        "## Check 4 detail",
        "",
        summary.get("check4_note") or "- Check 4 uses the sample in `check4_sample.csv`.",
        "",
        "## How to read a failure",
        "",
        "All six pass: the full study can go ahead.",
        "Some fail: keep the parts that passed. A smaller study is still a paper.",
        "Check 1 fails: do not spend months on this design.",
        "",
    ]
    return "\n".join(lines)


def _row(check: str, result: str, passed: bool, fallback: str) -> str:
    mark = "yes" if passed else "no"
    return f"| {check} | {result} | {mark} | {fallback} |"


def _check3_text(item: dict) -> str:
    if not item["labeled"]:
        return "Samples are ready. The hand labels have not been entered yet."
    rate = item["placement_rate"]
    commit = item["implementation_rate"]
    placed = "n/a" if rate is None else f"{rate:.0%}"
    found = "n/a" if commit is None else f"{item['implementation_correct']} of {item['implementation_judged']} ({commit:.0%})"
    return (
        f"{item['placed_in_first_two_groups']} of {item['labeled']} records placed as written-first or written-after ({placed}). "
        f"Script commit agreed in {found}."
    )


def _check4_text(item: dict) -> str:
    if not item["labeled"]:
        return "Samples are ready. The hand labels have not been entered yet."
    rate = "n/a" if item["rate"] is None else f"{item['rate']:.0%}"
    return f"Script agreed with the hand label in {item['agreements']} of {item['labeled']} ({rate})."


def _check5_text(item: dict) -> str:
    if item["waiting_for_second_rater"]:
        return f"Rater A labeled {item['rater_a']} cases. A second rater has not labeled them yet, so kappa is not computed."
    type_k = item["decision_type_kappa"]
    hard_k = item["hard_kappa"]
    return (
        f"Decision-type kappa {None if type_k is None else round(type_k, 2)}. "
        f"Hard-dimension kappa {None if hard_k is None else round(hard_k, 2)}."
    )


def _check6_text(item: dict) -> str:
    if item["waiting_for_replies"]:
        return "Emails are drafted. No maintainer has replied in the replies sheet yet."
    return f"{item['matches']} of {item['compared']} compared replies match the label."


def blank_manual_templates(manual: Path) -> None:
    manual.mkdir(parents=True, exist_ok=True)
    templates = {
        "check3_labels.csv": ["case_id", "timing", "timing_note", "implementation_correct", "implementation_note", "minutes"],
        "check4_labels.csv": ["case_id", "label", "note", "minutes"],
        "check5_rater_a.csv": ["case_id", "decision_type", "hard", "d1", "d2", "d3", "d4", "d5", "minutes", "note"],
        "check5_rater_b.csv": ["case_id", "decision_type", "hard", "d1", "d2", "d3", "d4", "d5", "minutes", "note"],
        "check6_replies.csv": ["case_id", "source_case", "hard_1_to_5", "data_moved", "outsiders_changed", "note"],
        "check2_replies.csv": ["repo", "maintainer_start", "note"],
    }
    for name, fields in templates.items():
        path = manual / name
        if path.exists():
            continue
        _write_csv(path, [], fields)
