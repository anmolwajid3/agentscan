"""Clone candidates and write one JSON file per repository.

The run is resumable: a repository that already has a JSON file is skipped.
Clones are deleted after they are measured so disk use stays flat.
"""

from __future__ import annotations

import json
import os
import shutil
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from adr_pilot.analyze import GitError, analyze_clone, clone_repo
from adr_pilot.eligibility import classify_project


def _safe(name: str) -> str:
    return name.replace("github.com/", "").replace("/", "__")


def _priority(row: dict) -> tuple:
    """AI-file hits and known ADR projects first. Higher sorts later, so negate."""
    ai = 0 if row.get("ai_file_probe") == "yes" else 1
    try:
        count = int(row.get("buchgeher_adr_count") or 0)
    except ValueError:
        count = 0
    in_census = 0 if "buchgeher-2022" in (row.get("sources") or "") else 1
    return (ai, in_census, -count, row.get("repository") or "")


def _one(row: dict, dest_root: Path, out_dir: Path) -> dict:
    name = row["repository"]
    out = out_dir / f"{_safe(name)}.json"
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    clone = dest_root / _safe(name)
    if clone.exists():
        shutil.rmtree(clone, ignore_errors=True)
    extra = [part for part in (row.get("buchgeher_dirs") or "").split(";") if part]
    try:
        clone_repo(row["url"], str(clone), timeout=150)
        result = analyze_clone(
            str(clone),
            repo_name=name.removeprefix("github.com/"),
            description=row.get("description") or "",
            extra_paths=extra,
        )
    except (GitError, OSError, TimeoutError) as exc:
        result = _failure(name, str(exc))
    except Exception as exc:  # noqa: BLE001 - one repo must not stop the pilot
        result = _failure(name, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-500:]}")
    finally:
        shutil.rmtree(clone, ignore_errors=True)
    result["sources"] = row.get("sources") or ""
    result["stars"] = row.get("stars") or ""
    result["ai_file_probe"] = row.get("ai_file_probe") or ""
    result["buchgeher_adr_count"] = row.get("buchgeher_adr_count") or ""
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=1), encoding="utf-8")
    os.replace(temporary, out)
    return result


def _failure(name: str, error: str) -> dict:
    eligibility = classify_project(
        adr_dates=[],
        superseded_flags=[],
        signal_date=None,
        likely_template=False,
        clone_ok=False,
    )
    return {
        "repo": name.removeprefix("github.com/"),
        "clone_ok": False,
        "error": error[:500],
        "group": eligibility.group,
        "adr_count": 0,
        "adr_count_before_signal": 0,
        "superseded_in_window": 0,
        "adrs": [],
        "status_changes": [],
        "ai_signals": [],
        "mentions": {},
        "signal_date": None,
        "signal_kind": None,
        "likely_template": False,
    }


def pilot_slice(rows: list[dict]) -> list[dict]:
    """The measured slice.

    The full frame is kept on disk. Measuring every candidate is not required
    to answer check 1, and a capped search is not a census. This slice is the
    part the pilot actually clones:

    - every repository the 2022 census recorded with at least 5 ADRs
    - every frame repository whose index hit contained "superseded by"
    - up to 200 further repositories with an AI-file hit, highest star count first
    - up to 150 further repositories with no AI-file hit, highest star count first

    A pass on this slice means at least this many projects qualify. A failure
    leaves the unmeasured rows of the frame as an open gap, and the scorecard
    says so.
    """
    census: list[dict] = []
    superseded: list[dict] = []
    ai_extra: list[dict] = []
    quiet_extra: list[dict] = []
    for row in rows:
        try:
            count = int(row.get("buchgeher_adr_count") or 0)
        except ValueError:
            count = 0
        if count >= 5:
            census.append(row)
            continue
        if row.get("superseded_probe") == "yes":
            superseded.append(row)
            continue
        if row.get("ai_file_probe") == "yes":
            ai_extra.append(row)
        else:
            quiet_extra.append(row)

    def stars(row: dict) -> int:
        try:
            return int(float(row.get("stars") or 0))
        except ValueError:
            return 0

    ai_extra.sort(key=stars, reverse=True)
    quiet_extra.sort(key=stars, reverse=True)
    return census + superseded + ai_extra[:200] + quiet_extra[:150]


def collect(rows: list[dict], out_dir: Path, clone_root: Path, workers: int = 3, limit: int | None = None) -> list[dict]:
    ordered = sorted(rows, key=_priority)
    if limit:
        # Keep a mix: every AI-probed repo, then fill with the rest.
        ai = [row for row in ordered if row.get("ai_file_probe") == "yes"]
        rest = [row for row in ordered if row.get("ai_file_probe") != "yes"]
        ordered = (ai + rest)[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    clone_root.mkdir(parents=True, exist_ok=True)
    pending = [row for row in ordered if not (out_dir / f"{_safe(row['repository'])}.json").exists()]
    print(f"collecting {len(pending)} repositories, {len(ordered) - len(pending)} already done, workers={workers}")
    results: list[dict] = []
    if not pending:
        return results
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, row, clone_root, out_dir): row for row in pending}
        for index, future in enumerate(as_completed(futures), start=1):
            row = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = _failure(row["repository"], str(exc))
            results.append(result)
            if index % 10 == 0 or index == len(pending):
                print(
                    f"  {index}/{len(pending)} {result.get('repo')} "
                    f"group={result.get('group')} adrs={result.get('adr_count')}"
                )
    return results
