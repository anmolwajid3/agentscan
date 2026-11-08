"""Find library swaps from pom.xml history."""

from __future__ import annotations

import posixpath
import re
from collections import defaultdict
from datetime import datetime, timedelta

from swap_pilot.adopt import commit_is_ai
from swap_pilot.gitrepo import parse_dt, prefetch_blobs, read_blobs, run_git
from swap_pilot.pom import parent_relative_path, parse_pom

_BOT = re.compile(r"(?i)dependabot|renovate")
_POM = re.compile(r"(^|/)pom\.xml$")


def _is_pom(path: str) -> bool:
    return bool(_POM.search(path.replace("\\", "/")))


def pom_commits(repo: str) -> list[dict]:
    """Commits on the first-parent history that touch a pom.xml."""
    text = run_git(
        repo,
        [
            "log",
            "--first-parent",
            "--reverse",
            "--diff-filter=AMDR",
            "--name-status",
            "--pretty=format:COMMIT%x1f%H%x1f%aI%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%s%x1e%n%b%x1e",
            "--",
            "pom.xml",
            "**/pom.xml",
        ],
        timeout=300,
    )
    commits = []
    for block in text.split("COMMIT\x1f")[1:]:
        head, _, rest = block.partition("\x1e")
        body, _, names = rest.partition("\x1e")
        parts = head.split("\x1f")
        if len(parts) < 7:
            continue
        files = []
        for line in names.splitlines():
            bits = line.split("\t")
            if len(bits) < 2:
                continue
            path = bits[-1]
            if _is_pom(path):
                files.append(path)
        if not files:
            continue
        commits.append(
            {
                "sha": parts[0],
                "date": parts[1],
                "author": parts[2],
                "email": parts[3],
                "committer": parts[4],
                "committer_email": parts[5],
                "subject": parts[6],
                "message": body,
                "files": files,
            }
        )
    return commits


def _is_bot(commit: dict) -> bool:
    blob = " ".join(
        [
            commit.get("author") or "",
            commit.get("email") or "",
            commit.get("committer") or "",
            commit.get("committer_email") or "",
        ]
    )
    return bool(_BOT.search(blob))


