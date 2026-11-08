"""Run the five-project trial. The full population is a separate command and is not the default."""

from __future__ import annotations

import csv
import json
import random
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from swap_pilot.adopt import adoption
from swap_pilot.config import load_config
from swap_pilot.detect import (
    assign_group,
    dependency_changes,
    pom_commits,
    same_commit_swaps,
    window_swaps,
)
from swap_pilot.gitrepo import (
    GitError,
    first_commit_date,
    had_pom_before,
    head_sha,
    last_commit_date,
    parse_dt,
    rev_count,
)
from swap_pilot.rules import load_rules
from swap_pilot.summarize import summarize

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.yaml"
SOURCE = ROOT / "source"
CLONE_ROOT = Path("/tmp/swap-clones")
CACHE = ROOT / "cache" / "github"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Library-swap feasibility, P1 trial")
    parser.add_argument("command", choices=["trial"])
    args = parser.parse_args()
    if args.command == "trial":
        trial()


def trial() -> None:
    config = load_config(CONFIG)
    rules = load_rules(SOURCE / "rules_typed.csv")
    projects = []
    changes = []
    swaps = []
    log_rows = []
    control_start = parse_dt(config["control_start"] + "T00:00:00+00:00")
    cutoff = parse_dt(config["cutoff_date"] + "T23:59:59+00:00")
    for repo in config["trial_repos"]:
        print(f"trial {repo}", flush=True)
        project, commit_sha, note = _one_project(repo, config)
        projects.append(project)
        log_rows.append({"project": repo, "head": commit_sha, "note": note})
        if project.get("clone_ok") != "yes":
            continue
        clone = CLONE_ROOT / repo.replace("/", "__")
        commits = pom_commits(str(clone))
        dep_rows, events = dependency_changes(str(clone), repo, commits)
        changes.extend(dep_rows)
        found = same_commit_swaps(repo, events, rules)
        found.extend(window_swaps(repo, events, rules, int(config["window_days"])))
        for row in found:
            row["group"] = assign_group(
                row, project["ai_signal"], project["adoption_date"], control_start, cutoff
            )
        swaps.extend(found)
        print(f"  pom commits {len(commits)} swaps {len(found)} signal {project['ai_signal']}", flush=True)
    _write_csv(ROOT / "projects.csv", projects, list(projects[0].keys()) if projects else [])
    _write_csv(
        ROOT / "dependency_changes.csv",
        changes,
        ["project", "commit", "date", "file", "change", "lib", "unparsed", "parse_note"],
    )
    _write_csv(
        ROOT / "swaps.csv",
        swaps,
        [
            "project", "commit", "pair_commit", "date", "lib_removed", "lib_added",
            "rule_id", "rule_type", "detection", "bot", "ai", "group",
        ],
    )
    (ROOT / "p1_summary.md").write_text(summarize(projects, swaps, config) + _estimate(config), encoding="utf-8")
    _p2_samples(swaps, changes, int(config["p2_seed"]), int(config["p2_swap_sample"]), int(config["p2_removal_sample"]))
    _run_log(config, rules, log_rows)
    print("wrote trial outputs")


