"""Analyze a seeded random sample of projects that pass the GitHub screen."""

from __future__ import annotations

import csv
import json
import random
import shutil
import subprocess
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from swap_pilot.adopt import adoption
from swap_pilot.config import load_config
from swap_pilot.detect import assign_group, dependency_changes, pom_commits, same_commit_swaps, window_swaps
from swap_pilot.gitrepo import (
    first_commit_date,
    had_pom_before,
    head_sha,
    last_commit_date,
    parse_dt,
    rev_count,
)
from swap_pilot.rules import load_rules
from swap_pilot.screen import screen
from swap_pilot.summarize import summarize

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
SCREEN = ROOT / "eligibility_screen.csv"
STATE = ROOT / "sample_state"
CLONE_ROOT = Path("/tmp/swap-sample")
CHANGE_FIELDS = ["project", "commit", "date", "file", "change", "lib", "unparsed", "parse_note"]
SWAP_FIELDS = [
    "project", "commit", "pair_commit", "date", "lib_removed", "lib_added",
    "rule_id", "rule_type", "rule_category", "detection", "bot", "ai", "group",
]


def run_sample() -> None:
    config = load_config(CONFIG_PATH)
    if not SCREEN.exists():
        screen()
    queue, population_api = _queue(int(config["sample_seed"]))
    target = int(config["sample_size"])
    if population_api < target:
        raise SystemExit(
            f"GitHub screening found {population_api} eligible projects, which is under {target}. The sample was not cloned."
        )
    STATE.mkdir(parents=True, exist_ok=True)
    workers = int(config["sample_workers"])
    included: list[dict] = []
    decided_yes = 0
    decided_no = 0
    index = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        while index < len(queue) and len(included) < target:
            wave = queue[index : index + workers]
            index += len(wave)
            futures = {pool.submit(_analyze, name): name for name in wave}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001
                    result = _failed(name, f"worker failed: {exc}")
                _save(result)
                status = result["project"].get("eligible")
                if status == "yes":
                    decided_yes += 1
                    included.append(result)
                elif status == "no":
                    decided_no += 1
                print(
                    f"sample yes {decided_yes} no {decided_no} last {name} {status} {result['note']}",
                    flush=True,
                )
    included = _prefix(queue, target)
    _publish(included, config, population_api, decided_yes, decided_no)
    print(f"wrote sample of {len(included)} projects", flush=True)


def _queue(seed: int) -> tuple[list[str], int]:
    rows = []
    with SCREEN.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("api_eligible") == "yes":
                rows.append(row["project"])
    population = len(rows)
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows, population


def _prefix(queue: list[str], target: int) -> list[dict]:
    """First `target` eligible results in the seeded order, not completion order."""
    chosen = []
    for name in queue:
        path = STATE / f"{name.replace('/', '__')}.json"
        if not path.exists():
            break
        result = json.loads(path.read_text(encoding="utf-8"))
        if result["project"].get("eligible") == "yes":
            chosen.append(result)
        if len(chosen) >= target:
            break
    return chosen


