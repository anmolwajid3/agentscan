"""Command line for the six feasibility checks.

    python -m adr_pilot discover
    python -m adr_pilot collect --workers 3
    python -m adr_pilot report
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from adr_pilot.collect import collect, pilot_slice
from adr_pilot.discover import build_frame, read_frame, write_frame
from adr_pilot.report import (
    blank_manual_templates,
    build_check3,
    build_check4,
    build_check5,
    build_check6,
    check1,
    check2,
    load_projects,
    render_scorecard,
    score_manual,
    write_packets,
    write_project_table,
    _write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPOS = DATA / "repos"
MANUAL = DATA / "manual"


def _discover(args: argparse.Namespace) -> None:
    rows = build_frame(Path(args.buchgeher))
    write_frame(rows, DATA / "sampling_frame.csv")
    print(f"wrote {len(rows)} repositories to {DATA / 'sampling_frame.csv'}")


def _collect(args: argparse.Namespace) -> None:
    frame_path = DATA / "sampling_frame.csv"
    if not frame_path.exists():
        raise SystemExit("No sampling frame. Run: python -m adr_pilot discover")
    rows = read_frame(frame_path)
    if args.slice == "pilot":
        rows = pilot_slice(rows)
        print(f"pilot slice: {len(rows)} repositories")
    collect(rows, REPOS, Path(args.clone_root), workers=args.workers, limit=args.limit)


def _held_out_repos(path: Path) -> set[str]:
    """Repositories from the Check 2 sample that exposed the date problem."""
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as handle:
        return {row.get("repo") or "" for row in csv.DictReader(handle) if row.get("repo")}


def _held_out_paths(path: Path) -> set[tuple[str, str]]:
    """Repository and path pairs from the sample that exposed the ending-rule gap."""
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row.get("repo") or "", row.get("path") or "") for row in csv.DictReader(handle)}


def _report(_args: argparse.Namespace) -> None:
    projects = load_projects(REPOS)
    if not projects:
        raise SystemExit("No collected repositories. Run: python -m adr_pilot collect")
    write_project_table(projects, DATA / "projects.csv")
    rng3 = random.Random(20261108)
    rng2 = random.Random(20261111)
    rng4 = random.Random(20261110)
    rng5 = random.Random(20261109)
    summary1 = check1(projects)
    frame_path = DATA / "sampling_frame.csv"
    if frame_path.exists():
        import csv
        with frame_path.open(encoding="utf-8", newline="") as handle:
            frame_rows = list(csv.DictReader(handle))
        summary1["frame_rows"] = len(frame_rows)
        summary1["frame_ai_probe"] = sum(1 for row in frame_rows if row.get("ai_file_probe") == "yes")
        summary1["frame_unmeasured"] = max(0, len(frame_rows) - len(projects))
    held_repos = _held_out_repos(DATA / "check2_development_sample.csv")
    summary2 = check2(projects, rng2, exclude=held_repos)
    cases3 = build_check3(projects, rng3)
    held_out = _held_out_paths(DATA / "check4_development_sample.csv")
    cases4 = build_check4(projects, rng4, exclude=held_out)
    cases5 = build_check5(projects, rng5)
    cases6 = build_check6(cases5)
    _write_cases(DATA / "check2_sample.csv", summary2)
    _write_check_table(DATA / "check3_sample.csv", cases3)
    _write_check_table(DATA / "check4_sample.csv", cases4)
    _write_check_table(DATA / "check5_sample.csv", cases5)
    _write_check_table(DATA / "check6_sample.csv", cases6)
    write_packets(DATA / "packets" / "check3", cases3, "check3")
    write_packets(DATA / "packets" / "check4", cases4, "check4")
    write_packets(DATA / "packets" / "check5", cases5, "check5")
    write_packets(DATA / "packets" / "check6", cases6, "check5")
    _write_csv(
        DATA / "check4_script_labels.csv",
        [{"case_id": case["case_id"], "script_label": case["script_label"], "script_rule": case["script_rule"]} for case in cases4],
        ["case_id", "script_label", "script_rule"],
    )
    blank_manual_templates(MANUAL)
    _write_letters(cases2_flagged=summary2["flagged"], cases6=cases6)
    manual = score_manual(cases3, cases4, cases5, MANUAL)
    generated = datetime.now(timezone.utc).astimezone().isoformat(timespec="minutes")
    summary = {
        "generated": generated,
        "check1": summary1,
        "check2": {key: value for key, value in summary2.items() if key not in {"flagged", "unflagged"}},
        "manual": manual,
        "samples": {
            "check3": len(cases3),
            "check4": len(cases4),
            "check5": len(cases5),
            "check6": len(cases6),
        },
        "check2_note": (
            f"- Check 2 is a fresh sample, seed 20261111. It excludes the {len(held_repos)} "
            "repositories in `check2_development_sample.csv`. The adoption date is the earliest "
            "instruction file, AI co-author line, or agent author. The gap is measured to the "
            "earliest co-author or agent author. An earlier commit-message mention does not move the date, "
            "and a project with no co-author or agent author keeps a blank gap."
        ),
        "check4_note": (
            f"- Check 4 is a fresh sample of {len(cases4)}, seed 20261110. "
            f"It shares no file with the first 30 (`check4_development_sample.csv`), "
            "which is where the pointer-phrase misses were found. That first sample is not the reported accuracy. "
            "The fresh mix is "
            + ", ".join(
                f"{sum(1 for case in cases4 if case.get('script_label') == label)} {label}"
                for label in ("replaced", "no-longer-needed", "rejected-before-use", "cleanup-or-rename")
            )
            + ". The measured repositories only contain 9 rejected-before-use transitions and 9 no-longer-needed transitions, and the first sample had already taken most of them."
        ),
    }
    (DATA / "scorecard.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    text = render_scorecard(summary)
    (DATA / "SCORECARD.md").write_text(text, encoding="utf-8")
    print(text)


def _write_cases(path: Path, summary2: dict) -> None:
    rows = []
    for row in summary2["flagged"]:
        rows.append({**row, "arm": "flagged"})
    for row in summary2["unflagged"]:
        rows.append({**row, "arm": "unflagged"})
    fields = [
        "arm", "repo", "signal_date", "signal_kind", "adoption_date", "strong_use_date",
        "earliest_mention", "earliest_observable_use", "abs_gap_days", "confirmed_use",
        "hidden_use", "evidence",
    ]
    _write_csv(path, rows, fields)


def _write_check_table(path: Path, cases: list[dict]) -> None:
    fields = [
        "case_id", "repo", "path", "title", "status", "first_commit", "date",
        "old_state", "new_state", "script_label", "script_rule", "script_reason",
        "script_commit", "author", "email", "commit_url", "adr_url",
    ]
    _write_csv(path, cases, fields)


def _write_letters(cases2_flagged: list[dict], cases6: list[dict]) -> None:
    lines = [
        "# Letters to send",
        "",
        "These are drafts. Nothing has been sent. Public git addresses are included",
        "because the pilot asks you to write to the people who made the change.",
        "Send them from your own account, and stop if someone asks not to be contacted.",
        "",
        "## Check 2. Ten projects, one question",
        "",
        "Question: roughly when did your team start using AI coding tools?",
        "",
    ]
    for row in cases2_flagged[:10]:
        lines += [
            f"### {row['repo']}",
            "",
            f"Signal date in git: {row.get('signal_date') or '(none)'} ({row.get('signal_kind') or ''})",
            "",
            "Subject: One question about AI coding tools",
            "",
            "Hello,",
            "",
            f"I am a PhD student studying architecture decision records. In {row['repo']} I can see a public trace that may mean the project uses an AI coding tool. I am not asking for anything private.",
            "",
            "Roughly when did your team start using AI coding tools on this project, if you did? A month and a year is enough. If the project has not used them, that answer helps too.",
            "",
            "Thank you,",
            "Anmol",
            "",
        ]
    lines += [
        "## Check 6. Ten reversals, three questions",
        "",
        "Record replies in `data/manual/check6_replies.csv`.",
        "",
    ]
    for case in cases6:
        lines += [
            f"### {case['case_id']} {case.get('repo')} {case.get('path')}",
            "",
            f"To: {case.get('author') or ''} <{case.get('email') or 'address not in the sampled commit'}>",
            f"Commit: {case.get('commit_url') or ''}",
            "",
            "Subject: Three short questions about a design change",
            "",
            "Hello,",
            "",
            f"I am a PhD student studying architecture decisions. I am looking at this public decision record in {case.get('repo')}: {case.get('path')}. The status change is dated {case.get('date') or ''}.",
            "",
            "Three questions, and a one-line answer is enough:",
            "",
            "1. How hard was it to change this decision? (1 = trivial, 5 = very hard)",
            "2. Did existing data have to be moved or converted?",
            "3. Did users or other systems have to change anything?",
            "",
            "Thank you,",
            "Anmol",
            "",
        ]
    (DATA / "letters.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="ADR feasibility pilot")
    sub = parser.add_subparsers(dest="command", required=True)
    discover = sub.add_parser("discover")
    discover.add_argument("--buchgeher", default="/tmp/adr-dataset")
    discover.set_defaults(func=_discover)
    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("--workers", type=int, default=3)
    collect_parser.add_argument("--limit", type=int, default=0)
    collect_parser.add_argument("--slice", choices=("all", "pilot"), default="all")
    collect_parser.add_argument("--clone-root", default="/tmp/adr-clones")
    collect_parser.set_defaults(func=_collect)
    report = sub.add_parser("report")
    report.set_defaults(func=_report)
    args = parser.parse_args()
    if args.command == "collect" and args.limit == 0:
        args.limit = None
    args.func(args)


if __name__ == "__main__":
    main()