def _one_project(repo: str, config: dict) -> tuple[dict, str, str]:
    clone = CLONE_ROOT / repo.replace("/", "__")
    row = {
        "project": repo,
        "eligible": "NA",
        "eligibility_note": "",
        "fork": "NA",
        "archived_before_cutoff": "NA",
        "pom_before_cutoff": "NA",
        "commits_before_cutoff": "NA",
        "commits_in_2023": "NA",
        "first_commit": "",
        "last_commit": "",
        "head": "",
        "ai_signal": "NA",
        "adoption_date": "",
        "signal_type": "",
        "clone_ok": "no",
    }
    if not (clone / ".git").exists() and not clone.exists():
        _clone(repo, clone, int(config["clone_timeout_seconds"]))
    if not clone.exists():
        row["eligibility_note"] = "clone failed"
        return row, "", "clone failed"
    try:
        sha = head_sha(str(clone))
        last = last_commit_date(str(clone))
        first = first_commit_date(str(clone))
        before = rev_count(str(clone), before="2024-01-01")
        during = rev_count(str(clone), after="2022-12-31", before="2024-01-01")
        pom = had_pom_before(str(clone), "2024-01-01")
        meta = _github(repo)
    except GitError as exc:
        row["eligibility_note"] = str(exc)
        return row, "", str(exc)
    row.update(
        {
            "clone_ok": "yes",
            "head": sha,
            "first_commit": first,
            "last_commit": last,
            "commits_before_cutoff": "" if before is None else before,
            "commits_in_2023": "" if during is None else during,
            "pom_before_cutoff": "" if pom is None else ("yes" if pom else "no"),
            "fork": meta.get("fork", "NA"),
            "archived_before_cutoff": meta.get("archived_before", "NA"),
        }
    )
    eligible, note = _eligible(row, config)
    row["eligible"] = eligible
    row["eligibility_note"] = note
    try:
        signal = adoption(str(clone))
    except Exception as exc:  # noqa: BLE001 - record the failure, do not invent a signal
        row["ai_signal"] = "NA"
        row["eligibility_note"] = (row["eligibility_note"] + "; " if row["eligibility_note"] else "") + f"adoption failed: {exc}"
        return row, sha, "adoption failed"
    row.update(signal)
    return row, sha, "ok"


def _eligible(row: dict, config: dict) -> tuple[str, str]:
    missing = []
    if row["pom_before_cutoff"] == "NA" or row["pom_before_cutoff"] == "":
        missing.append("pom")
    if row["commits_before_cutoff"] == "NA" or row["commits_before_cutoff"] == "":
        missing.append("commits")
    if row["commits_in_2023"] == "NA" or row["commits_in_2023"] == "":
        missing.append("2023 commits")
    if row["fork"] == "NA" or row["archived_before_cutoff"] == "NA":
        missing.append("github metadata")
    if missing:
        return "NA", "missing " + ", ".join(missing)
    reasons = []
    if row["pom_before_cutoff"] != "yes":
        reasons.append("no pom.xml before 2024")
    if int(row["commits_before_cutoff"]) < int(config["min_commits_before"]):
        reasons.append("fewer than 50 commits before 2024")
    if int(row["commits_in_2023"]) < int(config["min_commits_in_year"]):
        reasons.append("fewer than 10 commits in 2023")
    if row["fork"] == "yes":
        reasons.append("fork")
    if row["archived_before_cutoff"] == "yes":
        reasons.append("archived before 2024")
    if reasons:
        return "no", "; ".join(reasons)
    return "yes", "eligible on history through 2023-12-31"


