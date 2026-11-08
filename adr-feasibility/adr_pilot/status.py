"""Parse the status of an Architecture Decision Record.

The parser is deliberately conservative. Template legends ("proposed, accepted,
rejected, deprecated, superseded") and unchecked option lists are not statuses.
A decision counts as superseded only when the status block says so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

STATES = ("proposed", "accepted", "rejected", "deprecated", "superseded", "unknown")

_FRONT_MATTER = re.compile(r"(?s)\A---\s*\n(.*?)\n---\s*\n")
_STATUS_LABEL = re.compile(
    r"(?im)^[ \t]{0,3}(?:#{1,6}[ \t]*)?(?:\*\*|__)?status(?:\*\*|__)?[ \t]*[:：][ \t]*(.*)$"
)
_STATUS_HEADING = re.compile(r"(?im)^[ \t]{0,3}#{1,6}[ \t]*(?:\*\*)?status(?:\*\*)?[ \t]*$")
_NEXT_HEADING = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+\S")
_CHECKED = re.compile(r"(?i)\[(?:x|X|✓)\][ \t]*([A-Za-z][^\]\n]{0,60})")
_BADGE = re.compile(
    r"(?i)badge/adr-([a-z]+)|shields\.io/badge/[^)]*?([a-z]+)-(?:green|red|yellow|blue|orange)"
)
_REPLACEMENT = re.compile(
    r"(?is)\b(?:superseded|replaced|superceded|supersedes)\s+by\s+"
    r"(?:\[(?P<label>[^\]]+)\]\((?P<url>[^)]+)\)|(?P<plain>[^.\n]{1,160}))"
)
_LEGEND = re.compile(
    r"(?is)what is the status|such as proposed|e\.g\.\s*proposed|"
    r"proposed\s*[,/|]\s*accepted\s*[,/|]\s*(?:rejected|deprecated)"
)

# First lifecycle word wins. A later word must not override it: "proposed, not
# implemented yet" is still proposed. Negated words ("not implemented") are skipped.
_STATE_WORD = re.compile(
    r"(?i)\b(?P<neg>not(?:\s+yet)?\s+)?(?P<word>superseded|superceded|replaced|"
    r"deprecated|obsolete|retired|abandoned|rejected|declined|refused|"
    r"accepted|approved|implemented|active|adopted|proposed|proposal|draft|pending)\b"
)
_STATE_OF_WORD = {
    "superseded": "superseded",
    "superceded": "superseded",
    "replaced": "superseded",
    "deprecated": "deprecated",
    "obsolete": "deprecated",
    "retired": "deprecated",
    "abandoned": "deprecated",
    "rejected": "rejected",
    "declined": "rejected",
    "refused": "rejected",
    "accepted": "accepted",
    "approved": "accepted",
    "implemented": "accepted",
    "active": "accepted",
    "adopted": "accepted",
    "proposed": "proposed",
    "proposal": "proposed",
    "draft": "proposed",
    "pending": "proposed",
}


@dataclass(frozen=True)
class Status:
    state: str
    raw: str
    replacement: str | None
    filled: bool

    @property
    def is_known(self) -> bool:
        return self.state != "unknown"


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_comments(text: str) -> str:
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"(?m)^[ \t]*<!---.*?--->[ \t]*$", " ", text)
    return text


def _replacement_from(text: str) -> str | None:
    match = _REPLACEMENT.search(text)
    if not match:
        return None
    if match.group("label"):
        label = _collapse(match.group("label"))
        url = _collapse(match.group("url") or "")
        return f"{label} ({url})" if url else label
    plain = _collapse(match.group("plain") or "")
    return plain or None


def _state_from_phrase(phrase: str) -> str:
    # "Accepted. Superseded by ADR-0004" is a replaced decision, not an
    # accepted one. The pointer is the current state.
    if re.search(r"(?i)\b(?:superseded|superceded|replaced)\s+by\b", phrase or ""):
        return "superseded"
    for match in _STATE_WORD.finditer(phrase or ""):
        if match.group("neg"):
            continue
        state = _STATE_OF_WORD.get(match.group("word").lower())
        if state:
            return state
    badge = _BADGE.search(phrase or "")
    if badge:
        word = next(group for group in badge.groups() if group)
        return _state_from_phrase(word)
    return "unknown"


def _from_block(block: str) -> Status:
    raw_block = _collapse(block)[:500]
    if not raw_block:
        return Status("unknown", "", None, False)
    if _LEGEND.search(block) and "[x]" not in block.lower() and "[X]" not in block:
        return Status("unknown", raw_block, None, False)
    checked = _CHECKED.findall(block)
    if checked:
        # The last checked box wins when a template ticks one option.
        phrase = checked[-1]
        state = _state_from_phrase(phrase)
        replacement = _replacement_from(block) if state == "superseded" else _replacement_from(phrase)
        if state == "superseded" and replacement is None:
            replacement = _replacement_from(block)
        return Status(state, _collapse(phrase)[:300], replacement, state != "unknown")
    # Ignore an unfilled option menu that mentions every lifecycle word.
    words = {state for state in ("proposed", "accepted", "rejected", "deprecated", "superseded") if re.search(rf"(?i)\b{state}", block)}
    if words >= {"proposed", "accepted", "rejected", "superseded"} and " by " not in block.lower():
        return Status("unknown", raw_block, None, False)
    state = _state_from_phrase(block)
    replacement = _replacement_from(block) if state == "superseded" else None
    filled = state != "unknown"
    return Status(state, raw_block[:300], replacement, filled)


def _front_matter_status(text: str) -> str | None:
    match = _FRONT_MATTER.search(text)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if re.match(r"(?i)^status\s*:", line):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def _status_region(text: str) -> str | None:
    """Return the status block.

    A ``## Status`` heading counts wherever it sits. Tendermint-style records
    put it after a long decision section, well past the first screen. Lines
    inside fenced code blocks are ignored. A same-line ``Status:`` label is
    only trusted near the top, which is where the templates put it.
    """
    lines = text.splitlines()
    fenced = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            continue
        if fenced or not _STATUS_HEADING.match(line):
            continue
        block: list[str] = []
        for nxt in lines[index + 1 : index + 40]:
            if nxt.strip().startswith("```"):
                break
            if _NEXT_HEADING.match(nxt):
                break
            block.append(nxt)
        return "\n".join(block)[:800]
    head = "\n".join(lines[:120])
    label = _STATUS_LABEL.search(head)
    if not label:
        return None
    extra = []
    # The label regex consumes the rest of its own line. Following lines may wrap.
    rest = head[label.end():]
    for line in rest.splitlines()[:6]:
        if not line.strip() or _NEXT_HEADING.match(line) or _STATUS_HEADING.match(line):
            break
        extra.append(line)
    return "\n".join([label.group(1), *extra])


def parse_status(text: str | None) -> Status:
    """Parse the lifecycle status written in an ADR."""
    if not text or not text.strip():
        return Status("unknown", "", None, False)
    cleaned = _strip_comments(text)
    front = _front_matter_status(cleaned)
    if front:
        parsed = _from_block(front)
        if parsed.filled or parsed.replacement:
            return parsed
    region = _status_region(cleaned)
    if region is not None:
        return _from_block(region)
    return Status("unknown", "", None, False)


def adr_title(text: str | None) -> str:
    if not text:
        return ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = re.sub(r"^#+\s*", "", stripped)
            title = re.sub(r"^\d+[.)\s:-]*", "", title).strip()
            return title[:200]
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:200]
    return ""


def adr_identifier(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    match = re.search(r"(?i)(?:adr[-_]?)?(\d{3,5})", name)
    if match:
        return match.group(1).lstrip("0") or "0"
    return ""
