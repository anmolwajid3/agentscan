"""Fresh reversal candidates for the agent experiment.

Step 1 collects repository names from the ADR path queries, then draws 1,500
with a fixed seed. Later steps do not use the AI-adoption window or the
five-ADR minimum. Builds are not run.

The Sourcegraph client is adr_pilot.discover._sourcegraph. Fork and archive
checks follow the GraphQL batch shape used by the library-swap screen.
Status wording is adr_pilot.status. Nothing under adr-feasibility/data is written.
"""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_ADR = _ROOT / "adr-feasibility"
if str(_ADR) not in sys.path:
    sys.path.insert(0, str(_ADR))

from adr_pilot.discover import _sourcegraph  # noqa: E402
from adr_pilot.eligibility import parse_dt  # noqa: E402
from adr_pilot.status import adr_identifier  # noqa: E402

from pair_rules import (  # noqa: E402
    build_files_from_names,
    choose_best_commit,
    filename_has_number,
    first_paragraph,
    has_status_section,
    is_adr_path,
    is_application_path,
    is_foreign_copy,
    is_general_folder_path,
    is_template_file,
    pairs_in_repo,
    title_of,
)

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
REPO_CACHE = CACHE / "repos"
REPO_CACHE_V2 = CACHE / "repos_v2"
LOG = HERE / "run.log"
CLONE_ROOT = Path("/tmp/fresh-reversals")
SAMPLE_SEED = 20261114
REVIEW_SEED = 20261114
CAP = 1500
WINDOW_DAYS = 180
NEW_QUERIES = {
    "src_adr": r"context:global file:src/adr/.*\.md$ select:repo count:3000",
    "docs_arch_decisions_hyphen": r"context:global file:docs/architecture-decisions/.*\.md$ select:repo count:3000",
    "docs_architecture_adr": r"context:global file:docs/architecture/adr/.*\.md$ select:repo count:3000",
    "docs_architecture_adrs": r"context:global file:docs/architecture/adrs/.*\.md$ select:repo count:2000",
    "docs_architecture_decisions": r"context:global file:docs/architecture/decisions/.*\.md$ select:repo count:3000",
    "doc_arch_decisions": r"context:global file:doc/architecture/decisions/.*\.md$ select:repo count:3000",
    "doc_arch_decisions_hyphen": r"context:global file:doc/architecture-decisions/.*\.md$ select:repo count:2000",
    "doc_arch": r"context:global file:doc/arch/.*\.md$ select:repo count:2000",
    "documentation_arch_decisions": r"context:global file:documentation/architecture/decisions/.*\.md$ select:repo count:2000",
    "source_adr_records": r"context:global file:source/architecture_decision_records/.*\.md$ select:repo count:1000",
    "docs_architecture": r"context:global file:docs/architecture/.*\.md$ select:repo count:4000",
}
CSV_FIELDS_V2 = [
    "project",
    "language",
    "build_tool",
    "old_adr",
    "new_adr",
    "supersede_wording",
    "adr_date",
    "commit_found",
    "best_commit",
    "best_commit_title",
    "best_commit_why",
    "best_commit_timing",
    "other_candidates",
    "matched_keywords",
    "confidence",
    "partial",
    "duplicate_of",
    "adr_count",
    "first_adr_date",
    "in_old_133",
    "in_v1",
    "notes",
]
KNOWN_CASES = [
    (
        "SukramJ/aiohomematic",
        "docs/adr/0004-thread-based-xml-rpc-server.md",
        "docs/adr/0012-async-xml-rpc-server-poc.md",
        ("57d79e74d2", "34d1218731"),
    ),
    (
        "chrisbanes/haze",
        "docs/adr/0002-use-a-shared-retained-stage-graph-for-glass.md",
        "docs/adr/0003-use-one-android-fused-glass-renderer.md",
        ("d3384f5611",),
    ),
    (
        "alphagov/whitehall",
        "docs/adr/0005-use-json-schema-for-flexible-page-schemas.md",
        "docs/adr/0008-drop-json-schema-for-document-configuration.md",
        (),
    ),
]
QUERIES = {
    "docs_adr": r"context:global file:docs/adr/.*\.md$ select:repo count:5000",
    "doc_adr": r"context:global file:doc/adr/.*\.md$ select:repo count:5000",
    "docs_decisions": r"context:global file:docs/decisions/.*\.md$ select:repo count:5000",
    "arch_decisions": r"context:global file:architecture/decisions/.*\.md$ select:repo count:4000",
    "doc_arch_decisions": r"context:global file:doc/architecture/decisions/.*\.md$ select:repo count:3000",
    "adr_root": r"context:global file:^adr/[0-9].*\.md$ select:repo count:5000",
    "docs_adrs": r"context:global file:docs/adrs/.*\.md$ select:repo count:3000",
}
CSV_FIELDS = [
    "project",
    "language",
    "build_tool",
    "old_adr",
    "new_adr",
    "supersede_wording",
    "adr_date",
    "commit_found",
    "method",
    "implementing_commits",
    "commit_timing",
    "matched_keywords",
    "confidence",
    "in_old_133",
    "notes",
]


def log(message: str) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    line = message.rstrip() + "\n"
    with LOG.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.write(line)
        handle.flush()
        fcntl.flock(handle, fcntl.LOCK_UN)
    print(line, end="", flush=True)


def token() -> str:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def git_env() -> dict:
    # Public clones work without a header. A bearer header on the git URL makes
    # GitHub reject the clone and git then asks for a username.
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_cmd(args: list[str], timeout: int, cwd: str | None = None) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=git_env(),
            check=False,
        )
        code = result.returncode
        shown = " ".join(args[:8])
        log(f"exit {code} {shown}")
        return result
    except subprocess.TimeoutExpired:
        log(f"exit timeout {' '.join(args[:8])}")
        raise


