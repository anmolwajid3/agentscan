"""Re-apply the AI allowlist to projects already saved by the sample."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from swap_pilot.adopt import adoption, commit_is_ai
from swap_pilot.config import load_config
from swap_pilot.detect import assign_group
from swap_pilot.gitrepo import parse_dt

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "sample_state"
CONFIG = ROOT / "config.yaml"
CLONE_ROOT = Path("/tmp/swap-redetect")
REPORT = ROOT / "adoption_allowlist_interim.md"


def redetect() -> None:
    config = load_config(CONFIG)
    names = _adopters()
    print(f"redetect {len(names)} adopters", flush=True)
    workers = min(8, max(1, int(config.get("sample_workers") or 4)))
    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, name): name for name in names}
        done = 0
        for future in as_completed(futures):
            name = futures[future]
            done += 1
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {"project": name, "status": "not rechecked", "error": str(exc)[:200]}
            results.append(result)
            if done % 25 == 0 or done == len(names):
                print(f"  redetect {done}/{len(names)}", flush=True)
    _apply(results, config)
    _report(results)
    dropped = [row for row in results if row.get("status") == "dropped"]
    changed = [row for row in results if row.get("status") in {"dropped", "date changed"}]
    print(f"checked {len(results)} changed {len(changed)} dropped {len(dropped)}", flush=True)


def _adopters() -> list[str]:
    names = []
    for path in sorted(STATE.glob("*.json")):
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        project = result.get("project") or {}
        if project.get("eligible") == "yes" and project.get("ai_signal") == "yes":
            names.append(project["project"])
    return names


def _one(name: str) -> dict:
    path = STATE / f"{name.replace('/', '__')}.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    project = saved["project"]
    dest = CLONE_ROOT / name.replace("/", "__")
    shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        cloned = subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", "--single-branch", f"https://github.com/{name}.git", str(dest)],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
            env={**dict(**__import__("os").environ), "GIT_TERMINAL_PROMPT": "0"},
        )
        if cloned.returncode != 0 or not (dest / ".git").exists():
            return {"project": name, "status": "not rechecked", "error": (cloned.stderr or "clone failed")[:200]}
        fresh = adoption(str(dest))
        old_date = project.get("adoption_date") or ""
        new_date = fresh.get("adoption_date") or ""
        old_type = project.get("signal_type") or ""
        new_type = fresh.get("signal_type") or ""
        same_date = parse_dt(old_date) == parse_dt(new_date) if old_date or new_date else True
        if fresh.get("ai_signal") == "no":
            status = "dropped"
        elif same_date and new_type == old_type:
            status = "unchanged"
        else:
            status = "date changed"
        swaps = saved.get("swaps") or []
        if status != "unchanged":
            _refresh_commit_flags(dest, swaps)
        return {
            "project": name,
            "status": status,
            "old_date": old_date,
            "old_type": old_type,
            "new_signal": fresh.get("ai_signal") or "no",
            "new_date": new_date,
            "new_type": new_type,
            "swaps": swaps,
        }
    except subprocess.TimeoutExpired:
        return {"project": name, "status": "not rechecked", "error": "clone timed out"}
    except Exception as exc:  # noqa: BLE001
        return {"project": name, "status": "not rechecked", "error": str(exc)[:200]}
    finally:
        shutil.rmtree(dest, ignore_errors=True)


def _refresh_commit_flags(dest: Path, swaps: list[dict]) -> None:
    seen: dict[str, str] = {}
    for row in swaps:
        sha = row.get("commit") or ""
        if not sha:
            continue
        if sha not in seen:
            seen[sha] = _commit_flag(dest, sha)
        row["ai"] = seen[sha]


def _commit_flag(dest: Path, sha: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(dest), "log", "-1", f"--format=%an%x1f%ae%x1f%B", sha],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        return "no"
    name, email, message = (result.stdout.split("\x1f", 2) + ["", "", ""])[:3]
    return "yes" if commit_is_ai(name, email, message) else "no"


def _apply(results: list[dict], config: dict) -> None:
    control_start = parse_dt(config["control_start"] + "T00:00:00+00:00")
    cutoff = parse_dt(config["cutoff_date"] + "T23:59:59+00:00")
    for row in results:
        if row.get("status") not in {"dropped", "date changed"}:
            continue
        path = STATE / f"{row['project'].replace('/', '__')}.json"
        saved = json.loads(path.read_text(encoding="utf-8"))
        project = saved["project"]
        project["ai_signal"] = row.get("new_signal") or "no"
        project["adoption_date"] = row.get("new_date") or ""
        project["signal_type"] = row.get("new_type") or ""
        swaps = row.get("swaps") or saved.get("swaps") or []
        for swap in swaps:
            swap["group"] = assign_group(
                swap,
                project["ai_signal"],
                project["adoption_date"],
                control_start,
                cutoff,
            )
        saved["swaps"] = swaps
        path.write_text(json.dumps(saved), encoding="utf-8")


def _report(results: list[dict]) -> None:
    dropped = [row for row in results if row.get("status") == "dropped"]
    moved = [row for row in results if row.get("status") == "date changed"]
    unchanged = [row for row in results if row.get("status") == "unchanged"]
    missed = [row for row in results if row.get("status") == "not rechecked"]
    lines = [
        "# Adoption allowlist recheck (interim)",
        "",
        "Interim. Names and emails match the exact allowlist in config.yaml. This is not a pass or fail.",
        "",
        f"Saved adopters rechecked: {len(results)}.",
        f"Unchanged: {len(unchanged)}.",
        f"Still adopters, with a different date or signal: {len(moved)}.",
        f"Dropped out: {len(dropped)}.",
        f"Not rechecked: {len(missed)}.",
        "",
        "## Dropped out",
        "",
    ]
    if not dropped:
        lines.append("None.")
        lines.append("")
    else:
        lines.append("| Project | Old date | Old signal |")
        lines.append("| --- | --- | --- |")
        for row in sorted(dropped, key=lambda item: item["project"]):
            lines.append(f"| {row['project']} | {row.get('old_date') or ''} | {row.get('old_type') or ''} |")
        lines.append("")
    if moved:
        lines.append("## Date or signal changed")
        lines.append("")
        lines.append("| Project | Old date | Old signal | New date | New signal |")
        lines.append("| --- | --- | --- | --- | --- |")
        for row in sorted(moved, key=lambda item: item["project"]):
            lines.append(
                f"| {row['project']} | {row.get('old_date') or ''} | {row.get('old_type') or ''} | {row.get('new_date') or ''} | {row.get('new_type') or ''} |"
            )
        lines.append("")
    if missed:
        lines.append("## Not rechecked")
        lines.append("")
        for row in sorted(missed, key=lambda item: item["project"]):
            lines.append(f"- {row['project']}: {row.get('error') or ''}")
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    redetect()
    sys.exit(0)
