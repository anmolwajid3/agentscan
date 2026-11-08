"""Read one Git repository and measure ADR history and AI signals.

The clone is partial: Git objects for commits and trees, blobs only when an
ADR or signal file is read. History is the default branch, which is where
merged decision records live.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass

from adr_pilot.eligibility import classify_project, parse_dt
from adr_pilot.endings import classify_ending
from adr_pilot.lead import extract_discussion_refs, extract_paths, pick_implementation
from adr_pilot.signals import (
    ai_coauthor_hits,
    classify_signal_path,
    is_agent_author,
    mention_kind,
)
from adr_pilot.status import adr_identifier, adr_title, parse_status

ADR_PATHSPECS = [
    "docs/adr",
    "doc/adr",
    "adr",
    "adrs",
    "docs/adrs",
    "doc/adrs",
    "docs/decisions",
    "doc/decisions",
    "architecture/decisions",
    "docs/architecture/decisions",
    "doc/architecture/decisions",
    "docs/architecture-decisions",
    "doc/architecture-decisions",
    "docs/architecture/adr",
    "doc/architecture/adr",
    "docs/architecture",
    "doc/architecture",
    "docs/arch",
    "doc/arch",
    "design/adr",
    "docs/design/adr",
    "architecture-decisions",
    "decisions/adr",
]

SIGNAL_PATHSPECS = [
    ":(glob)**/CLAUDE.md",
    ":(glob)**/CLAUDE.local.md",
    ":(glob)**/AGENTS.md",
    ":(glob)**/AGENTS.override.md",
    ":(glob)**/.cursorrules",
    ":(glob)**/copilot-instructions.md",
    ":(glob)**/GEMINI.md",
    ":(glob)**/.windsurfrules",
    ":(glob)**/.cursor/rules/**",
    ":(glob)**/.github/agents/**",
]

_TEMPLATE_NAME = re.compile(
    r"(?i)(?:^|/)(?:awesome-[\w.-]*|architecture-decision-record|adr-tools|"
    r"adr-template|decision-record-template|madr)$"
)
_TEMPLATE_TEXT = re.compile(
    r"(?i)\b(?:template for (?:writing )?architecture decision|example repository|"
    r"awesome list|collection of architecture decision records|"
    r"tutorial on (?:how to )?(?:write|writing) adrs?)\b"
)
_SKIP_FILE = {
    "readme.md",
    "readme.markdown",
    "index.md",
    "template.md",
    "adr-template.md",
    "decision-template.md",
    "toc.md",
}


class GitError(RuntimeError):
    pass


def run_git(repo: str | None, args: list[str], timeout: int = 90, check: bool = True) -> str:
    cmd = ["git", *args]
    try:
        completed = subprocess.run(
            cmd,
            cwd=repo,
            text=True,
            capture_output=True,
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"timeout: git {' '.join(args[:4])}") from exc
    if check and completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()[:400]
        raise GitError(message or f"git {' '.join(args[:3])} failed")
    return completed.stdout


def clone_repo(url: str, dest: str, timeout: int = 180) -> None:
    if os.path.exists(dest):
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        subprocess.run(
            [
                "git",
                "-c",
                "http.lowSpeedLimit=2000",
                "-c",
                "http.lowSpeedTime=25",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                "--single-branch",
                url,
                dest,
            ],
            text=True,
            capture_output=True,
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            check=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError("clone timed out") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or "").strip()[:400]
        raise GitError(message or "clone failed") from exc


def is_candidate_path(path: str) -> bool:
    lowered = path.lower()
    if not lowered.endswith((".md", ".markdown", ".adoc", ".asciidoc", ".rst", ".txt")):
        return False
    base = lowered.rsplit("/", 1)[-1]
    if base in _SKIP_FILE:
        return False
    parts = lowered.split("/")
    if any(part in {"adr", "adrs", "architecture-decision-records", "architecture-decisions"} for part in parts):
        return True
    if re.search(r"(^|/)(docs/|doc/)?(architecture/)?decisions/", lowered):
        return True
    if re.search(r"(^|/)adr[-_]?\d+", lowered):
        return True
    return False


def looks_like_template(name: str, description: str) -> bool:
    if _TEMPLATE_NAME.search(name or ""):
        return True
    return bool(_TEMPLATE_TEXT.search(description or ""))


@dataclass
class _Version:
    sha: str
    date: str
    author: str
    email: str
    subject: str
    renamed: bool = False
    deleted: bool = False


def _split_commits(text: str) -> list[tuple[dict, list[str]]]:
    commits: list[tuple[dict, list[str]]] = []
    current: dict | None = None
    files: list[str] = []
    for line in text.splitlines():
        if line.startswith("COMMIT\x1f"):
            if current is not None:
                commits.append((current, files))
            parts = line[len("COMMIT\x1f"):].split("\x1f")
            # sha, date, author, email, subject, then optional body before \x1e
            raw_subject = parts[4] if len(parts) > 4 else ""
            subject, _, _rest = raw_subject.partition("\x1e")
            current = {
                "sha": parts[0] if parts else "",
                "date": parts[1] if len(parts) > 1 else "",
                "author": parts[2] if len(parts) > 2 else "",
                "email": parts[3] if len(parts) > 3 else "",
                "subject": subject,
            }
            files = []
            continue
        if current is None or not line.strip():
            continue
        files.append(line)
    if current is not None:
        commits.append((current, files))
    return commits


def _parse_name_status(line: str) -> tuple[str, str, str | None]:
    """Return action, path, old_path (for renames)."""
    parts = line.split("\t")
    action = parts[0]
    if action.startswith("R") or action.startswith("C"):
        old = parts[1] if len(parts) > 1 else ""
        new = parts[2] if len(parts) > 2 else old
        return action[:1], new, old
    path = parts[1] if len(parts) > 1 else ""
    return action[:1], path, None


def _cat_batch(repo: str, specs: list[str]) -> list[str | None]:
    """Read blobs without deadlocking the pipe.

    ``cat-file --batch`` writes a body for every request. Filling stdin before
    reading stdout blocks once the pipe buffer fills, which happens on any
    repository with more than a few dozen ADR versions.
    """
    if not specs:
        return []
    import threading

    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert proc.stdin and proc.stdout
    bodies: list[str | None] = []
    error: list[BaseException] = []

    def read_all() -> None:
        try:
            for _ in specs:
                header = proc.stdout.readline()
                if not header:
                    bodies.append(None)
                    continue
                if header.endswith(b" missing\n"):
                    bodies.append(None)
                    continue
                try:
                    size = int(header.split()[-1])
                except (ValueError, IndexError):
                    bodies.append(None)
                    continue
                blob = proc.stdout.read(size)
                proc.stdout.read(1)
                bodies.append(blob.decode("utf-8", "replace"))
        except BaseException as exc:  # noqa: BLE001 - reported to the caller
            error.append(exc)

    reader = threading.Thread(target=read_all, daemon=True)
    reader.start()
    try:
        proc.stdin.write(("\n".join(specs) + "\n").encode())
        proc.stdin.close()
        reader.join(timeout=180)
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
        if proc.stdout:
            proc.stdout.close()
    if error:
        raise GitError(f"cat-file failed: {error[0]}")
    if len(bodies) < len(specs):
        bodies.extend([None] * (len(specs) - len(bodies)))
    return bodies


def _history(repo: str, pathspecs: list[str], timeout: int = 90) -> list[tuple[dict, list[str]]]:
    if not pathspecs:
        return []
    text = run_git(
        repo,
        [
            "log",
            "--find-renames=30",
            "--name-status",
            "--pretty=format:COMMIT%x1f%H%x1f%aI%x1f%an%x1f%ae%x1f%s%x1e",
            "--",
            *pathspecs,
        ],
        timeout=timeout,
    )
    return _split_commits(text)


def _tracked_files(repo: str) -> list[str]:
    text = run_git(repo, ["ls-tree", "-r", "--name-only", "HEAD"], timeout=60)
    return [line for line in text.splitlines() if line.strip()]


def _repo_bounds(repo: str) -> tuple[str | None, str | None, int | None]:
    try:
        last = run_git(repo, ["log", "-1", "--pretty=%aI"], timeout=30).strip() or None
    except GitError:
        last = None
    try:
        roots = run_git(repo, ["rev-list", "--max-parents=0", "HEAD"], timeout=40).split()
        first = None
        if roots:
            first = run_git(repo, ["show", "-s", "--pretty=%aI", roots[-1]], timeout=30).strip() or None
    except GitError:
        first = None
    try:
        count = int(run_git(repo, ["rev-list", "--count", "HEAD"], timeout=60).strip() or "0")
    except GitError:
        count = None
    return first, last, count


def _author_count(repo: str) -> int | None:
    try:
        text = run_git(repo, ["log", "--pretty=%ae"], timeout=60)
    except GitError:
        return None
    return len({line.strip().lower() for line in text.splitlines() if line.strip()})


def analyze_clone(
    repo_dir: str,
    *,
    repo_name: str,
    description: str = "",
    extra_paths: list[str] | None = None,
) -> dict:
    """Measure a repository that is already cloned at ``repo_dir``."""
    files = _tracked_files(repo_dir)
    first_commit, last_commit, n_commits = _repo_bounds(repo_dir)
    n_authors = _author_count(repo_dir)
    template = looks_like_template(repo_name, description)

    pathspecs = list(ADR_PATHSPECS)
    for extra in extra_paths or []:
        extra = extra.strip().strip("/")
        if extra and extra not in pathspecs:
            pathspecs.append(extra)

    history = _history(repo_dir, pathspecs, timeout=120)
    # path -> chronological versions
    versions: dict[str, list[_Version]] = {}
    renames: list[tuple[str, str, _Version]] = []
    for commit, lines in history:
        version = _Version(
            sha=commit["sha"],
            date=commit["date"],
            author=commit["author"],
            email=commit["email"],
            subject=commit["subject"],
        )
        for line in lines:
            action, path, old = _parse_name_status(line)
            if not path:
                continue
            if action in {"A", "M", "T"} or action == "R" or action == "C":
                if is_candidate_path(path) or (old and is_candidate_path(old)):
                    versions.setdefault(path, []).append(
                        _Version(
                            version.sha,
                            version.date,
                            version.author,
                            version.email,
                            version.subject,
                            renamed=action in {"R", "C"},
                        )
                    )
                    if old and action in {"R", "C"}:
                        renames.append((old, path, version))
            elif action == "D" and (is_candidate_path(path) or path in versions):
                versions.setdefault(path, []).append(
                    _Version(
                        version.sha,
                        version.date,
                        version.author,
                        version.email,
                        version.subject,
                        deleted=True,
                    )
                )

    # Oldest first. git log is newest first.
    for path in versions:
        versions[path].sort(key=lambda item: (parse_dt(item.date) or parse_dt("1970-01-01T00:00:00+00:00"), item.sha))

    specs: list[str] = []
    spec_index: list[tuple[str, int]] = []
    for path, items in versions.items():
        for index, item in enumerate(items):
            if item.deleted:
                continue
            specs.append(f"{item.sha}:{path}")
            spec_index.append((path, index))
    # Cap pathological repositories that matched a broad docs tree.
    truncated = False
    if len(specs) > 800:
        truncated = True
        specs = specs[:800]
        spec_index = spec_index[:800]
    blobs = _cat_batch(repo_dir, specs)
    texts: dict[tuple[str, int], str] = {}
    for (path, index), blob in zip(spec_index, blobs):
        if blob is not None:
            texts[(path, index)] = blob

    # Follow renames so a moved ADR keeps one identity.
    parent: dict[str, str] = {}

    def root(path: str) -> str:
        while path in parent:
            path = parent[path]
        return path

    for old, new, _version in renames:
        if old in versions and new in versions:
            parent[new] = root(old) if root(old) != new else old

    adr_records: list[dict] = []
    changes: list[dict] = []
    seen_identity: set[str] = set()

    for path, items in versions.items():
        identity = root(path)
        # Keep the latest path of a renamed record as the canonical one.
        if identity != path and path != max(
            (candidate for candidate in versions if root(candidate) == identity),
            default=path,
        ):
            # Still walk it if it is the only path. Skip intermediate paths;
            # the newest path's history does not include pre-rename commits,
            # so we must merge. Handled below by grouping.
            continue
        seen_identity.add(identity)

    grouped: dict[str, list[tuple[str, _Version, str | None]]] = {}
    for path, items in versions.items():
        identity = root(path)
        for index, item in enumerate(items):
            grouped.setdefault(identity, []).append((path, item, texts.get((path, index))))

    for identity, events in grouped.items():
        events.sort(key=lambda item: (parse_dt(item[1].date) or parse_dt("1970-01-01T00:00:00+00:00"), item[1].sha))
        canonical_path = events[-1][0]
        last_text = ""
        for _path, _item, blob in reversed(events):
            if blob:
                last_text = blob
                canonical_path = _path
                break
        if not last_text and not any(item[1].deleted for item in events):
            continue
        # Require ADR shape, not every markdown file under docs/architecture.
        sample = last_text or ""
        if sample and parse_status(sample).state == "unknown" and "architecture decision" not in sample.lower():
            if not re.search(r"(?i)(^|/)(adr|adrs)/", canonical_path) and "adr" not in os.path.basename(canonical_path).lower():
                if not re.search(r"(?i)## (context|decision)\b", sample):
                    continue
        born = next((item for item in events if not item[1].deleted), None)
        if born is None:
            continue
        status = parse_status(last_text)
        record = {
            "path": canonical_path,
            "identity": identity,
            "adr_id": adr_identifier(canonical_path),
            "title": adr_title(last_text),
            "first_commit": born[1].date,
            "first_sha": born[1].sha,
            "last_commit": events[-1][1].date,
            "author": born[1].author,
            "email": born[1].email,
            "status": status.state,
            "status_raw": status.raw,
            "replacement": status.replacement,
            "n_commits": len({item[1].sha for item in events}),
            "text": (last_text or "")[:12000],
            "truncated_text": len(last_text or "") > 12000,
        }
        previous: tuple[str, str] | None = None
        for path, item, blob in events:
            if item.deleted:
                ending = classify_ending(
                    previous[0] if previous else "unknown",
                    previous[0] if previous else "unknown",
                    old_raw=previous[1] if previous else "",
                    message=item.subject,
                    deleted=True,
                    renamed=False,
                )
                if previous is not None:
                    changes.append(
                        {
                            "path": path,
                            "identity": identity,
                            "commit": item.sha,
                            "date": item.date,
                            "old_state": previous[0],
                            "new_state": "deleted",
                            "old_raw": previous[1],
                            "new_raw": "",
                            "replacement": None,
                            "message": item.subject,
                            "renamed": False,
                            "script_label": ending.label,
                            "script_rule": ending.rule,
                            "author": item.author,
                            "email": item.email,
                        }
                    )
                continue
            if not blob:
                continue
            parsed = parse_status(blob)
            if previous is None:
                previous = (parsed.state, parsed.raw)
                continue
            if parsed.state == previous[0] and (parsed.raw == previous[1] or parsed.state == "unknown"):
                if item.renamed:
                    ending = classify_ending(
                        previous[0],
                        parsed.state,
                        old_raw=previous[1],
                        new_raw=parsed.raw,
                        message=item.subject,
                        replacement=parsed.replacement,
                        renamed=True,
                    )
                    changes.append(
                        {
                            "path": path,
                            "identity": identity,
                            "commit": item.sha,
                            "date": item.date,
                            "old_state": previous[0],
                            "new_state": parsed.state,
                            "old_raw": previous[1],
                            "new_raw": parsed.raw,
                            "replacement": parsed.replacement,
                            "message": item.subject,
                            "renamed": True,
                            "script_label": ending.label,
                            "script_rule": ending.rule,
                            "author": item.author,
                            "email": item.email,
                        }
                    )
                previous = (parsed.state, parsed.raw)
                continue
            if parsed.state != previous[0]:
                ending = classify_ending(
                    previous[0],
                    parsed.state,
                    old_raw=previous[1],
                    new_raw=parsed.raw,
                    message=item.subject,
                    replacement=parsed.replacement,
                    renamed=item.renamed,
                )
                changes.append(
                    {
                        "path": path,
                        "identity": identity,
                        "commit": item.sha,
                        "date": item.date,
                        "old_state": previous[0],
                        "new_state": parsed.state,
                        "old_raw": previous[1],
                        "new_raw": parsed.raw,
                        "replacement": parsed.replacement,
                        "message": item.subject,
                        "renamed": item.renamed,
                        "script_label": ending.label,
                        "script_rule": ending.rule,
                        "author": item.author,
                        "email": item.email,
                    }
                )
            previous = (parsed.state, parsed.raw)
        record["discussion_refs"] = extract_discussion_refs(last_text)
        record["mentioned_paths"] = extract_paths(last_text)
        adr_records.append(record)

    signal_events = _signal_events(repo_dir)
    signal_dates = [parse_dt(event["date"]) for event in signal_events if event["official"]]
    signal_dates = [item for item in signal_dates if item is not None]
    signal_date = min(signal_dates).isoformat() if signal_dates else None
    signal_kind = None
    if signal_date:
        for event in sorted(signal_events, key=lambda item: item["date"] or ""):
            if event["official"] and event["date"] and parse_dt(event["date"]) == min(signal_dates):
                signal_kind = event["kind"]
                break

    mentions = _mention_sample(repo_dir)

    # Implementation commits. One log for every path named by an ADR.
    named: list[str] = []
    for record in adr_records:
        for path in record["mentioned_paths"]:
            if path not in named:
                named.append(path)
        if len(named) >= 60:
            break
    code_commits = _code_commits(repo_dir, named) if named else []
    message_commits = _adr_message_commits(repo_dir)
    combined = _merge_commits(code_commits, message_commits)
    for record in adr_records:
        token = record["adr_id"]
        hit = pick_implementation(
            record["first_commit"],
            record["path"],
            record["mentioned_paths"],
            token,
            combined,
        )
        record["implementation"] = {
            "sha": hit.sha,
            "date": hit.date,
            "subject": hit.subject,
            "reason": hit.reason,
            "paths": list(hit.paths),
        }

    superseded_flags = [record["status"] == "superseded" for record in adr_records]
    eligibility = classify_project(
        adr_dates=[record["first_commit"] for record in adr_records],
        superseded_flags=superseded_flags,
        signal_date=signal_date,
        likely_template=template,
        clone_ok=True,
    )
    code_ext = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rs", ".rb", ".php",
        ".cs", ".c", ".cc", ".cpp", ".kt", ".scala", ".swift",
    }
    n_code = sum(1 for path in files if os.path.splitext(path)[1].lower() in code_ext)
    return {
        "repo": repo_name,
        "clone_ok": True,
        "error": None,
        "description": description,
        "first_commit": first_commit,
        "last_commit": last_commit,
        "n_commits": n_commits,
        "n_authors": n_authors,
        "n_files": len(files),
        "n_code_files": n_code,
        "likely_template": template,
        "history_truncated": truncated,
        "adr_count": len(adr_records),
        "adrs": adr_records,
        "status_changes": changes,
        "ai_signals": signal_events,
        "signal_date": signal_date,
        "signal_kind": signal_kind,
        "mentions": mentions,
        "group": eligibility.group,
        "adr_count_before_signal": eligibility.adr_count_before_signal,
        "superseded_in_window": eligibility.superseded,
        "eligibility_reason": eligibility.reason,
    }


def _safe_git(repo: str, args: list[str], timeout: int = 60) -> str:
    try:
        return run_git(repo, args, timeout=timeout, check=False)
    except GitError:
        return ""


def _signal_events(repo: str) -> list[dict]:
    history = _history(repo, SIGNAL_PATHSPECS, timeout=90)
    events: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for commit, lines in reversed(history):
        for line in lines:
            action, path, _old = _parse_name_status(line)
            if action not in {"A", "C", "R", "M"}:
                continue
            kind = classify_signal_path(path)
            if not kind:
                continue
            key = (kind, path)
            if key in seen:
                continue
            seen.add(key)
            events.append(
                {
                    "kind": f"file:{kind}",
                    "name": path,
                    "date": commit["date"],
                    "commit": commit["sha"],
                    "evidence": commit["subject"],
                    "official": kind == "primary",
                    "author": commit["author"],
                    "email": commit["email"],
                }
            )
    coauthor_text = _safe_git(
        repo,
        [
            "log",
            "--reverse",
            "-i",
            "--extended-regexp",
            "--grep=Co-authored-by:.*(copilot|claude|chatgpt|cursor|devin|codeium|aider|openhands|codegen|gemini)",
            "--pretty=format:COMMIT%x1f%H%x1f%aI%x1f%an%x1f%ae%x1f%s%x1e%n%b%x1e",
        ],
        timeout=90,
    )
    for block in coauthor_text.split("COMMIT\x1f")[1:]:
        head, _, body = block.partition("\x1e")
        parts = head.split("\x1f")
        if len(parts) < 5:
            continue
        hits = ai_coauthor_hits(body)
        if not hits:
            continue
        events.append(
            {
                "kind": "coauthor",
                "name": hits[0],
                "date": parts[1],
                "commit": parts[0],
                "evidence": parts[4][:200],
                "official": True,
                "author": parts[2],
                "email": parts[3],
            }
        )
    author_text = _safe_git(
        repo,
        [
            "log",
            "--reverse",
            "-i",
            "--extended-regexp",
            "--author=copilot|claude|cursor|devin|codeium|openhands|chatgpt|aider",
            "--pretty=format:%H%x1f%aI%x1f%an%x1f%ae%x1f%s%x1e",
        ],
        timeout=90,
    )
    for line in author_text.splitlines():
        parts = line.split("\x1f")
        if len(parts) < 5:
            continue
        subject, _, _rest = parts[4].partition("\x1e")
        if not is_agent_author(parts[2], parts[3]):
            continue
        events.append(
            {
                "kind": "agent-author",
                "name": f"{parts[2]} <{parts[3]}>",
                "date": parts[1],
                "commit": parts[0],
                "evidence": subject[:200],
                "official": True,
                "author": parts[2],
                "email": parts[3],
            }
        )
    return events


def _mention_sample(repo: str) -> dict:
    text = _safe_git(
        repo,
        [
            "log",
            "--reverse",
            "-i",
            "--extended-regexp",
            "--grep=copilot|chatgpt|claude|cursor",
            "--pretty=format:%H%x1f%aI%x1f%s%x1e",
        ],
        timeout=90,
    )
    strict: list[dict] = []
    strict_count = 0
    literal = 0
    capped = False
    for line in text.splitlines():
        parts = line.split("\x1f")
        if len(parts) < 3:
            continue
        subject = parts[2].partition("\x1e")[0]
        kind = mention_kind(subject)
        if kind == "strict":
            strict_count += 1
            if len(strict) < 12:
                strict.append({"sha": parts[0], "date": parts[1], "subject": subject[:200]})
        elif kind == "literal-only":
            literal += 1
        if strict_count + literal > 500:
            capped = True
            break
    return {
        "strict": strict,
        "strict_count": strict_count,
        "literal_only_count": literal,
        "capped": capped,
    }


def _code_commits(repo: str, paths: list[str]) -> list[dict]:
    if not paths:
        return []
    text = run_git(
        repo,
        [
            "log",
            "--name-only",
            "--pretty=format:COMMIT%x1f%H%x1f%aI%x1f%s%x1e",
            "-n",
            "400",
            "--",
            *paths,
        ],
        timeout=60,
        check=False,
    )
    commits: list[dict] = []
    for commit, files in _split_commits(text):
        cleaned = []
        for line in files:
            path = line.split("\t")[-1].strip()
            if path and not path.startswith("COMMIT"):
                cleaned.append(path)
        commits.append({**commit, "files": cleaned})
    commits.sort(key=lambda item: item.get("date") or "")
    return commits


def _adr_message_commits(repo: str) -> list[dict]:
    text = run_git(
        repo,
        [
            "log",
            "-i",
            "--extended-regexp",
            "--grep=ADR[- ]?[0-9]|adr/",
            "--name-only",
            "--pretty=format:COMMIT%x1f%H%x1f%aI%x1f%s%x1e",
            "-n",
            "250",
        ],
        timeout=60,
        check=False,
    )
    commits = []
    for commit, files in _split_commits(text):
        cleaned = [line.split("\t")[-1].strip() for line in files if line.strip()]
        commits.append({**commit, "files": cleaned})
    commits.sort(key=lambda item: item.get("date") or "")
    return commits


def _merge_commits(*groups: list[dict]) -> list[dict]:
    by_sha: dict[str, dict] = {}
    for group in groups:
        for commit in group:
            sha = commit.get("sha") or ""
            if not sha:
                continue
            current = by_sha.setdefault(sha, {**commit, "files": []})
            for path in commit.get("files") or []:
                if path not in current["files"]:
                    current["files"].append(path)
    merged = list(by_sha.values())
    merged.sort(key=lambda item: item.get("date") or "")
    return merged