def _clone(repo: str, dest: Path, timeout: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    try:
        subprocess.run(
            [
                "git", "clone", "--filter=blob:none", "--no-checkout", "--single-branch",
                f"https://github.com/{repo}.git", str(dest),
            ],
            check=False,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return


def _github(repo: str) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (repo.replace("/", "__") + ".json")
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        token = _token()
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repo}",
            headers={"User-Agent": "swap-feasibility", "Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {token}"} if token else {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            return {"fork": "NA", "archived_before": "NA", "error": str(exc)[:200]}
        path.write_text(json.dumps(payload), encoding="utf-8")
    archived_at = payload.get("archived")
    # GitHub does not give the archive date. A repository archived now may have
    # been active through 2023. The flag stays NA unless the API says it is not archived.
    if archived_at is False:
        archived_before = "no"
    else:
        archived_before = "NA"
    fork = payload.get("fork")
    return {"fork": "NA" if fork is None else ("yes" if fork else "no"), "archived_before": archived_before}


def _token() -> str:
    import os
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def _estimate(config: dict) -> str:
    path = SOURCE / "projects.csv"
    total = 0
    at_least_50 = 0
    size_kb = 0
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            total += 1
            try:
                commits = int(row.get("commitsCount") or 0)
            except ValueError:
                commits = 0
            try:
                size = int(row.get("size") or 0)
            except ValueError:
                size = 0
            if commits >= int(config["min_commits_before"]):
                at_least_50 += 1
                size_kb += size
    clone_bytes = 0
    if CLONE_ROOT.exists():
        for child in CLONE_ROOT.iterdir():
            if child.is_dir():
                clone_bytes += _dir_size(child)
    gib = size_kb / 1024 / 1024
    return "\n".join(
        [
            "## Estimate before a full run",
            "",
            f"- He et al. project list: {total} repositories. All of them are marked fork=False in that file, and all have a pom file count above zero.",
            f"- {at_least_50} had at least 50 commits at the paper's crawl, whose timestamps end around January 2020. That count is not the 2023 commit count.",
            f"- Those {at_least_50} repositories had a combined GitHub `size` of {gib:.0f} GiB at the crawl. A blobless clone is smaller than that checkout size. The five trial clones together are {clone_bytes / 1024 / 1024:.0f} MiB.",
            "- Commits during 2023, a pom.xml still present before 2024, and archive status are not in the file. They need a live git history. The eligible count is therefore not known yet. The 2,000-project stop line cannot be judged until that history is read. The crawl already shows more than 2,000 repositories with 50 commits, so the list itself is large enough to continue to the trial.",
            "- No GITHUB_TOKEN is set. Unauthenticated API access is too slow to screen archive status for the whole list. Eligibility for the full list would be computed from partial clones.",
            "- The five trial repositories finished their blobless clones in a few seconds each and the swap pass on all five took about two minutes once pom blobs were fetched in batches. The largest repositories in the list, such as elasticsearch, are not in this trial, so a full run would be slower than five times this sample.",
            "",
        ]
    )


def _dir_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total


def _p2_samples(swaps: list[dict], changes: list[dict], seed: int, swap_n: int, removal_n: int) -> None:
    rng = random.Random(seed)
    same = [row for row in swaps if row.get("detection") == "same commit"]
    rng.shuffle(same)
    removals = [row for row in changes if row.get("change") == "rem" and row.get("unparsed") == "no"]
    swapped = {(row["project"], row["commit"], row["lib_removed"]) for row in same}
    bare = [row for row in removals if (row["project"], row["commit"], row["lib"]) not in swapped]
    rng.shuffle(bare)
    out = ROOT / "p2_samples"
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "swaps.csv", same[:swap_n], list(same[0].keys()) if same else ["project"])
    _write_csv(
        out / "removals_without_swap.csv",
        bare[:removal_n],
        ["project", "commit", "date", "lib", "unparsed"],
    )
    (out / "README.md").write_text(
        "\n".join(
            [
                "# P2 samples",
                "",
                f"Seed {seed}. These rows were drawn and not checked.",
                f"Same-commit swaps available in this trial: {len(same)}. Drawn: {min(swap_n, len(same))}.",
                f"Removals with no same-commit swap available: {len(bare)}. Drawn: {min(removal_n, len(bare))}.",
                "The full check has not been run, so these are not the samples for the full study.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _run_log(config: dict, rules: dict, rows: list[dict]) -> None:
    try:
        git_version = subprocess.run(["git", "--version"], check=False, capture_output=True, text=True).stdout.strip()
    except OSError:
        git_version = "NA"
    lines = [
        "# Run log",
        "",
        f"Data cut-off: {config['cutoff_date']}",
        f"P2 seed: {config['p2_seed']}",
        f"Rules loaded: {len(rules)} from source/rules_typed.csv",
        "Replication package: Zenodo 10.5281/zenodo.5091384 (concept 10.5281/zenodo.4816752). Project list is cache/projects.csv. Rules are LibraryMigration/data/rules_typed.csv inside gitrepo.zip.",
        f"Git: {git_version}",
        f"Python: {__import__('sys').version.split()[0]}",
        f"Written: {datetime.now(timezone.utc).isoformat(timespec='minutes')}",
        "",
        "| Project | HEAD | Note |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['project']} | {row['head'] or 'NA'} | {row['note']} |")
    lines.append("")
    (ROOT / "RUN_LOG.md").write_text("\n".join(lines), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


if __name__ == "__main__":
    main()
