"""Build the sampling frame.

Two public sources, both searched on the run date:

1. The Buchgeher et al. census of GitHub ADR repositories (crawled January 2022).
   This is the list behind the "about half of projects have only one to five ADRs"
   finding. It is a census of that date, not a fresh search.
2. A Sourcegraph query over the public GitHub index for ADR folder paths.
   GitHub code search itself requires an authenticated token. When GITHUB_TOKEN
   or GH_TOKEN is set, the same paths are also queried through the GitHub API.

Archived repositories are included. A project that went quiet after adopting
AI is part of the population the reviewers asked us not to drop.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

SOURCEGRAPH = "https://sourcegraph.com/.api/search/stream"
DATASET_URL = "https://github.com/software-competence-center-hagenberg/ADR-Study-Dataset.git"

QUERIES = {
    "docs_adr": r"context:global file:docs/adr/.*\.md$ select:repo count:1000",
    "doc_adr": r"context:global file:doc/adr/.*\.md$ select:repo count:500",
    "docs_decisions": r"context:global file:docs/decisions/.*\.md$ select:repo count:500",
    "arch_decisions": r"context:global file:architecture/decisions/.*\.md$ select:repo count:400",
    "doc_arch_decisions": r"context:global file:doc/architecture/decisions/.*\.md$ select:repo count:300",
    "adr_root": r"context:global file:^adr/[0-9].*\.md$ select:repo count:500",
    "docs_adrs": r"context:global file:docs/adrs/.*\.md$ select:repo count:300",
    "docs_adr_archived": r"context:global archived:yes file:docs/adr/.*\.md$ select:repo count:300",
    "superseded_phrase": r'context:global "superseded by" file:\.md$ select:repo count:500',
}


def _sourcegraph(query: str, timeout: int = 120) -> tuple[list[dict], dict | None]:
    url = SOURCEGRAPH + "?v=V3&t=keyword&q=" + urllib.parse.quote(query)
    request = urllib.request.Request(url, headers={"Accept": "text/event-stream", "User-Agent": "adr-pilot"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8", "replace")
    repos: list[dict] = []
    progress = None
    event = None
    data: list[str] = []

    def flush() -> None:
        nonlocal progress, event, data
        if not event:
            return
        raw = "".join(data)
        if event == "matches" and raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return
            if isinstance(payload, dict):
                payload = [payload]
            for item in payload:
                if isinstance(item, dict) and item.get("type") == "repo" and item.get("repository"):
                    repos.append(
                        {
                            "repository": item["repository"],
                            "stars": item.get("repoStars"),
                            "description": item.get("description") or "",
                        }
                    )
        elif event == "progress" and raw:
            try:
                progress = json.loads(raw)
            except json.JSONDecodeError:
                pass

    for line in text.splitlines():
        if line.startswith("event:"):
            flush()
            event = line[6:].strip()
            data = []
        elif line.startswith("data:"):
            data.append(line[5:].strip())
        elif line == "":
            flush()
            event = None
            data = []
    flush()
    unique: list[dict] = []
    seen: set[str] = set()
    for repo in repos:
        if repo["repository"] not in seen:
            seen.add(repo["repository"])
            unique.append(repo)
    return unique, progress


def search_sourcegraph() -> dict[str, dict]:
    found: dict[str, dict] = {}
    for name, query in QUERIES.items():
        try:
            repos, progress = _sourcegraph(query)
        except Exception as exc:  # noqa: BLE001 - one query should not abort the frame
            print(f"sourcegraph {name} failed: {exc}")
            continue
        match_count = progress.get("matchCount") if progress else None
        print(f"sourcegraph {name}: {len(repos)} repos (reported {match_count})")
        for repo in repos:
            full = repo["repository"]
            if not full.startswith("github.com/"):
                continue
            row = found.setdefault(
                full,
                {
                    "repository": full,
                    "stars": repo.get("stars"),
                    "description": repo.get("description") or "",
                    "sources": [],
                },
            )
            if repo.get("stars"):
                row["stars"] = repo["stars"]
            if repo.get("description") and not row["description"]:
                row["description"] = repo["description"]
            if name not in row["sources"]:
                row["sources"].append(name)
    return found


def ensure_buchgeher(dest: Path) -> Path:
    if (dest / "repositories").is_dir() and any((dest / "repositories").glob("*.json")):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", DATASET_URL, str(dest)],
        check=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return dest


def load_buchgeher(dest: Path) -> dict[str, dict]:
    folder = dest / "repositories"
    found: dict[str, dict] = {}
    for path in folder.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        url = payload.get("repositoryUrl") or ""
        match = re.search(r"github\.com[:/](?P<name>[\w.-]+/[\w.-]+?)(?:\.git)?$", url)
        if not match:
            continue
        name = "github.com/" + match.group("name")
        found[name] = {
            "repository": name,
            "buchgeher_adr_count": payload.get("numAdrFiles") or 0,
            "buchgeher_dirs": payload.get("adrDirectories") or [],
            "buchgeher_crawled": payload.get("crawlDateTime") or "",
        }
    return found


def github_code_search(token: str) -> dict[str, dict]:
    """Optional authenticated GitHub code search. Ten requests per minute."""
    queries = [
        "path:docs/adr filename:0001 extension:md",
        "path:doc/adr filename:0001 extension:md",
        "path:docs/decisions filename:0001 extension:md",
        "path:architecture/decisions extension:md",
    ]
    found: dict[str, dict] = {}
    for query in queries:
        url = "https://api.github.com/search/code?per_page=100&q=" + urllib.parse.quote(query)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "adr-pilot",
            },
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for item in payload.get("items") or []:
            repo = (item.get("repository") or {}).get("full_name")
            if not repo:
                continue
            full = "github.com/" + repo
            row = found.setdefault(full, {"repository": full, "sources": [], "description": "", "stars": None})
            if "github-code-search" not in row["sources"]:
                row["sources"].append("github-code-search")
        print(f"github code search '{query}': page {len(payload.get('items') or [])}, total {payload.get('total_count')}")
    return found


def probe_ai_files(repositories: list[str]) -> set[str]:
    """Ask Sourcegraph which candidate repos contain an official AI instruction file."""
    flagged: set[str] = set()
    batch = 25
    for start in range(0, len(repositories), batch):
        chunk = repositories[start : start + batch]
        names = "|".join(re.escape(repo) for repo in chunk)
        query = (
            r"context:global repo:^(" + names + r")$ "
            r"(file:(^|/)CLAUDE\.md$ OR file:(^|/)AGENTS\.md$ OR file:(^|/)\.cursorrules$ "
            r"OR file:copilot-instructions\.md$) select:repo count:100"
        )
        try:
            repos, _progress = _sourcegraph(query, timeout=90)
        except Exception as exc:  # noqa: BLE001
            print(f"ai probe batch {start} failed: {exc}")
            continue
        for repo in repos:
            flagged.add(repo["repository"])
        print(f"ai probe {start + len(chunk)}/{len(repositories)} flagged {len(flagged)}")
    return flagged


def build_frame(buchgeher_dir: Path, use_github_token: bool = True) -> list[dict]:
    sourcegraph = search_sourcegraph()
    buchgeher = load_buchgeher(ensure_buchgeher(buchgeher_dir))
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    github: dict[str, dict] = {}
    if use_github_token and token:
        try:
            github = github_code_search(token)
        except Exception as exc:  # noqa: BLE001
            print(f"github code search skipped: {exc}")
    elif not token:
        print("No GITHUB_TOKEN set. GitHub code search needs one; Sourcegraph is the live index used instead.")

    superseded_names = {
        name for name, row in sourcegraph.items() if "superseded_phrase" in row.get("sources", [])
    }
    for name in list(sourcegraph):
        sources = sourcegraph[name].get("sources") or []
        if sources == ["superseded_phrase"]:
            del sourcegraph[name]
    names = set(sourcegraph) | set(buchgeher) | set(github)
    # Probe AI files on the union. This can be a few hundred requests; batching keeps it small.
    flagged = probe_ai_files(sorted(names))
    rows = []
    for name in sorted(names):
        sg = sourcegraph.get(name, {})
        older = buchgeher.get(name, {})
        gh = github.get(name, {})
        sources = []
        for item in sg.get("sources", []):
            sources.append("sourcegraph:" + item)
        if older:
            sources.append("buchgeher-2022")
        for item in gh.get("sources", []):
            sources.append(item)
        rows.append(
            {
                "repository": name,
                "url": "https://" + name + ".git",
                "stars": sg.get("stars") if sg.get("stars") is not None else "",
                "description": (sg.get("description") or "")[:300],
                "sources": ";".join(sources),
                "buchgeher_adr_count": older.get("buchgeher_adr_count", ""),
                "buchgeher_dirs": ";".join(older.get("buchgeher_dirs") or []),
                "ai_file_probe": "yes" if name in flagged else "no",
                "superseded_probe": "yes" if name in superseded_names else "no",
            }
        )
    return rows


def write_frame(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "repository",
        "url",
        "stars",
        "description",
        "sources",
        "buchgeher_adr_count",
        "buchgeher_dirs",
        "ai_file_probe",
        "superseded_probe",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_frame(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