def _pom_history(repo: str) -> list[tuple[str, list[tuple[str, str, str, list[str]]]]]:
    """Chronological first-parent pom changes: sha, then status/old/new/paths."""
    text = run_git(
        repo,
        [
            "log",
            "--first-parent",
            "--reverse",
            "--raw",
            "--no-abbrev",
            "--diff-filter=AMDRC",
            "--pretty=format:COMMIT %H",
            "--",
            "pom.xml",
            "**/pom.xml",
        ],
        timeout=300,
    )
    order: list[tuple[str, list[tuple[str, str, str, list[str]]]]] = []
    current = ""
    changes: list[tuple[str, str, str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("COMMIT "):
            if current:
                order.append((current, changes))
            current = line[7:].strip()
            changes = []
            continue
        if not current or not line.startswith(":"):
            continue
        meta, *paths = line.split("\t")
        bits = meta.split()
        if len(bits) < 5 or not paths:
            continue
        if any(_is_pom(path) for path in paths):
            changes.append((bits[4], bits[2], bits[3], paths))
    if current:
        order.append((current, changes))
    return order


def _apply_pom_change(state: dict[str, str], status: str, old: str, new: str, paths: list[str]) -> None:
    empty = "0" * 40
    if status.startswith("R"):
        state.pop(paths[0], None)
        if new != empty:
            state[paths[-1]] = new
        return
    if status.startswith("C"):
        if new != empty:
            state[paths[-1]] = new
        return
    path = paths[-1]
    if new == empty:
        state.pop(path, None)
    else:
        state[path] = new


def dependency_changes(repo: str, project: str, commits: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return change rows and per-commit add/remove sets.

    Before and after are the libraries in every pom.xml on that commit, not
    only the file the commit edited. A file that cannot be read is an unparsed
    row, not a silent skip.
    """
    history = _pom_history(repo)
    by_sha = {commit["sha"]: commit for commit in commits}
    oids = [oid for _, changes in history for _, old, new, _ in changes for oid in (old, new)]
    requested = prefetch_blobs(repo, oids)
    print(f"  prefetch {requested} pom blobs", flush=True)
    texts = read_blobs(repo, oids)
    parsed: dict[tuple[str, ...], tuple[set[str], list[str]] | None] = {}
    relative_by_oid: dict[str, str | None] = {}

    def relative_for(oid: str, text: str) -> str | None:
        if oid not in relative_by_oid:
            relative_by_oid[oid] = parent_relative_path(text)
        return relative_by_oid[oid]

    def libraries(path: str, files: dict[str, str]) -> tuple[set[str], list[str]] | None:
        oids: list[str] = []
        parent_texts: list[str] = []
        seen: set[str] = set()
        current = path
        while current and current not in seen:
            seen.add(current)
            oid = files.get(current)
            if not oid:
                break
            text = texts.get(oid)
            if text is None:
                if current == path:
                    return None
                break
            oids.append(oid)
            if current != path:
                parent_texts.append(text)
            relative = relative_for(oid, text)
            if not relative:
                break
            nxt = posixpath.normpath(posixpath.join(posixpath.dirname(current), relative))
            if nxt == current:
                break
            current = nxt
        key = tuple(oids)
        if key not in parsed:
            parsed[key] = parse_pom(texts[oids[0]], parent_texts)
        return parsed[key]

    def union_deps(files: dict[str, str], commit: dict, when: str) -> set[str]:
        found: set[str] = set()
        for path in files:
            result = libraries(path, files)
            if result is None:
                rows.append(_change_row(project, commit, path, "", "", "yes", f"could not read pom.xml {when}"))
                continue
            deps, notes = result
            found |= deps
            if path in changed_paths:
                for note in notes:
                    rows.append(_change_row(project, commit, path, "", "", "yes", note))
        return found

    rows: list[dict] = []
    events = []
    state: dict[str, str] = {}
    for sha, changes in history:
        commit = by_sha.get(sha)
        if commit is None:
            for status, old, new, paths in changes:
                _apply_pom_change(state, status, old, new, paths)
            continue
        before_files = dict(state)
        for status, old, new, paths in changes:
            _apply_pom_change(state, status, old, new, paths)
        after_files = state
        changed_paths = {
            path
            for path in set(before_files) | set(after_files)
            if before_files.get(path) != after_files.get(path)
        }
        before = union_deps(before_files, commit, "before")
        after = union_deps(after_files, commit, "after")
        removed = before - after
        added = after - before
        for lib in sorted(removed):
            rows.append(_change_row(project, commit, "", "rem", lib, "no", ""))
        for lib in sorted(added):
            rows.append(_change_row(project, commit, "", "add", lib, "no", ""))
        events.append({**commit, "removed": removed, "added": added, "bot": _is_bot(commit)})
    return rows, events


def _change_row(project: str, commit: dict, path: str, change: str, lib: str, unparsed: str, note: str) -> dict:
    return {
        "project": project,
        "commit": commit["sha"],
        "date": commit["date"],
        "file": path,
        "change": change,
        "lib": lib,
        "unparsed": unparsed,
        "parse_note": note,
    }


def same_commit_swaps(project: str, events: list[dict], rules: dict[tuple[str, str], dict]) -> list[dict]:
    rules_from: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for (source, target), rule in rules.items():
        rules_from[source].append((target, rule))
    found = []
    for event in events:
        ai = commit_is_ai(event.get("author") or "", event.get("email") or "", event.get("message") or "")
        for source in event["removed"]:
            for target, rule in rules_from.get(source, []):
                if target in event["added"]:
                    found.append(_swap_row(project, event, source, target, rule, "same commit", ai))
    return found


def window_swaps(project: str, events: list[dict], rules: dict[tuple[str, str], dict], window_days: int) -> list[dict]:
    additions: dict[str, list[tuple[datetime, dict]]] = defaultdict(list)
    rules_from: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for (source, target), rule in rules.items():
        rules_from[source].append((target, rule))
    removals = []
    for event in events:
        when = parse_dt(event["date"])
        if when is None:
            continue
        for lib in event["removed"]:
            removals.append((when, lib, event))
        for lib in event["added"]:
            additions[lib].append((when, event))
    found = []
    window = timedelta(days=window_days)
    for removed_at, source, removal in removals:
        for target, rule in rules_from.get(source, []):
            for added_at, addition in additions.get(target, []):
                if removal["sha"] == addition["sha"]:
                    continue
                if abs(added_at - removed_at) > window:
                    continue
                ai = commit_is_ai(
                    removal.get("author") or "", removal.get("email") or "", removal.get("message") or ""
                ) or commit_is_ai(
                    addition.get("author") or "", addition.get("email") or "", addition.get("message") or ""
                )
                # The row is dated at the later of the two commits. The SHA is the removal.
                later = removal if removed_at >= added_at else addition
                row = _swap_row(project, later, source, target, rule, "30-day window", ai)
                row["commit"] = removal["sha"]
                row["pair_commit"] = addition["sha"]
                row["bot"] = "yes" if removal["bot"] or addition["bot"] else "no"
                found.append(row)
    return found


def _swap_row(project: str, event: dict, source: str, target: str, rule: dict, mode: str, ai: bool) -> dict:
    return {
        "project": project,
        "commit": event["sha"],
        "pair_commit": "",
        "date": event["date"],
        "lib_removed": source,
        "lib_added": target,
        "rule_id": rule["rule_id"],
        "rule_type": rule["rule_type"],
        "rule_category": "rename" if str(rule.get("rule_type") or "").startswith("rename") else "main",
        "detection": mode,
        "bot": "yes" if event.get("bot") else "no",
        "ai": "yes" if ai else "no",
        "group": "",
    }


def assign_group(row: dict, ai_signal: str, adoption_date: str, control_start: datetime, cutoff: datetime) -> str:
    when = parse_dt(row.get("date"))
    if when is None or ai_signal not in {"yes", "no"}:
        return "NA"
    if ai_signal == "yes":
        adopted = parse_dt(adoption_date)
        if adopted is None:
            return "NA"
        return "ai_after" if when >= adopted else "ai_before"
    if control_start <= when <= cutoff:
        return "control_same_period"
    return "NA"