def _analyze(name: str) -> dict:
    config = load_config(CONFIG_PATH)
    rules = load_rules(ROOT / "source" / "rules_typed.csv")
    screen_row = _screen_row(name)
    dest = CLONE_ROOT / name.replace("/", "__")
    shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        cloned = subprocess.run(
            [
                "git", "clone", "--filter=blob:none", "--no-checkout", "--single-branch",
                f"https://github.com/{name}.git", str(dest),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=int(config["sample_clone_timeout_seconds"]),
            env={**dict(**__import__("os").environ), "GIT_TERMINAL_PROMPT": "0"},
        )
        if cloned.returncode != 0 or not (dest / ".git").exists():
            return _failed(name, (cloned.stderr or "clone failed")[:200], screen_row)
        row = _measure(name, dest, screen_row, config)
        if row["eligible"] != "yes":
            return {"project": row, "swaps": [], "changes": [], "note": row["eligibility_note"]}
        signal = adoption(str(dest))
        row.update(signal)
        commits = pom_commits(str(dest))
        changes, events = dependency_changes(str(dest), name, commits)
        control_start = parse_dt(config["control_start"] + "T00:00:00+00:00")
        cutoff = parse_dt(config["cutoff_date"] + "T23:59:59+00:00")
        found = same_commit_swaps(name, events, rules)
        found.extend(window_swaps(name, events, rules, int(config["window_days"])))
        for swap in found:
            swap["group"] = assign_group(swap, row["ai_signal"], row["adoption_date"], control_start, cutoff)
        return {"project": row, "swaps": found, "changes": changes, "note": "ok"}
    except subprocess.TimeoutExpired:
        return _failed(name, "clone timed out", screen_row)
    except Exception:
        return _failed(name, traceback.format_exc().splitlines()[-1][:200], screen_row)
    finally:
        shutil.rmtree(dest, ignore_errors=True)


def _measure(name: str, dest: Path, screen_row: dict, config: dict) -> dict:
    before = rev_count(str(dest), before="2024-01-01")
    during = rev_count(str(dest), after="2022-12-31", before="2024-01-01")
    pom = had_pom_before(str(dest), "2024-01-01")
    archived_now = screen_row.get("archived_now") or "NA"
    archived_before = "no" if archived_now == "no" else "NA"
    row = {
        "project": name,
        "eligible": "NA",
        "eligibility_note": "",
        "fork": screen_row.get("fork") or "NA",
        "archived_now": archived_now,
        "archived_before_cutoff": archived_before,
        "pom_before_cutoff": "" if pom is None else ("yes" if pom else "no"),
        "commits_before_cutoff": "" if before is None else before,
        "commits_in_2023": "" if during is None else during,
        "first_commit": first_commit_date(str(dest)),
        "last_commit": last_commit_date(str(dest)),
        "head": head_sha(str(dest)),
        "ai_signal": "NA",
        "adoption_date": "",
        "signal_type": "",
        "clone_ok": "yes",
    }
    reasons = []
    if row["fork"] == "yes":
        reasons.append("fork")
    if archived_now == "yes":
        reasons.append("archived now, archive date unknown")
    if row["pom_before_cutoff"] != "yes":
        reasons.append("no pom.xml before 2024")
    if row["commits_before_cutoff"] == "" or int(row["commits_before_cutoff"]) < int(config["min_commits_before"]):
        reasons.append("fewer than 50 commits before 2024")
    if row["commits_in_2023"] == "" or int(row["commits_in_2023"]) < int(config["min_commits_in_year"]):
        reasons.append("fewer than 10 commits in 2023")
    if reasons:
        row["eligible"] = "no"
        row["eligibility_note"] = "; ".join(reasons)
    else:
        row["eligible"] = "yes"
        row["eligibility_note"] = "eligible on history through 2023-12-31 and GitHub fork/archive status"
    return row


def _screen_row(name: str) -> dict:
    with SCREEN.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["project"] == name:
                return row
    return {}


def _failed(name: str, note: str, screen_row: dict | None = None) -> dict:
    screen_row = screen_row or {}
    return {
        "project": {
            "project": name,
            "eligible": "NA",
            "eligibility_note": note,
            "fork": screen_row.get("fork") or "NA",
            "archived_now": screen_row.get("archived_now") or "NA",
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
        },
        "swaps": [],
        "changes": [],
        "note": note,
    }


def _save(result: dict) -> None:
    name = result["project"]["project"].replace("/", "__")
    payload = {"project": result["project"], "swaps": result["swaps"], "note": result["note"]}
    (STATE / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    path = STATE / f"{name}.changes.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHANGE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in result["changes"]:
            writer.writerow({key: row.get(key, "") for key in CHANGE_FIELDS})


def _publish(included: list[dict], config: dict, population_api: int, decided_yes: int, decided_no: int) -> None:
    # Scale the API-eligible count by the share that still failed the git pom and commit check.
    decided = decided_yes + decided_no
    if decided:
        population = int(round(population_api * (decided_yes / decided)))
    else:
        population = None
    projects = [item["project"] for item in included]
    swaps = [swap for item in included for swap in item["swaps"]]
    rules = load_rules(ROOT / "source" / "rules_typed.csv")
    _write_projects(projects)
    unparsed = _write_changes(included)
    _write_swaps(swaps)
    text = summarize(
        projects,
        swaps,
        config,
        unparsed_rows=unparsed,
        population_eligible=population,
        sample=True,
    )
    text += _population_note(population_api, population, decided_yes, decided_no, len(included))
    (ROOT / "p1_summary.md").write_text(text, encoding="utf-8")
    _p2(swaps, included, int(config["p2_seed"]), int(config["p2_swap_sample"]), int(config["p2_removal_sample"]))
    _log(config, rules, included, population_api, population)


def _population_note(population_api: int, population: int | None, decided_yes: int, decided_no: int, kept: int) -> str:
    adjusted = "NA" if population is None else str(population)
    return "\n".join(
        [
            "## Eligible population",
            "",
            f"GitHub screening marked {population_api} projects eligible before the pom.xml check.",
            f"Of the screened projects cloned in seed order, {decided_yes} passed the git history check and {decided_no} failed it. Clone failures are not in either number.",
            f"The projection uses {adjusted} as the full eligible population: the screened count times that pass rate.",
            f"Projects kept in this sample: {kept}.",
            "",
        ]
    )


def _write_projects(projects: list[dict]) -> None:
    fields = list(projects[0].keys()) if projects else ["project"]
    with (ROOT / "projects.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in projects:
            writer.writerow({key: row.get(key, "") for key in fields})


def _write_changes(included: list[dict]) -> int:
    unparsed = 0
    with (ROOT / "dependency_changes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHANGE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for item in included:
            path = STATE / f"{item['project']['project'].replace('/', '__')}.changes.csv"
            if not path.exists():
                continue
            with path.open(newline="", encoding="utf-8") as source:
                for row in csv.DictReader(source):
                    writer.writerow({key: row.get(key, "") for key in CHANGE_FIELDS})
                    if row.get("unparsed") == "yes":
                        unparsed += 1
    return unparsed


def _write_swaps(swaps: list[dict]) -> None:
    with (ROOT / "swaps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SWAP_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in swaps:
            writer.writerow({key: row.get(key, "") for key in SWAP_FIELDS})


def _p2(swaps: list[dict], included: list[dict], seed: int, swap_n: int, removal_n: int) -> None:
    rng = random.Random(seed)
    same = [
        row for row in swaps
        if row.get("detection") == "same commit" and row.get("rule_category") == "main"
    ]
    rng.shuffle(same)
    swapped = {(row["project"], row["commit"], row["lib_removed"]) for row in same}
    bare = []
    for item in included:
        path = STATE / f"{item['project']['project'].replace('/', '__')}.changes.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("change") == "rem" and row.get("unparsed") == "no":
                    if (row["project"], row["commit"], row["lib"]) not in swapped:
                        bare.append(row)
    rng.shuffle(bare)
    out = ROOT / "p2_samples"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "swaps.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(same[0].keys()) if same else ["project"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in same[:swap_n]:
            writer.writerow({key: row.get(key, "") for key in fields})
    with (out / "removals_without_swap.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["project", "commit", "date", "lib", "unparsed"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in bare[:removal_n]:
            writer.writerow({key: row.get(key, "") for key in fields})
    (out / "README.md").write_text(
        "\n".join(
            [
                "# P2 samples",
                "",
                f"Seed {seed}. These rows were drawn and not checked.",
                "The swap sample is same-commit swaps from the 802 non-rename rules.",
                f"Such swaps available: {len(same)}. Drawn: {min(swap_n, len(same))}.",
                f"Removals with no such swap available: {len(bare)}. Drawn: {min(removal_n, len(bare))}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _log(config: dict, rules: dict, included: list[dict], population_api: int, population: int | None) -> None:
    try:
        git_version = subprocess.run(["git", "--version"], check=False, capture_output=True, text=True).stdout.strip()
    except OSError:
        git_version = "NA"
    main_rules = sum(1 for rule in rules.values() if not str(rule["rule_type"]).startswith("rename"))
    lines = [
        "# Run log",
        "",
        f"Data cut-off: {config['cutoff_date']}",
        f"Sample seed: {config['sample_seed']}",
        f"P2 seed: {config['p2_seed']}",
        f"Rules loaded: {len(rules)} from source/rules_typed.csv",
        f"Main rules (not rename): {main_rules}",
        f"API-eligible projects: {population_api}",
        f"Eligible population used in the projection: {population if population is not None else 'NA'}",
        "Replication package: Zenodo 10.5281/zenodo.5091384 (concept 10.5281/zenodo.4816752).",
        f"Git: {git_version}",
        f"Python: {__import__('sys').version.split()[0]}",
        "",
        "Sample heads:",
        "",
    ]
    for item in included:
        row = item["project"]
        lines.append(f"- {row['project']} {row.get('head') or 'NA'}")
    lines.append("")
    (ROOT / "RUN_LOG.md").write_text("\n".join(lines), encoding="utf-8")