def graphql(query: str) -> dict:
    body = json.dumps({"query": query}).encode("utf-8")
    key = token()
    last = ""
    for attempt in range(6):
        request = urllib.request.Request(
            "https://api.github.com/graphql",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": "fresh-reversals",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                log(f"exit {response.status} graphql")
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = exc.read().decode("utf-8", "replace")[:240]
            log(f"exit {exc.code} graphql")
            if exc.code in {403, 429, 502, 503}:
                time.sleep(min(90, 5 * (2 ** attempt)))
                continue
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            log(f"exit error graphql {type(exc).__name__}")
            time.sleep(min(60, 2 * (2 ** attempt)))
    return {"errors": [{"message": last or "graphql failed"}]}


def rest(url: str, accept: str = "application/vnd.github+json") -> tuple[int, object]:
    key = token()
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": "fresh-reversals",
            "Accept": accept,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            log(f"exit {response.status} GET {url.split('?', 1)[0]}")
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        log(f"exit {exc.code} GET {url.split('?', 1)[0]}")
        if exc.code in {403, 429}:
            time.sleep(20)
        return exc.code, {}
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        log(f"exit error GET {type(exc).__name__}")
        return 0, {}


def step1() -> tuple[list[str], dict]:
    saved = CACHE / "candidates.json"
    if saved.exists():
        payload = json.loads(saved.read_text(encoding="utf-8"))
        return payload["names"], payload["queries"]
    found: dict[str, list[str]] = {}
    query_stats = {}
    for name, query in QUERIES.items():
        try:
            repos, progress = _sourcegraph(query, timeout=180)
            code = 0
        except Exception as exc:  # noqa: BLE001
            repos, progress = [], None
            code = 1
            log(f"sourcegraph {name} failed: {exc}")
        log(f"exit {code} sourcegraph {name}")
        match_count = None
        if isinstance(progress, dict):
            match_count = progress.get("matchCount")
        query_stats[name] = {"returned": len(repos), "match_count": match_count}
        log(f"sourcegraph {name}: returned {len(repos)} reported {match_count}")
        for repo in repos:
            full = repo.get("repository") or ""
            if not full.startswith("github.com/"):
                continue
            short = full.split("github.com/", 1)[1]
            if "/" not in short:
                continue
            found.setdefault(short, [])
            if name not in found[short]:
                found[short].append(name)
    names = sorted(found)
    CACHE.mkdir(parents=True, exist_ok=True)
    saved.write_text(json.dumps({"names": names, "queries": query_stats, "sources": found}), encoding="utf-8")
    return names, query_stats


def draw(names: list[str]) -> list[str]:
    saved = CACHE / "sample.json"
    if saved.exists():
        return json.loads(saved.read_text(encoding="utf-8"))["sample"]
    ordered = sorted(names)
    rng = random.Random(SAMPLE_SEED)
    rng.shuffle(ordered)
    sample = ordered[:CAP]
    saved.write_text(
        json.dumps({"seed": SAMPLE_SEED, "cap": CAP, "universe": len(names), "sample": sample}),
        encoding="utf-8",
    )
    return sample


def step1_v2() -> dict:
    """Keep the v1 draw and add repositories found only by the extra folder queries."""
    saved = CACHE / "candidates_v2.json"
    if saved.exists():
        return json.loads(saved.read_text(encoding="utf-8"))
    v1_names = json.loads((CACHE / "candidates.json").read_text(encoding="utf-8"))["names"]
    v1_sample = json.loads((CACHE / "sample.json").read_text(encoding="utf-8"))["sample"]
    found: dict[str, list[str]] = {}
    query_stats = {}
    for name, query in NEW_QUERIES.items():
        try:
            repos, progress = _sourcegraph(query, timeout=180)
            code = 0
        except Exception as exc:  # noqa: BLE001
            repos, progress = [], None
            code = 1
            log(f"sourcegraph {name} failed: {exc}")
        log(f"exit {code} sourcegraph {name}")
        match_count = progress.get("matchCount") if isinstance(progress, dict) else None
        query_stats[name] = {"returned": len(repos), "match_count": match_count}
        log(f"sourcegraph {name}: returned {len(repos)} reported {match_count}")
        for repo in repos:
            full = repo.get("repository") or ""
            if not full.startswith("github.com/"):
                continue
            short = full.split("github.com/", 1)[1]
            if "/" not in short:
                continue
            found.setdefault(short, [])
            if name not in found[short]:
                found[short].append(name)
    new_names = sorted(set(found) - set(v1_names))
    rng = random.Random(SAMPLE_SEED)
    rng.shuffle(new_names)
    sample = list(v1_sample) + new_names
    payload = {
        "seed": SAMPLE_SEED,
        "v1_universe": len(v1_names),
        "v1_sample": len(v1_sample),
        "new_repositories": len(new_names),
        "new_names": new_names,
        "sample": sample,
        "queries": query_stats,
    }
    saved.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def _tree_names(tree: dict | None, prefix: str = "") -> list[str]:
    names: list[str] = []
    for entry in (tree or {}).get("entries") or []:
        name = entry.get("name") or ""
        if not name or name in {".git", "node_modules", "vendor"}:
            continue
        rel = f"{prefix}{name}" if not prefix else f"{prefix}/{name}"
        kind = entry.get("type")
        if kind == "blob":
            names.append(rel)
        elif kind == "tree" and prefix == "":
            child = entry.get("object") or {}
            for nested in child.get("entries") or []:
                if nested.get("type") == "blob":
                    names.append(f"{name}/{nested.get('name') or ''}")
    return names


def screen(sample: list[str]) -> dict[str, dict]:
    done: dict[str, dict] = {}
    path = CACHE / "screen.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if isinstance(row, dict) and row.get("project"):
                    done[row["project"]] = row
    pending = [name for name in sample if name not in done]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for start in range(0, len(pending), 3):
            batch = pending[start : start + 3]
            rows = _screen_batch(batch)
            remaining = rows.pop("__rate__", None)
            for name, row in rows.items():
                done[name] = row
                handle.write(json.dumps(row) + "\n")
            handle.flush()
            if start % 60 == 0:
                log(f"screened {min(start + 3, len(pending))}/{len(pending)}")
            if isinstance(remaining, dict) and int(remaining.get("remaining") or 9999) < 80:
                reset = remaining.get("resetAt") or ""
                log(f"rate limit remaining {remaining.get('remaining')} reset {reset}")
                time.sleep(30)
    return {name: done[name] for name in sample if name in done and "project" in done[name]}


def _screen_batch(batch: list[str]) -> dict[str, dict]:
    fields = ["rateLimit { remaining resetAt cost }"]
    for index, name in enumerate(batch):
        owner, repo = name.split("/", 1)
        fields.append(
            f"""
            r{index}: repository(owner: {json.dumps(owner)}, name: {json.dumps(repo)}) {{
              isFork
              isArchived
              defaultBranchRef {{
                name
                target {{
                  ... on Commit {{
                    tree {{
                      entries {{
                        name
                        type
                        object {{
                          ... on Tree {{
                            entries {{ name type }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """
        )
    payload = graphql("query {\n" + "\n".join(fields) + "\n}")
    if payload.get("data") is None and len(batch) > 1:
        rows = {}
        for name in batch:
            rows.update(_screen_batch([name]))
        return rows
    data = payload.get("data") or {}
    rows: dict[str, dict] = {}
    rate = data.get("rateLimit") or {}
    if rate:
        rows["__rate__"] = rate
    errors = payload.get("errors") or []
    for index, name in enumerate(batch):
        repo = data.get(f"r{index}")
        if not repo:
            message = ""
            for error in errors:
                path = error.get("path") or []
                if path and path[0] == f"r{index}":
                    message = error.get("message") or ""
            rows[name] = {
                "project": name,
                "keep": False,
                "reason": "api error",
                "detail": message[:200] or "repository not returned",
                "language": "",
                "build_tool": "",
            }
            log(f"skipped {name} api error")
            continue
        if repo.get("isFork"):
            rows[name] = {"project": name, "keep": False, "reason": "fork", "detail": "", "language": "", "build_tool": ""}
            continue
        if repo.get("isArchived"):
            rows[name] = {"project": name, "keep": False, "reason": "archived", "detail": "", "language": "", "build_tool": ""}
            continue
        names = _tree_names(((repo.get("defaultBranchRef") or {}).get("target") or {}).get("tree"))
        language, tool = build_files_from_names(names)
        if not tool:
            rows[name] = {"project": name, "keep": False, "reason": "no build file", "detail": "", "language": "", "build_tool": ""}
            continue
        rows[name] = {
            "project": name,
            "keep": True,
            "reason": "",
            "detail": "",
            "language": language,
            "build_tool": tool,
        }
    return rows


class RepoTimeout(Exception):
    pass


def _alarm(signum, frame):  # noqa: ARG001
    raise RepoTimeout()


def _kill_children(pid: int) -> None:
    proc = Path("/proc")
    if not proc.exists():
        return
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            text = (entry / "stat").read_text(encoding="utf-8")
        except OSError:
            continue
        tail = text.rsplit(")", 1)[-1].split()
        if len(tail) >= 2 and tail[1] == str(pid):
            child = int(entry.name)
            _kill_children(child)
            try:
                os.kill(child, signal.SIGKILL)
            except OSError:
                pass


def process_repo(row: dict) -> dict:
    name = row["project"]
    dest = CLONE_ROOT / name.replace("/", "__")
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(900)
    try:
        return _process_repo(row, dest)
    except RepoTimeout:
        _kill_children(os.getpid())
        log(f"exit timeout repo {name}")
        return {"project": name, "error": "timeout", "pairs": [], "adr_count": 0, "links_rejected": 0, "unresolved": 0}
    except Exception as exc:  # noqa: BLE001
        log(f"exit error repo {name} {type(exc).__name__}")
        return {"project": name, "error": str(exc)[:200], "pairs": [], "adr_count": 0, "links_rejected": 0, "unresolved": 0}
    finally:
        signal.alarm(0)
        shutil.rmtree(dest, ignore_errors=True)


def _empty_repo(name: str, error: str, **extra: object) -> dict:
    payload = {
        "project": name,
        "error": error,
        "pairs": [],
        "adr_count": 0,
        "links_rejected": 0,
        "unresolved": 0,
        "general_removed": 0,
        "copied_pairs": 0,
        "template_pairs": 0,
        "first_adr_date": "",
    }
    payload.update(extra)
    return payload


def _process_repo(row: dict, dest: Path) -> dict:
    name = row["project"]
    shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cloned = None
    for attempt in range(3):
        shutil.rmtree(dest, ignore_errors=True)
        cloned = run_cmd(
            ["git", "clone", "--filter=blob:none", "--no-checkout", "--single-branch", f"https://github.com/{name}.git", str(dest)],
            timeout=180,
        )
        if cloned.returncode == 0 and (dest / ".git").exists():
            break
        err = (cloned.stderr or "").lower()
        if attempt < 2 and any(bit in err for bit in ("could not resolve", "timed out", "timeout", "429", "503", "connection")):
            time.sleep(5 * (attempt + 1))
            continue
        break
    if cloned is None or cloned.returncode != 0 or not (dest / ".git").exists():
        detail = (cloned.stderr or "clone failed")[-200:]
        return _empty_repo(name, detail)
    listed = run_cmd(["git", "-C", str(dest), "ls-tree", "-r", "--name-only", "HEAD"], timeout=90)
    if listed.returncode != 0:
        return _empty_repo(name, "ls-tree failed")
    candidates = [line for line in listed.stdout.splitlines() if is_adr_path(line)]
    records = []
    general_removed = 0
    for path in candidates:
        blob = run_cmd(["git", "-C", str(dest), "cat-file", "blob", f"HEAD:{path}"], timeout=60)
        if blob.returncode != 0:
            continue
        text = blob.stdout
        if is_general_folder_path(path) and not (filename_has_number(path) or has_status_section(text)):
            general_removed += 1
            continue
        records.append({"path": path, "text": text})
    found, rejected, unresolved = pairs_in_repo(records, name)
    copied_pairs = 0
    template_pairs = 0
    kept_pairs = []
    for pair in found:
        old_text = pair.get("old_text") or ""
        new_text = pair.get("new_text") or ""
        if is_foreign_copy(pair["old_adr"], old_text, name) or is_foreign_copy(pair["new_adr"], new_text, name):
            copied_pairs += 1
            continue
        if is_template_file(pair["old_adr"], old_text) or is_template_file(pair["new_adr"], new_text):
            template_pairs += 1
            continue
        kept_pairs.append(pair)
    kept_files = [
        record["path"]
        for record in records
        if not is_foreign_copy(record["path"], record.get("text") or "", name)
    ]
    first_date = _first_adr_date(dest, kept_files)
    pairs = []
    for pair in kept_pairs:
        searched = _search_pair(dest, name, pair)
        searched["adr_count"] = len(kept_files)
        searched["first_adr_date"] = first_date
        pairs.append(searched)
    return {
        "project": name,
        "error": "",
        "pairs": pairs,
        "adr_count": len(kept_files),
        "links_rejected": rejected,
        "unresolved": unresolved,
        "general_removed": general_removed,
        "copied_pairs": copied_pairs,
        "template_pairs": template_pairs,
        "first_adr_date": first_date,
        "language": row.get("language") or "",
        "build_tool": row.get("build_tool") or "",
    }


def _first_adr_date(dest: Path, paths: list[str]) -> str:
    """Author date of the oldest commit that touches any kept ADR file.

    `git log -1 --reverse` applies the limit before reversing, so it returns the
    newest commit. `rev-list --reverse` prints the oldest first.
    """
    earliest = ""
    for start in range(0, len(paths), 80):
        chunk = paths[start : start + 80]
        listed = run_cmd(["git", "-C", str(dest), "rev-list", "--reverse", "HEAD", "--", *chunk], timeout=120)
        sha = ((listed.stdout or "").strip().splitlines() or [""])[0]
        if not sha:
            continue
        shown = run_cmd(["git", "-C", str(dest), "log", "-1", "--format=%aI", sha], timeout=30)
        stamp = (shown.stdout or "").strip().splitlines()[0] if (shown.stdout or "").strip() else ""
        if stamp and (not earliest or stamp < earliest):
            earliest = stamp
    return earliest


def _kept_adr_paths(dest: Path, project: str) -> list[str]:
    listed = run_cmd(["git", "-C", str(dest), "ls-tree", "-r", "--name-only", "HEAD"], timeout=90)
    if listed.returncode != 0:
        return []
    kept = []
    for path in listed.stdout.splitlines():
        if not is_adr_path(path):
            continue
        blob = run_cmd(["git", "-C", str(dest), "cat-file", "blob", f"HEAD:{path}"], timeout=60)
        if blob.returncode != 0:
            continue
        text = blob.stdout
        if is_general_folder_path(path) and not (filename_has_number(path) or has_status_section(text)):
            continue
        if is_foreign_copy(path, text, project):
            continue
        kept.append(path)
    return kept


def refresh_one_date(project: str) -> dict:
    dest = CLONE_ROOT / ("date_" + project.replace("/", "__"))
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(600)
    try:
        shutil.rmtree(dest, ignore_errors=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        cloned = run_cmd(
            ["git", "clone", "--filter=blob:none", "--no-checkout", "--single-branch", f"https://github.com/{project}.git", str(dest)],
            timeout=180,
        )
        if cloned.returncode != 0 or not (dest / ".git").exists():
            return {"project": project, "first_adr_date": "", "error": "clone failed"}
        paths = _kept_adr_paths(dest, project)
        return {"project": project, "first_adr_date": _first_adr_date(dest, paths), "error": ""}
    except RepoTimeout:
        _kill_children(os.getpid())
        return {"project": project, "first_adr_date": "", "error": "timeout"}
    except Exception as exc:  # noqa: BLE001
        return {"project": project, "first_adr_date": "", "error": str(exc)[:160]}
    finally:
        signal.alarm(0)
        shutil.rmtree(dest, ignore_errors=True)


def refresh_first_dates() -> None:
    """Fill first_adr_date from the oldest ADR commit. Leaves every other column as it is."""
    projects = []
    for path in sorted(REPO_CACHE_V2.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("pairs"):
            projects.append(data["project"])
    log(f"refresh first_adr_date for {len(projects)}")
    found: dict[str, str] = {}
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(refresh_one_date, project): project for project in projects}
        done = 0
        for future in as_completed(futures):
            done += 1
            project = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {"project": project, "first_adr_date": "", "error": str(exc)[:160]}
            found[result["project"]] = result.get("first_adr_date") or ""
            if result.get("error"):
                log(f"date {done}/{len(projects)} {project} {result['error']}")
            elif done % 20 == 0 or done == len(projects):
                log(f"date {done}/{len(projects)} {project}")
    for path in REPO_CACHE_V2.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        project = data.get("project") or ""
        if project not in found:
            continue
        data["first_adr_date"] = found[project]
        for pair in data.get("pairs") or []:
            pair["first_adr_date"] = found[project]
        path.write_text(json.dumps(data), encoding="utf-8")
    csv_path = HERE / "fresh_reversals_v2.csv"
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0].keys()) if rows else CSV_FIELDS_V2
    for row in rows:
        if row["project"] in found:
            row["first_adr_date"] = found[row["project"]]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    blank = sum(1 for row in rows if row["project"] in found and not row["first_adr_date"])
    log(f"first_adr_date refreshed blank_rows {blank}")


