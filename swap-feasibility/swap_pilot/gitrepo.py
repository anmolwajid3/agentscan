"""Git helpers for a partial clone."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path


class GitError(RuntimeError):
    pass


def run_git(repo: str, args: list[str], timeout: int = 120) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", repo, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"timeout: git {' '.join(args[:4])}") from exc
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise GitError(message[:300] or f"git exited {result.returncode}")
    return result.stdout


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def head_sha(repo: str) -> str:
    return run_git(repo, ["rev-parse", "HEAD"]).strip()


def last_commit_date(repo: str) -> str:
    return run_git(repo, ["log", "-1", "--format=%aI"]).strip()


def first_commit_date(repo: str) -> str:
    """Author date of the earliest root commit.

    ``git log -1 --reverse`` still returns the newest commit, because the limit
    is applied first. The root list is what the history actually starts from.
    """
    roots = run_git(repo, ["rev-list", "--max-parents=0", "HEAD"], timeout=180).split()
    dated = []
    for root in roots:
        text = run_git(repo, ["log", "-1", "--format=%aI", root]).strip()
        when = parse_dt(text)
        if when is not None:
            dated.append((when, text))
    if not dated:
        return ""
    return min(dated)[1]


def rev_count(repo: str, before: str | None = None, after: str | None = None) -> int | None:
    args = ["rev-list", "--count", "HEAD"]
    if before:
        args.append(f"--before={before}")
    if after:
        args.append(f"--after={after}")
    text = run_git(repo, args, timeout=180).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def had_pom_before(repo: str, before: str) -> bool | None:
    text = run_git(
        repo,
        ["log", "-1", f"--before={before}", "--pretty=%H", "--", "pom.xml", "**/pom.xml"],
        timeout=180,
    ).strip()
    return bool(text)


def show_file(repo: str, sha: str, path: str) -> str | None:
    try:
        return run_git(repo, ["show", f"{sha}:{path}"], timeout=60)
    except GitError:
        return None


def indexed_oids(repo: str) -> set[str]:
    """Object ids already stored in this clone, without asking the network."""
    found: set[str] = set()
    git_dir = Path(repo) / ".git"
    for index in git_dir.glob("objects/pack/*.idx"):
        result = subprocess.run(
            ["git", "show-index"],
            stdin=index.open("rb"),
            check=False,
            capture_output=True,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                found.add(parts[1].decode())
    for path in git_dir.glob("objects/??/*"):
        if path.is_file():
            found.add(path.parent.name + path.name)
    return found


def prefetch_blobs(repo: str, oids: list[str], batch: int = 50) -> int:
    """Fetch missing blobs in batches.

    A partial clone does not contain file contents. Asking for one blob at a
    time spends most of the time on a separate connection, so the missing pom
    blobs are requested together. Returns how many were requested.
    """
    wanted = []
    seen = set()
    for oid in oids:
        if not oid or oid in seen or oid == "0" * 40:
            continue
        if len(oid) != 40 or any(ch not in "0123456789abcdef" for ch in oid):
            continue
        seen.add(oid)
        wanted.append(oid)
    have = indexed_oids(repo)
    missing = [oid for oid in wanted if oid not in have]
    for start in range(0, len(missing), batch):
        chunk = missing[start : start + batch]
        if start % 500 == 0:
            print(f"    blobs {start}/{len(missing)}", flush=True)
        subprocess.run(
            ["git", "-C", repo, "fetch", "--no-tags", "origin", *chunk],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    return len(missing)


def read_blobs(repo: str, oids: list[str]) -> dict[str, str | None]:
    """Return blob text. None means the blob could not be read."""
    unique = []
    seen = set()
    for oid in oids:
        if not oid or oid in seen or oid == "0" * 40:
            continue
        seen.add(oid)
        unique.append(oid)
    if not unique:
        return {}
    try:
        result = subprocess.run(
            ["git", "-C", repo, "cat-file", "--batch"],
            input=("\n".join(unique) + "\n").encode(),
            check=False,
            capture_output=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {oid: None for oid in unique}
    texts: dict[str, str | None] = {}
    data = result.stdout
    cursor = 0
    while cursor < len(data):
        newline = data.find(b"\n", cursor)
        if newline < 0:
            break
        header = data[cursor:newline].decode("utf-8", errors="replace")
        cursor = newline + 1
        parts = header.split()
        if len(parts) < 3 or parts[1] == "missing":
            if parts:
                texts[parts[0]] = None
            continue
        size = int(parts[2])
        body = data[cursor : cursor + size]
        cursor += size + 1
        texts[parts[0]] = body.decode("utf-8", errors="replace")
    for oid in unique:
        texts.setdefault(oid, None)
    return texts
