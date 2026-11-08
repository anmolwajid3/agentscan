"""Find the commit that puts an ADR into practice, and any discussion refs.

The study plan's proxy: the first commit after the ADR that touches a file
or module the ADR names. A commit that only edits the ADR file does not count.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PATH = re.compile(
    r"`([^`\n]{2,160})`|(?<![A-Za-z0-9_])((?:[\w.-]+/)+[\w.-]+\.[\w]{1,8})"
)
_PATH_EXT = re.compile(
    r"(?i)\.(?:py|js|jsx|ts|tsx|go|java|rs|rb|cs|kt|php|scala|c|cc|cpp|h|hpp|"
    r"yml|yaml|json|tf|sql|gradle|xml|proto|vue|svelte)$"
)
_ISSUE = re.compile(
    r"(?i)(?:https?://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)/(?:issues|pull)/(?P<num>\d+))"
    r"|(?:(?P<kind>issue|pull request|pr)\s*#(?P<hash>\d+))|(?<![\w/])#(?P<bare>\d+)\b"
)
_ADR_SELF = re.compile(r"(?i)(^|/)(adr|adrs|decisions|architecture-decision)")


@dataclass(frozen=True)
class ImplementationHit:
    sha: str | None
    date: str | None
    subject: str | None
    reason: str
    paths: tuple[str, ...]


def extract_paths(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in _PATH.finditer(text or ""):
        raw = match.group(1) or match.group(2) or ""
        raw = raw.strip().strip(".,:;")
        if not raw or " " in raw or raw.startswith("http"):
            continue
        if not (_PATH_EXT.search(raw) or "/" in raw):
            continue
        if _ADR_SELF.search(raw) and raw.lower().endswith((".md", ".markdown", ".rst", ".adoc")):
            continue
        if raw not in seen:
            seen.add(raw)
            found.append(raw)
    return found[:40]


def extract_discussion_refs(text: str) -> list[dict]:
    refs: list[dict] = []
    seen: set[str] = set()
    for match in _ISSUE.finditer(text or ""):
        if match.group("num"):
            key = f"{match.group('owner')}/{match.group('repo')}#{match.group('num')}"
            kind = "pull" if "/pull/" in match.group(0) else "issue"
            url = match.group(0)
        else:
            number = match.group("hash") or match.group("bare")
            key = f"#{number}"
            word = (match.group("kind") or "").lower()
            kind = "pull" if word.startswith("pr") or word.startswith("pull") else "hash"
            url = ""
        if key in seen:
            continue
        seen.add(key)
        refs.append({"key": key, "kind": kind, "url": url, "number": key.split("#")[-1]})
    return refs[:20]


def pick_implementation(
    adr_date: str,
    adr_path: str,
    mentioned_paths: list[str],
    adr_token: str,
    commits: list[dict],
) -> ImplementationHit:
    """Choose the implementation commit from commits that touch this repo.

    Each commit dict needs sha, date, subject, files (list of paths).
    Dates are ISO strings. ``adr_date`` is the ADR's first commit date.
    """
    from adr_pilot.eligibility import parse_dt

    born = parse_dt(adr_date)
    token = adr_token.lower().strip()

    def after(commit: dict) -> bool:
        when = parse_dt(commit.get("date"))
        if born is None or when is None:
            return True
        return when >= born

    def code_files(commit: dict) -> list[str]:
        files = []
        for path in commit.get("files") or []:
            if path == adr_path:
                continue
            if path.lower().endswith((".md", ".markdown", ".rst", ".adoc")) and _ADR_SELF.search(path):
                continue
            files.append(path)
        return files

    # Prefer a later commit whose message names this ADR and which edits code.
    if token:
        for commit in commits:
            if not after(commit):
                continue
            subject = (commit.get("subject") or "").lower()
            if token not in subject and f"adr-{token}" not in subject and f"adr {token}" not in subject:
                continue
            files = code_files(commit)
            if files:
                return ImplementationHit(
                    commit.get("sha"),
                    commit.get("date"),
                    commit.get("subject"),
                    "commit-message-names-the-adr",
                    tuple(files[:12]),
                )

    if mentioned_paths:
        needles = [path.lower() for path in mentioned_paths]
        for commit in commits:
            if not after(commit):
                continue
            files = code_files(commit)
            hit = []
            for path in files:
                low = path.lower()
                if any(needle == low or low.endswith("/" + needle) or needle.endswith("/" + low) or needle in low for needle in needles):
                    hit.append(path)
            if hit:
                return ImplementationHit(
                    commit.get("sha"),
                    commit.get("date"),
                    commit.get("subject"),
                    "first-commit-touching-a-path-named-in-the-adr",
                    tuple(hit[:12]),
                )

    return ImplementationHit(None, None, None, "no-code-commit-found", ())