def _oldest_add(dest: Path, path: str) -> dict | None:
    result = run_cmd(
        ["git", "-C", str(dest), "log", "--follow", "--diff-filter=A", "--format=%H%x1f%aI%x1f%s", "--", path],
        timeout=60,
    )
    lines = [line for line in (result.stdout or "").splitlines() if "\x1f" in line]
    if not lines:
        result = run_cmd(
            ["git", "-C", str(dest), "log", "--follow", "--format=%H%x1f%aI%x1f%s", "--", path],
            timeout=60,
        )
        lines = [line for line in (result.stdout or "").splitlines() if "\x1f" in line]
    if not lines:
        return None
    sha, when, subject = lines[-1].split("\x1f", 2)
    return {"sha": sha, "date": when, "subject": subject}


def _files_of(dest: Path, sha: str) -> list[str]:
    result = run_cmd(
        ["git", "-C", str(dest), "diff-tree", "--no-commit-id", "--name-status", "-r", "-M", sha],
        timeout=40,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _message_of(dest: Path, sha: str) -> str:
    result = run_cmd(["git", "-C", str(dest), "log", "-1", "--format=%B", sha], timeout=30)
    return (result.stdout or "").strip()[:800]


def _window_commits(dest: Path, start: datetime, end: datetime) -> list[dict]:
    # Git's --since uses the committer date. The padded range is filtered on the author date below.
    padded_start = (start - timedelta(days=30)).strftime("%Y-%m-%d")
    padded_end = (end + timedelta(days=2)).strftime("%Y-%m-%d")
    result = run_cmd(
        [
            "git", "-C", str(dest), "log",
            f"--since={padded_start}", f"--until={padded_end}",
            "--name-status", "--pretty=format:COMMIT%x1f%H%x1f%aI%x1f%s%x1e",
        ],
        timeout=150,
    )
    if result.returncode != 0:
        return []
    commits = []
    current = None
    files: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("COMMIT\x1f"):
            if current is not None:
                current["files"] = files
                commits.append(current)
            parts = line[len("COMMIT\x1f"):].split("\x1f")
            subject = parts[2] if len(parts) > 2 else ""
            subject = subject.split("\x1e", 1)[0]
            current = {"sha": parts[0], "date": parts[1] if len(parts) > 1 else "", "subject": subject}
            files = []
            continue
        if current is None or not line.strip() or line.startswith("\x1e"):
            continue
        files.append(line.strip())
    if current is not None:
        current["files"] = files
        commits.append(current)
    kept = []
    for commit in commits:
        when = parse_dt(commit.get("date"))
        if when is not None and start <= when <= end:
            kept.append(commit)
    return kept


def _timing(when: datetime | None, adr: datetime) -> str:
    if when is None:
        return "unknown"
    if when < adr:
        return "before"
    if when > adr:
        return "after"
    return "same"


def _same_pr(project: str, sha: str, dest: Path, adr: datetime, start: datetime, end: datetime) -> list[dict]:
    code, payload = rest(f"https://api.github.com/repos/{project}/commits/{sha}/pulls")
    if code != 200 or not isinstance(payload, list) or not payload:
        return []
    number = payload[0].get("number")
    if not number:
        return []
    status, commits = rest(f"https://api.github.com/repos/{project}/pulls/{number}/commits?per_page=50")
    if status != 200 or not isinstance(commits, list):
        return []
    hits = []
    for commit in commits:
        info = commit.get("commit") or {}
        author = (info.get("author") or {}).get("date") or ""
        when = parse_dt(author)
        if when is None or not (start <= when <= end):
            continue
        other = commit.get("sha") or ""
        if not other or other == sha:
            continue
        files = _files_of(dest, other)
        if any(is_application_path(path) for path in files):
            hits.append(
                {
                    "sha": other,
                    "date": author,
                    "timing": _timing(when, adr),
                    "subject": (info.get("message") or "").splitlines()[0][:200],
                    "message": (info.get("message") or "")[:800],
                    "files": files[:40],
                    "method": "a",
                }
            )
    return hits


def _content_key(old_text: str, new_text: str) -> str:
    def norm(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    blob = norm(old_text) + "\n" + norm(new_text)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def _rest_retry(url: str) -> tuple[int, object]:
    code, payload = 0, {}
    for attempt in range(4):
        code, payload = rest(url)
        if code not in {0, 403, 429, 502, 503}:
            return code, payload
        time.sleep(15 * (attempt + 1))
    return code, payload


def _pr_commits(project: str, sha: str, dest: Path, start: datetime, end: datetime) -> list[dict]:
    """Commits on the pull request that added the ADR, with the PR title available for ranking."""
    code, payload = _rest_retry(f"https://api.github.com/repos/{project}/commits/{sha}/pulls")
    if code != 200 or not isinstance(payload, list) or not payload:
        return []
    title = (payload[0].get("title") or "").strip()
    number = payload[0].get("number")
    if not number:
        return []
    status, commits = _rest_retry(f"https://api.github.com/repos/{project}/pulls/{number}/commits?per_page=20")
    if status != 200 or not isinstance(commits, list):
        return []
    extras = []
    for commit in commits[:15]:
        info = commit.get("commit") or {}
        author = (info.get("author") or {}).get("date") or ""
        when = parse_dt(author)
        if when is None or not (start <= when <= end):
            continue
        other = commit.get("sha") or ""
        if not other:
            continue
        subject = ((info.get("message") or "").splitlines() or [""])[0][:180]
        if title and title.lower() not in subject.lower():
            subject = f"{title}. {subject}"[:240]
        extras.append(
            {
                "sha": other,
                "date": author,
                "subject": subject,
                "files": _files_of(dest, other),
            }
        )
    return extras


def _apply_best(base: dict, best: dict, adr: datetime) -> None:
    commit = best["commit"]
    when = parse_dt(commit.get("date"))
    timing = _timing(when, adr)
    base["commit_found"] = "yes"
    base["best_commit"] = commit.get("sha") or ""
    base["best_commit_title"] = (commit.get("subject") or "")[:200]
    base["best_commit_why"] = best.get("why") or ""
    base["best_commit_timing"] = timing
    base["commit_timing"] = timing
    base["confidence"] = best.get("confidence") or ""
    base["matched_keywords"] = ",".join(best.get("keywords") or [])
    others = best.get("others") or []
    base["other_candidates"] = "; ".join(
        f"{(item.get('sha') or '')[:12]} {(item.get('subject') or '')[:80]}" for item in others
    )
    shown_files = []
    for raw in (commit.get("files") or [])[:25]:
        shown_files.append(raw.replace("\t", " "))
    base["details"] = [
        {
            "sha": commit.get("sha") or "",
            "timing": timing,
            "message": commit.get("subject") or "",
            "files": shown_files,
            "why": best.get("why") or "",
        }
    ]


def _search_pair(dest: Path, project: str, pair: dict) -> dict:
    added = _oldest_add(dest, pair["new_adr"])
    new_text = pair.get("new_text") or ""
    old_text = pair.get("old_text") or ""
    base = {
        "old_adr": pair["old_adr"],
        "new_adr": pair["new_adr"],
        "supersede_wording": pair.get("supersede_wording") or "",
        "old_status": pair.get("old_status") or "",
        "new_title": title_of(new_text),
        "new_paragraph": first_paragraph(new_text),
        "adr_date": "",
        "commit_found": "no",
        "best_commit": "",
        "best_commit_title": "",
        "best_commit_why": "",
        "best_commit_timing": "",
        "other_candidates": "",
        "commit_timing": "",
        "matched_keywords": "",
        "confidence": "",
        "partial": pair.get("partial") or "no",
        "duplicate_of": "",
        "content_key": _content_key(old_text, new_text),
        "notes": "",
        "details": [],
    }
    if not added:
        base["notes"] = "new ADR commit not found"
        return base
    adr = parse_dt(added["date"])
    if adr is None:
        base["notes"] = "new ADR date not readable"
        return base
    base["adr_date"] = added["date"]
    start = adr - timedelta(days=WINDOW_DAYS)
    end = adr + timedelta(days=WINDOW_DAYS)
    try:
        commits = _window_commits(dest, start, end)
    except subprocess.TimeoutExpired:
        base["notes"] = "git log timed out"
        return base
    add_files = _files_of(dest, added["sha"])
    by_sha = {commit["sha"]: commit for commit in commits}
    if added["sha"] in by_sha:
        if add_files:
            by_sha[added["sha"]]["files"] = add_files
        if not by_sha[added["sha"]].get("subject"):
            by_sha[added["sha"]]["subject"] = added["subject"]
    else:
        commits.append({"sha": added["sha"], "date": added["date"], "subject": added["subject"], "files": add_files})
    number = adr_identifier(pair["new_adr"])
    best = choose_best_commit(commits, base["new_title"], old_text, new_text, number)
    if best is None or "matches the new ADR" not in (best.get("why") or ""):
        extras = _pr_commits(project, added["sha"], dest, start, end)
        if extras:
            again = choose_best_commit(commits + extras, base["new_title"], old_text, new_text, number)
            if again is not None and (best is None or again.get("score", 0) > best.get("score", 0)):
                best = again
    if best is None:
        base["notes"] = "no implementing commit in the 180-day window"
        return base
    _apply_best(base, best, adr)
    return base


def old_133() -> dict[tuple[str, str], str]:
    """Reconstruct the previous 133 from the saved measurements. Read only."""
    keys: dict[tuple[str, str], str] = {}
    folder = _ADR / "data" / "repos"
    for path in sorted(folder.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not data.get("clone_ok") or data.get("likely_template"):
            continue
        group = data.get("group")
        signal = parse_dt(data.get("signal_date"))
        repo = data.get("repo") or ""
        for adr in data.get("adrs") or []:
            if adr.get("status") != "superseded":
                continue
            written = parse_dt(adr.get("first_commit"))
            keep = False
            if signal is None and group == "non-ai-eligible":
                keep = True
            elif signal is not None and group == "ai-eligible" and written is not None and written < signal:
                keep = True
            if keep and repo and adr.get("path"):
                keys[(repo, adr["path"])] = repo
    return keys


def write_outputs(results: list[dict], screen_rows: dict[str, dict], universe: list[str], sample: list[str], queries: dict, old: dict) -> None:
    pairs = []
    for result in results:
        row = screen_rows.get(result["project"], {})
        for pair in result.get("pairs") or []:
            key = (result["project"], pair.get("old_adr") or "")
            pair = dict(pair)
            pair["project"] = result["project"]
            pair["language"] = result.get("language") or row.get("language") or ""
            pair["build_tool"] = result.get("build_tool") or row.get("build_tool") or ""
            pair["in_old_133"] = "yes" if key in old else "no"
            pairs.append(pair)
    with (HERE / "fresh_reversals.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for pair in pairs:
            writer.writerow({key: pair.get(key, "") for key in CSV_FIELDS})
    _review(pairs)
    _funnel(results, screen_rows, universe, sample, queries, old, pairs)
    log(f"wrote {len(pairs)} pairs")


def _review(pairs: list[dict]) -> None:
    folder = HERE / "review"
    folder.mkdir(parents=True, exist_ok=True)
    for child in folder.glob("*.md"):
        child.unlink()
    rng = random.Random(REVIEW_SEED)
    written = 0
    for confidence in ("high", "medium", "low"):
        pool = [pair for pair in pairs if pair.get("confidence") == confidence and pair.get("commit_found") == "yes"]
        rng.shuffle(pool)
        chosen = pool[:5]
        for index, pair in enumerate(chosen, start=1):
            written += 1
            slug = re.sub(r"[^A-Za-z0-9._-]+", "-", pair["project"])[:40]
            path = folder / f"{confidence}-{index}-{slug}.md"
            lines = [
                f"# {pair['project']} ({confidence})",
                "",
                f"Old ADR: `{pair.get('old_adr')}`",
                f"New ADR: `{pair.get('new_adr')}`",
                "",
                "## Old ADR status line",
                "",
                pair.get("old_status") or pair.get("supersede_wording") or "",
                "",
                "## New ADR",
                "",
                pair.get("new_title") or "",
                "",
                pair.get("new_paragraph") or "",
                "",
                "## Commits",
                "",
            ]
            details = pair.get("details") or []
            if not details:
                lines.append("No commit detail was kept.")
            for item in details:
                lines.append(f"### {item.get('sha')} ({item.get('timing')})")
                lines.append("")
                lines.append(item.get("message") or "")
                lines.append("")
                lines.append("Changed files:")
                lines.append("")
                for changed in item.get("files") or []:
                    lines.append(f"- {changed}")
                lines.append("")
            path.write_text("\n".join(lines), encoding="utf-8")
        log(f"review {confidence}: {len(chosen)} of {len(pool)}")
    log(f"review packets {written} seed {REVIEW_SEED}")


def _funnel(results, screen_rows, universe, sample, queries, old, pairs) -> None:
    reasons: dict[str, int] = {}
    for row in screen_rows.values():
        if not row.get("keep"):
            reasons[row.get("reason") or "unknown"] = reasons.get(row.get("reason") or "unknown", 0) + 1
    kept = [row for row in screen_rows.values() if row.get("keep")]
    clone_failed = [row for row in results if row.get("error") and not row.get("pairs")]
    two_adrs = sum(1 for row in results if int(row.get("adr_count") or 0) >= 2)
    rejected = sum(int(row.get("links_rejected") or 0) for row in results)
    unresolved = sum(int(row.get("unresolved") or 0) for row in results)
    by_conf = {"high": 0, "medium": 0, "low": 0, "": 0}
    loss: dict[str, int] = {}
    for pair in pairs:
        by_conf[pair.get("confidence") or ""] = by_conf.get(pair.get("confidence") or "", 0) + 1
        if pair.get("commit_found") != "yes":
            note = pair.get("notes") or "no commit"
            loss[note] = loss.get(note, 0) + 1
    found_keys = {(pair["project"], pair.get("old_adr") or "") for pair in pairs}
    missing: dict[str, list[str]] = {}
    universe_set = set(universe)
    sample_set = set(sample)
    screen_by = screen_rows
    processed = {row["project"]: row for row in results}
    for (repo, path), _repo in sorted(old.items()):
        if (repo, path) in found_keys:
            continue
        if repo not in universe_set:
            reason = "repository was not returned by the path queries"
        elif repo not in sample_set:
            reason = "outside the 1500 draw"
        elif repo not in screen_by:
            reason = "not screened"
        elif not screen_by[repo].get("keep"):
            reason = screen_by[repo].get("reason") or "filtered"
        elif repo not in processed:
            reason = "not processed"
        elif processed[repo].get("error"):
            reason = "clone or read failed"
        else:
            reason = "no resolvable newer ADR under the link rule"
        missing.setdefault(reason, []).append(f"{repo} `{path}`")
    in_old = sum(1 for pair in pairs if pair.get("in_old_133") == "yes")
    lines = [
        "# Fresh reversal funnel (interim)",
        "",
        "Interim. No builds were run. This is not a pass or fail.",
        "",
        f"Sample seed: {SAMPLE_SEED}. Review seed: {REVIEW_SEED}. Cap: {CAP}.",
        "The 1,500 repositories were drawn at random from the path-query names after sorting, not in the order Sourcegraph returned them.",
        "The implementing-commit window is 180 days before and 180 days after the new ADR's author date.",
        "",
        "## Step 1. ADR folders",
        "",
        f"Unique GitHub repositories from the path queries: {len(universe)}.",
        "",
    ]
    for name, stats in queries.items():
        lines.append(f"- {name}: returned {stats.get('returned')}, Sourcegraph matchCount {stats.get('match_count')}.")
    lines += [
        "",
        f"Drawn for the capped run: {len(sample)}.",
        "",
        "## Step 2. Not a fork, not archived, has a build file",
        "",
        f"Screened: {len(screen_rows)}.",
        f"Kept: {len(kept)}.",
        f"- fork: {reasons.get('fork', 0)}.",
        f"- archived: {reasons.get('archived', 0)}.",
        f"- no build file: {reasons.get('no build file', 0)}.",
        f"- api error: {reasons.get('api error', 0)}.",
    ]
    lines += [
        "",
        "## Step 3. Superseded pairs",
        "",
        f"Repositories whose clone or read failed: {len(clone_failed)}.",
        f"Repositories with at least two ADR files: {two_adrs}.",
        f"Markdown links to other ADRs rejected because they were ordinary cross-references: {rejected}.",
        f"Superseded wording whose newer ADR could not be resolved: {unresolved}.",
        f"Pairs written: {len(pairs)}.",
        "",
        "## Step 4. Implementing commits",
        "",
        f"High confidence: {by_conf.get('high', 0)}.",
        f"Medium confidence: {by_conf.get('medium', 0)}.",
        f"Low confidence: {by_conf.get('low', 0)}.",
        f"No commit found: {by_conf.get('', 0)}.",
        "",
        "Pairs lost at this step:",
        "",
    ]
    if not loss:
        lines.append("None.")
    for note, count in sorted(loss.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {count}: {note}")
    lines += [
        "",
        "## Step 5. Comparison with the old 133",
        "",
        f"Old superseded records reconstructed from the saved measurements: {len(old)}.",
        f"New pairs that were in that set: {in_old}.",
        f"Old records missing from the new pairs: {sum(len(items) for items in missing.values())}.",
        "",
    ]
    for reason, items in sorted(missing.items()):
        lines.append(f"### {reason} ({len(items)})")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    lines.append("Review packets are in `review/`. Five were requested at each confidence. A short band means fewer than five pairs had that confidence.")
    lines.append("")
    (HERE / "fresh_funnel.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not token():
        raise SystemExit("GITHUB_TOKEN is not set")
    CACHE.mkdir(parents=True, exist_ok=True)
    REPO_CACHE.mkdir(parents=True, exist_ok=True)
    log("start fresh reversals")
    universe, queries = step1()
    log(f"universe {len(universe)}")
    sample = draw(universe)
    log(f"sample {len(sample)} seed {SAMPLE_SEED}")
    screened = screen(sample)
    kept = [screened[name] for name in sample if screened.get(name, {}).get("keep")]
    log(f"kept {len(kept)}")
    results = []
    pending = []
    for row in kept:
        slug = row["project"].replace("/", "__")
        cached = REPO_CACHE / f"{slug}.json"
        if cached.exists():
            results.append(json.loads(cached.read_text(encoding="utf-8")))
        else:
            pending.append(row)
    log(f"clone pending {len(pending)} cached {len(results)}")
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(process_repo, row): row for row in pending}
        finished = 0
        for future in as_completed(futures):
            row = futures[future]
            finished += 1
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {"project": row["project"], "error": str(exc)[:200], "pairs": [], "adr_count": 0, "links_rejected": 0, "unresolved": 0}
            result["language"] = row.get("language") or ""
            result["build_tool"] = row.get("build_tool") or ""
            slug = row["project"].replace("/", "__")
            (REPO_CACHE / f"{slug}.json").write_text(json.dumps(result), encoding="utf-8")
            results.append(result)
            if finished % 10 == 0 or finished == len(pending):
                log(f"processed {finished}/{len(pending)} {row['project']}")
    old = old_133()
    log(f"old reconstructed {len(old)}")
    write_outputs(results, screened, universe, sample, queries, old)
    log("EXIT:0")


def _kept_pairs(pairs: list[dict]) -> list[dict]:
    return [pair for pair in pairs if not pair.get("duplicate_of")]


def _pair_year(pair: dict) -> str:
    when = parse_dt(pair.get("adr_date"))
    if when is None:
        return "unknown"
    if when.year < 2026:
        return "before 2026"
    if when.year == 2026:
        return "2026"
    return str(when.year)


def _mark_duplicates(pairs: list[dict]) -> None:
    groups: dict[str, list[dict]] = defaultdict(list)
    for pair in pairs:
        key = pair.get("content_key") or ""
        if key:
            groups[key].append(pair)
    for group in groups.values():
        projects = list(dict.fromkeys(pair["project"] for pair in group))
        if len(projects) < 2:
            continue
        meta = {project: _repo_meta(project) for project in projects}
        keep = _canonical_repo(projects, meta)
        for pair in group:
            if pair["project"] != keep:
                pair["duplicate_of"] = keep


def _repo_meta(project: str) -> dict:
    code, payload = _rest_retry(f"https://api.github.com/repos/{project}")
    if code != 200 or not isinstance(payload, dict):
        return {"created_at": "", "parent": ""}
    parent = ""
    parent_obj = payload.get("parent") or {}
    if isinstance(parent_obj, dict):
        parent = parent_obj.get("full_name") or ""
    return {"created_at": payload.get("created_at") or "", "parent": parent}


def _canonical_repo(projects: list[str], meta: dict[str, dict]) -> str:
    lowered = {project.lower(): project for project in projects}
    parents = []
    for project in projects:
        parent = (meta.get(project) or {}).get("parent") or ""
        if parent.lower() in lowered and parent.lower() != project.lower():
            parents.append(lowered[parent.lower()])
    if parents:
        return sorted(set(parents), key=lambda project: ((meta.get(project) or {}).get("created_at") or "9999", project.lower()))[0]
    return sorted(projects, key=lambda project: ((meta.get(project) or {}).get("created_at") or "9999", project.lower()))[0]


def _load_v1() -> list[dict]:
    path = HERE / "fresh_reversals.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _v1_survival(v1_rows: list[dict], pairs: list[dict]) -> dict:
    """Same project and the same two ADR files, in either order, counts as surviving."""
    by_paths: dict[tuple[str, tuple[str, str]], dict] = {}
    paths_by_project: dict[str, set[str]] = defaultdict(set)
    for pair in pairs:
        key = (pair["project"], tuple(sorted([pair.get("old_adr") or "", pair.get("new_adr") or ""])))
        by_paths.setdefault(key, pair)
        paths_by_project[pair["project"]].add(pair.get("old_adr") or "")
        paths_by_project[pair["project"]].add(pair.get("new_adr") or "")
    survive = flip = changed = dropped = 0
    for row in v1_rows:
        key = (row.get("project") or "", tuple(sorted([row.get("old_adr") or "", row.get("new_adr") or ""])))
        hit = by_paths.get(key)
        if hit is not None:
            survive += 1
            if (hit.get("old_adr") or "") != (row.get("old_adr") or "") or (hit.get("new_adr") or "") != (row.get("new_adr") or ""):
                flip += 1
            continue
        owned = paths_by_project.get(row.get("project") or "", set())
        if (row.get("old_adr") or "") in owned or (row.get("new_adr") or "") in owned:
            changed += 1
        else:
            dropped += 1
    return {"v1_rows": len(v1_rows), "survive": survive, "flip": flip, "changed_target": changed, "dropped": dropped}


def _known_lines(pairs: list[dict]) -> list[str]:
    lines = ["## Known-case check", ""]
    by_key = {
        (pair["project"], pair.get("old_adr") or "", pair.get("new_adr") or ""): pair
        for pair in pairs
    }
    for project, old, new, expected in KNOWN_CASES:
        pair = by_key.get((project, old, new))
        if pair is None:
            lines.append(f"- {project} `{old}` → `{new}`: not in the v2 pairs.")
            continue
        chosen = pair.get("best_commit") or ""
        hit = ""
        for prefix in expected:
            if chosen.startswith(prefix):
                hit = prefix
                break
        extra = f" It matches the expected prefix {hit}." if hit else ""
        if expected and not hit:
            extra = " It does not match the expected prefixes " + ", ".join(expected) + "."
        lines.append(
            f"- {project}: best commit `{chosen or 'none'}` ({pair.get('confidence') or 'no confidence'}). "
            f"Title: {pair.get('best_commit_title') or 'none'}. Why: {pair.get('best_commit_why') or pair.get('notes') or 'none'}.{extra}"
        )
    lines.append("")
    return lines


def _write_review_v2(pairs: list[dict]) -> None:
    folder = HERE / "review_v2"
    folder.mkdir(parents=True, exist_ok=True)
    for child in folder.glob("*.md"):
        child.unlink()
    rng = random.Random(REVIEW_SEED)
    chosen_keys: set[tuple[str, str, str]] = set()

    def take(pool: list[dict], count: int) -> list[dict]:
        rng.shuffle(pool)
        picked = []
        for pair in pool:
            key = (pair["project"], pair.get("old_adr") or "", pair.get("new_adr") or "")
            if key in chosen_keys:
                continue
            chosen_keys.add(key)
            picked.append(pair)
            if len(picked) >= count:
                break
        return picked

    bands = [
        ("high_topic", [pair for pair in pairs if pair.get("confidence") == "high_topic" and pair.get("commit_found") == "yes"], 5),
        ("high_cooccur", [pair for pair in pairs if pair.get("confidence") == "high_cooccur" and pair.get("commit_found") == "yes"], 5),
        ("medium", [pair for pair in pairs if pair.get("confidence") == "medium" and pair.get("commit_found") == "yes"], 5),
        ("before-2026", [pair for pair in pairs if _pair_year(pair) == "before 2026"], 5),
    ]
    written = 0
    for label, pool, count in bands:
        picked = take(pool, count)
        for index, pair in enumerate(picked, start=1):
            written += 1
            slug = re.sub(r"[^A-Za-z0-9._-]+", "-", pair["project"])[:40]
            path = folder / f"{label}-{index}-{slug}.md"
            lines = [
                f"# {pair['project']} ({label})",
                "",
                f"Old ADR: `{pair.get('old_adr')}`",
                f"New ADR: `{pair.get('new_adr')}`",
                f"New ADR date: {pair.get('adr_date') or ''}",
                f"Partial: {pair.get('partial') or 'no'}",
                "",
                "## Old ADR status line",
                "",
                pair.get("old_status") or pair.get("supersede_wording") or "",
                "",
                "## New ADR",
                "",
                pair.get("new_title") or "",
                "",
                pair.get("new_paragraph") or "",
                "",
                "## Best commit",
                "",
                f"`{pair.get('best_commit') or 'none'}` ({pair.get('best_commit_timing') or 'unknown'})",
                "",
                pair.get("best_commit_title") or "",
                "",
                pair.get("best_commit_why") or pair.get("notes") or "",
                "",
                "Changed files:",
                "",
            ]
            details = pair.get("details") or []
            files = (details[0].get("files") if details else None) or []
            if not files:
                lines.append("No file list was kept.")
            for changed in files:
                lines.append(f"- {changed}")
            lines += ["", "## Other candidates", "", pair.get("other_candidates") or "None.", ""]
            path.write_text("\n".join(lines), encoding="utf-8")
        log(f"review_v2 {label}: {len(picked)} of {len(pool)}")
    log(f"review_v2 packets {written} seed {REVIEW_SEED}")


def _confidence_lines(pairs: list[dict], year: str) -> list[str]:
    counts: dict[str, int] = {}
    for pair in pairs:
        if _pair_year(pair) != year:
            continue
        label = pair.get("confidence") or "no commit"
        counts[label] = counts.get(label, 0) + 1
    lines = [f"### Confidence, new ADR {year}", ""]
    if not counts:
        lines.append("None.")
        lines.append("")
        return lines
    for label in ("high_topic", "high_cooccur", "medium", "low", "no commit"):
        if label in counts:
            lines.append(f"- {label}: {counts.pop(label)}.")
    for label, count in sorted(counts.items()):
        lines.append(f"- {label}: {count}.")
    lines.append("")
    return lines


def write_v2(results: list[dict], screen_rows: dict[str, dict], discovery: dict, old: dict) -> None:
    v1_rows = _load_v1()
    v1_keys = {
        (row.get("project") or "", tuple(sorted([row.get("old_adr") or "", row.get("new_adr") or ""])))
        for row in v1_rows
    }
    pairs = []
    for result in results:
        row = screen_rows.get(result["project"], {})
        for pair in result.get("pairs") or []:
            pair = dict(pair)
            pair["project"] = result["project"]
            pair["language"] = result.get("language") or row.get("language") or ""
            pair["build_tool"] = result.get("build_tool") or row.get("build_tool") or ""
            pair["adr_count"] = pair.get("adr_count") or result.get("adr_count") or 0
            pair["first_adr_date"] = pair.get("first_adr_date") or result.get("first_adr_date") or ""
            key = (result["project"], pair.get("old_adr") or "")
            pair["in_old_133"] = "yes" if key in old else "no"
            unordered = (result["project"], tuple(sorted([pair.get("old_adr") or "", pair.get("new_adr") or ""])))
            pair["in_v1"] = "yes" if unordered in v1_keys else "no"
            pairs.append(pair)
    _mark_duplicates(pairs)
    survival = _v1_survival(v1_rows, pairs)
    kept = _kept_pairs(pairs)
    with (HERE / "fresh_reversals_v2.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS_V2, extrasaction="ignore")
        writer.writeheader()
        for pair in pairs:
            writer.writerow({key: pair.get(key, "") for key in CSV_FIELDS_V2})
    _write_review_v2(kept)
    _funnel_v2(results, screen_rows, discovery, old, pairs, kept, survival)
    log(f"wrote v2 {len(pairs)} rows, {len(kept)} after duplicates")


def _funnel_v2(results, screen_rows, discovery, old, pairs, kept, survival) -> None:
    reasons: dict[str, int] = {}
    for row in screen_rows.values():
        if not row.get("keep"):
            reason = row.get("reason") or "unknown"
            reasons[reason] = reasons.get(reason, 0) + 1
    kept_repos = [row for row in screen_rows.values() if row.get("keep")]
    clone_failed = [row for row in results if row.get("error")]
    general_removed = sum(int(row.get("general_removed") or 0) for row in results)
    copied_pairs = sum(int(row.get("copied_pairs") or 0) for row in results)
    template_pairs = sum(int(row.get("template_pairs") or 0) for row in results)
    rejected = sum(int(row.get("links_rejected") or 0) for row in results)
    unresolved = sum(int(row.get("unresolved") or 0) for row in results)
    by_conf: dict[str, int] = {}
    by_year: dict[str, int] = {}
    loss: dict[str, int] = {}
    partial = 0
    for pair in kept:
        label = pair.get("confidence") or "no commit"
        by_conf[label] = by_conf.get(label, 0) + 1
        year = _pair_year(pair)
        by_year[year] = by_year.get(year, 0) + 1
        if pair.get("partial") == "yes":
            partial += 1
        if pair.get("commit_found") != "yes":
            note = pair.get("notes") or "no commit"
            loss[note] = loss.get(note, 0) + 1
    top = Counter(pair["project"] for pair in kept).most_common(10)
    top_pairs = sum(count for _project, count in top)
    sample = discovery.get("sample") or []
    queries = discovery.get("queries") or {}
    lines = [
        "# Fresh reversal funnel v2 (interim)",
        "",
        "Interim. No builds were run. This is not a pass or fail. v1 files were not rewritten.",
        "",
        f"Sample seed: {SAMPLE_SEED}. Review seed: {REVIEW_SEED}.",
        "The original 1,500 repositories stay in the draw. Newly discovered repository names were shuffled with the same seed and added after them.",
        "The implementing-commit window is 180 days before and 180 days after the new ADR's author date.",
        "One commit is chosen per pair. A title match outranks a dependency-manifest edit.",
        "",
        "## Step 1. ADR folders",
        "",
        f"v1 universe: {discovery.get('v1_universe', '')}. v1 draw kept: {discovery.get('v1_sample', '')}.",
        f"New repositories added by the extra folder queries: {discovery.get('new_repositories', 0)}.",
        f"Repositories in this run: {len(sample)}.",
        "",
    ]
    for name, stats in queries.items():
        lines.append(f"- {name}: returned {stats.get('returned')}, Sourcegraph matchCount {stats.get('match_count')}.")
    lines += [
        "",
        f"Markdown files in general folders (docs/architecture and the other broad folders) removed because the filename has no number and the file has no Status section: {general_removed}.",
        "",
        "## Step 2. Not a fork, not archived, has a build file",
        "",
        f"Screened: {len(screen_rows)}.",
        f"Kept: {len(kept_repos)}.",
        f"- fork: {reasons.get('fork', 0)}.",
        f"- archived: {reasons.get('archived', 0)}.",
        f"- no build file: {reasons.get('no build file', 0)}.",
        f"- api error: {reasons.get('api error', 0)}.",
        "",
        "## Step 3. Real replacement pairs",
        "",
        f"Repositories whose clone or read failed: {len(clone_failed)}.",
        f"Pairs removed because an ADR file is copied, vendored, or from another project: {copied_pairs}.",
        f"Pairs removed because an ADR file is a template: {template_pairs}.",
        f"ADR links that are not a real replacement sentence: {rejected}.",
        f"Replacement sentences whose other ADR could not be resolved: {unresolved}.",
        f"Pairs from more than one repository with the same ADR text, recorded as duplicates: {len(pairs) - len(kept)}.",
        f"Pairs kept: {len(kept)}.",
        f"Of those, partial supersedes: {partial}.",
        "",
        "### Compared with v1",
        "",
        f"v1 pairs: {survival.get('v1_rows', 0)}.",
        f"v1 pairs that survive into v2 (same project and the same two ADR files, either order): {survival.get('survive', 0)}.",
        f"Of the surviving pairs, direction flipped: {survival.get('flip', 0)}.",
        f"v1 pairs whose target changed: {survival.get('changed_target', 0)}.",
        f"v1 pairs dropped: {survival.get('dropped', 0)}.",
        "",
        "### New ADR year",
        "",
        f"Before 2026: {by_year.get('before 2026', 0)}.",
        f"2026: {by_year.get('2026', 0)}.",
    ]
    for year, count in sorted(by_year.items()):
        if year not in {"before 2026", "2026"}:
            lines.append(f"{year}: {count}.")
    lines += [
        "",
        f"The top 10 repositories account for {top_pairs} of {len(kept)} kept pairs.",
        "",
    ]
    for project, count in top:
        lines.append(f"- {project}: {count}.")
    lines += [
        "",
        "## Step 4. One implementing commit",
        "",
        f"high_topic: {by_conf.get('high_topic', 0)}.",
        f"high_cooccur: {by_conf.get('high_cooccur', 0)}.",
        f"Medium: {by_conf.get('medium', 0)}.",
        f"Low: {by_conf.get('low', 0)}.",
        f"No commit found: {by_conf.get('no commit', 0)}.",
        "",
    ]
    for year in ("before 2026", "2026"):
        lines.extend(_confidence_lines(kept, year))
    later_years = [year for year in by_year if year not in {"before 2026", "2026", "unknown"}]
    for year in sorted(later_years):
        lines.extend(_confidence_lines(kept, year))
    if by_year.get("unknown"):
        lines.extend(_confidence_lines(kept, "unknown"))
    lines += ["Pairs lost at this step:", ""]
    if not loss:
        lines.append("None.")
    for note, count in sorted(loss.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {count}: {note}")
    lines.append("")
    lines.extend(_known_lines(kept))
    lines += [
        "## Step 5. Comparison with the old 133",
        "",
        f"Old superseded records reconstructed from the saved measurements: {len(old)}.",
        f"Kept pairs whose old ADR is in that set: {sum(1 for pair in kept if pair.get('in_old_133') == 'yes')}.",
        "",
        "Review packets are in `review_v2/`. Fifteen come from high_topic, high_cooccur, and medium. Five more come from pairs whose new ADR is before 2026.",
        "",
    ]
    (HERE / "fresh_funnel_v2.md").write_text("\n".join(lines), encoding="utf-8")


def main_v2() -> None:
    if not token():
        raise SystemExit("GITHUB_TOKEN is not set")
    CACHE.mkdir(parents=True, exist_ok=True)
    REPO_CACHE_V2.mkdir(parents=True, exist_ok=True)
    log("start fresh reversals v2")
    discovery = step1_v2()
    sample = discovery["sample"]
    log(f"v2 sample {len(sample)} new {discovery.get('new_repositories')}")
    screened = screen(sample)
    kept = [screened[name] for name in sample if screened.get(name, {}).get("keep")]
    log(f"kept {len(kept)}")
    results = []
    pending = []
    for row in kept:
        slug = row["project"].replace("/", "__")
        cached = REPO_CACHE_V2 / f"{slug}.json"
        if cached.exists():
            results.append(json.loads(cached.read_text(encoding="utf-8")))
        else:
            pending.append(row)
    log(f"clone pending {len(pending)} cached {len(results)}")
    if pending:
        with ProcessPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(process_repo, row): row for row in pending}
            finished = 0
            for future in as_completed(futures):
                row = futures[future]
                finished += 1
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001
                    result = _empty_repo(row["project"], str(exc)[:200])
                result["language"] = row.get("language") or result.get("language") or ""
                result["build_tool"] = row.get("build_tool") or result.get("build_tool") or ""
                slug = row["project"].replace("/", "__")
                (REPO_CACHE_V2 / f"{slug}.json").write_text(json.dumps(result), encoding="utf-8")
                results.append(result)
                if finished % 10 == 0 or finished == len(pending):
                    log(f"processed {finished}/{len(pending)} {row['project']}")
    old = old_133()
    log(f"old reconstructed {len(old)}")
    write_v2(results, screened, discovery, old)
    log("EXIT:0")


if __name__ == "__main__":
    main_v2()
