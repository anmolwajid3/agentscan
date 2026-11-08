"""Screen the He et al. project list with the GitHub API.

Fork status, archive status, and the 2023 / pre-2024 commit thresholds come
from GitHub. A pom.xml check still happens on the clone, because the API does
not show that a pom existed before 2024.
"""

from __future__ import annotations

import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "projects.csv"
OUT = ROOT / "eligibility_screen.csv"
CACHE = ROOT / "cache" / "screen.jsonl"

SINCE = "2023-01-01T00:00:00Z"
UNTIL = "2024-01-01T00:00:00Z"
BATCH = 8


def token() -> str:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def screen() -> None:
    key = token()
    if not key:
        raise SystemExit("GITHUB_TOKEN is not set. Fork and archive status were not queried.")
    done = _load_cache()
    names = _project_names()
    pending = [name for name in names if name not in done]
    print(f"screen {len(names)} projects, {len(done)} cached, {len(pending)} left", flush=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("a", encoding="utf-8") as handle:
        for start in range(0, len(pending), BATCH):
            batch = pending[start : start + BATCH]
            rows = _query(batch, key)
            for name, row in rows.items():
                done[name] = row
                handle.write(json.dumps({"project": name, **row}) + "\n")
            handle.flush()
            if (start // BATCH) % 25 == 0:
                print(f"  screened {min(start + BATCH, len(pending))}/{len(pending)}", flush=True)
    _write(names, done)
    eligible = sum(1 for name in names if done.get(name, {}).get("api_eligible") == "yes")
    print(f"api eligible {eligible} of {len(names)}", flush=True)


def _project_names() -> list[str]:
    names = []
    with SOURCE.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("nameWithOwner") or "").strip()
            if name:
                names.append(name)
    return names


def _load_cache() -> dict[str, dict]:
    found: dict[str, dict] = {}
    if not CACHE.exists():
        return found
    for line in CACHE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        found[row["project"]] = {key: value for key, value in row.items() if key != "project"}
    return found


def _query(batch: list[str], key: str) -> dict[str, dict]:
    fields = []
    for index, name in enumerate(batch):
        owner, repo = name.split("/", 1)
        fields.append(
            f"""
            r{index}: repository(owner: {json.dumps(owner)}, name: {json.dumps(repo)}) {{
              isFork
              isArchived
              pushedAt
              defaultBranchRef {{
                target {{
                  ... on Commit {{
                    in2023: history(first: 10, since: "{SINCE}", until: "{UNTIL}") {{
                      nodes {{ oid }}
                    }}
                    before2024: history(first: 50, until: "{UNTIL}") {{
                      nodes {{ oid }}
                    }}
                  }}
                }}
              }}
            }}
            """
        )
    query = "query {\n" + "\n".join(fields) + "\n}"
    payload = _post(query, key)
    if payload.get("data") is None:
        if len(batch) == 1:
            name = batch[0]
            message = ""
            if payload.get("errors"):
                message = payload["errors"][0].get("message") or "repository not returned"
            return {name: _row("NA", "NA", "", "NA", "NA", "no", message[:200])}
        rows = {}
        for name in batch:
            rows.update(_query([name], key))
        return rows
    errors = {item.get("path", [None])[0]: item for item in payload.get("errors") or []}
    data = payload.get("data") or {}
    rows = {}
    for index, name in enumerate(batch):
        alias = f"r{index}"
        repo = data.get(alias)
        if repo is None:
            message = ""
            err = errors.get(alias) or {}
            message = err.get("message") or "repository not returned"
            rows[name] = _row("NA", "NA", "", "NA", "NA", "no", message[:200])
            continue
        commit = ((repo.get("defaultBranchRef") or {}).get("target") or {})
        in_2023 = ((commit.get("in2023") or {}).get("nodes") or [])
        before = ((commit.get("before2024") or {}).get("nodes") or [])
        fork = "yes" if repo.get("isFork") else "no"
        archived = "yes" if repo.get("isArchived") else "no"
        enough_2023 = "yes" if len(in_2023) >= 10 else "no"
        enough_before = "yes" if len(before) >= 50 else "no"
        # Archived now has no archive date. Those projects stay out of the eligible set.
        api_ok = fork == "no" and archived == "no" and enough_2023 == "yes" and enough_before == "yes"
        rows[name] = _row(
            fork,
            archived,
            repo.get("pushedAt") or "",
            enough_2023,
            enough_before,
            "yes" if api_ok else "no",
            "",
        )
    return rows


def _row(fork: str, archived: str, pushed: str, year: str, before: str, eligible: str, error: str) -> dict:
    return {
        "fork": fork,
        "archived_now": archived,
        "pushed_at": pushed,
        "commits_in_2023_at_least_10": year,
        "commits_before_2024_at_least_50": before,
        "api_eligible": eligible,
        "api_error": error,
    }


def _post(query: str, key: str) -> dict:
    body = json.dumps({"query": query}).encode("utf-8")
    for attempt in range(6):
        request = urllib.request.Request(
            "https://api.github.com/graphql",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": "swap-feasibility",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            if exc.code in {403, 429, 502, 503}:
                time.sleep(min(120, 2 ** attempt * 5))
                continue
            raise SystemExit(f"GitHub API {exc.code}: {detail}") from exc
        except urllib.error.URLError:
            time.sleep(min(60, 2 ** attempt * 2))
    raise SystemExit("GitHub API did not answer after retries")


def _write(names: list[str], done: dict[str, dict]) -> None:
    fields = [
        "project",
        "fork",
        "archived_now",
        "pushed_at",
        "commits_in_2023_at_least_10",
        "commits_before_2024_at_least_50",
        "api_eligible",
        "api_error",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for name in names:
            row = done.get(name) or _row("NA", "NA", "", "NA", "NA", "NA", "not screened")
            writer.writerow({"project": name, **row})
