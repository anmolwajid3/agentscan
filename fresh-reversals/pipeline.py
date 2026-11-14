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
    first_paragraph,
    is_adr_path,
    is_application_path,
    is_config_or_schema,
    keyword_hits,
    keywords_from,
    mentions_adr,
    pairs_in_repo,
    technologies_in,
    title_of,
)

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
REPO_CACHE = CACHE / "repos"
LOG = HERE / "run.log"
CLONE_ROOT = Path("/tmp/fresh-reversals")
SAMPLE_SEED = 20261114
REVIEW_SEED = 20261114
CAP = 1500
WINDOW_DAYS = 180
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
    signal.alarm(600)
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
        return {"project": name, "error": detail, "pairs": [], "adr_count": 0, "links_rejected": 0, "unresolved": 0}
    listed = run_cmd(["git", "-C", str(dest), "ls-tree", "-r", "--name-only", "HEAD"], timeout=90)
    if listed.returncode != 0:
        return {"project": name, "error": "ls-tree failed", "pairs": [], "adr_count": 0, "links_rejected": 0, "unresolved": 0}
    adr_paths = [line for line in listed.stdout.splitlines() if is_adr_path(line)]
    if len(adr_paths) < 2:
        return {"project": name, "error": "", "pairs": [], "adr_count": len(adr_paths), "links_rejected": 0, "unresolved": 0}
    records = []
    for path in adr_paths:
        blob = run_cmd(["git", "-C", str(dest), "cat-file", "blob", f"HEAD:{path}"], timeout=60)
        if blob.returncode != 0:
            continue
        records.append({"path": path, "text": blob.stdout})
    found, rejected, unresolved = pairs_in_repo(records)
    pairs = []
    for pair in found:
        pairs.append(_search_pair(dest, name, pair))
    return {
        "project": name,
        "error": "",
        "pairs": pairs,
        "adr_count": len(adr_paths),
        "links_rejected": rejected,
        "unresolved": unresolved,
        "language": row.get("language") or "",
        "build_tool": row.get("build_tool") or "",
    }


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
    result = run_cmd(["git", "-C", str(dest), "diff-tree", "--no-commit-id", "--name-only", "-r", sha], timeout=40)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


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
        if current is None or not line.strip():
            continue
        path = line.split("\t")[-1].strip()
        if path:
            files.append(path)
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


def _search_pair(dest: Path, project: str, pair: dict) -> dict:
    added = _oldest_add(dest, pair["new_adr"])
    base = {
        "old_adr": pair["old_adr"],
        "new_adr": pair["new_adr"],
        "supersede_wording": pair.get("supersede_wording") or "",
        "old_status": pair.get("old_status") or "",
        "new_title": title_of(pair.get("new_text") or ""),
        "new_paragraph": first_paragraph(pair.get("new_text") or ""),
        "adr_date": "",
        "commit_found": "no",
        "method": "",
        "implementing_commits": "",
        "commit_timing": "",
        "matched_keywords": "",
        "confidence": "",
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
    hits: list[dict] = []
    if any(is_application_path(path) for path in add_files):
        when = parse_dt(added["date"])
        hits.append(
            {
                "sha": added["sha"],
                "timing": _timing(when, adr),
                "subject": added["subject"],
                "message": _message_of(dest, added["sha"]),
                "files": add_files[:40],
                "method": "a",
                "keywords": [],
            }
        )
    else:
        for hit in _same_pr(project, added["sha"], dest, adr, start, end):
            hit["keywords"] = []
            hits.append(hit)
    numbers = [adr_identifier(pair["old_adr"]), adr_identifier(pair["new_adr"])]
    titles = [title_of(pair.get("old_text") or ""), title_of(pair.get("new_text") or "")]
    words = keywords_from(*titles)
    techs = technologies_in(pair.get("old_text") or "", pair.get("new_text") or "")
    keyword_union: list[str] = []
    for commit in commits:
        files = commit.get("files") or []
        apps = [path for path in files if is_application_path(path)]
        when = parse_dt(commit.get("date"))
        timing = _timing(when, adr)
        if mentions_adr(commit.get("subject") or "", numbers, titles) and apps:
            hits.append(
                {
                    "sha": commit["sha"],
                    "timing": timing,
                    "subject": commit.get("subject") or "",
                    "message": commit.get("subject") or "",
                    "files": files[:40],
                    "method": "b",
                    "keywords": [],
                }
            )
        config = [path for path in files if is_config_or_schema(path)]
        matched = keyword_hits(config, words)
        if matched:
            for word in matched:
                if word not in keyword_union:
                    keyword_union.append(word)
            hits.append(
                {
                    "sha": commit["sha"],
                    "timing": timing,
                    "subject": commit.get("subject") or "",
                    "message": commit.get("subject") or "",
                    "files": config[:40],
                    "method": "c",
                    "keywords": matched,
                }
            )
        tech_files = [path for path in apps if any(re.search(rf"(?<![a-z0-9]){re.escape(tech)}(?![a-z0-9])", path.lower()) for tech in techs)]
        if tech_files:
            hits.append(
                {
                    "sha": commit["sha"],
                    "timing": timing,
                    "subject": commit.get("subject") or "",
                    "message": commit.get("subject") or "",
                    "files": tech_files[:40],
                    "method": "d",
                    "keywords": [],
                }
            )
    if not hits:
        base["notes"] = "no implementing commit in the 180-day window"
        return base
    methods = []
    for hit in hits:
        if hit["method"] not in methods:
            methods.append(hit["method"])
    if "a" in methods or "b" in methods:
        confidence = "high"
    elif "c" in methods:
        confidence = "medium"
    else:
        confidence = "low"
    # Keep every method that fired. Cap the commit list so one busy repository cannot flood the sheet.
    chosen = []
    seen = set()
    for hit in hits:
        if hit["sha"] in seen:
            continue
        seen.add(hit["sha"])
        if hit["method"] == "b" or hit["method"] == "a":
            message = hit.get("message") or hit.get("subject") or ""
            if message == hit.get("subject"):
                message = _message_of(dest, hit["sha"])
            hit["message"] = message
        chosen.append(hit)
        if len(chosen) >= 12:
            break
    base["commit_found"] = "yes"
    base["method"] = "+".join(methods)
    base["confidence"] = confidence
    base["implementing_commits"] = ",".join(hit["sha"] for hit in chosen)
    base["commit_timing"] = ",".join(hit["timing"] for hit in chosen)
    base["matched_keywords"] = ",".join(keyword_union)
    if len(seen) > len(chosen):
        base["notes"] = f"{len(seen)} commits matched; 12 listed"
    base["details"] = [
        {"sha": hit["sha"], "timing": hit["timing"], "message": hit.get("message") or hit.get("subject") or "", "files": hit.get("files") or []}
        for hit in chosen
    ]
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


if __name__ == "__main__":
    main()
