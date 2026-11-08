"""Classify a change in ADR status.

Four labels, matching the pilot guide:

- replaced: a new decision takes the place of this one
- no-longer-needed: the decision was dropped, deprecated, or became obsolete
- rejected-before-use: the proposal was turned down before it was accepted
- cleanup-or-rename: renumbering, moving, or a wording-only edit
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from adr_pilot.status import find_replacement

LABELS = (
    "replaced",
    "no-longer-needed",
    "rejected-before-use",
    "cleanup-or-rename",
)

_RENAME_MESSAGE = re.compile(
    r"(?i)\b(?:renumber|re-number|rename|renamed|move[sd]?|moving|relocate|"
    r"restructur\w*|fix(?:ed)? (?:the )?(?:adr )?number|typo|spelling|"
    r"reformat|whitespace|link fix|fix links?)\b"
)
_DROP_MESSAGE = re.compile(
    r"(?i)\b(?:no longer (?:needed|used|relevant)|obsolete|abandon\w*|"
    r"retir(?:e|ed|ing)|deprecat\w*|remove[sd]? the (?:adr|decision)|"
    r"drop(?:ped)? the (?:adr|decision)|withdrawn?)\b"
)
_REPLACE_MESSAGE = re.compile(
    r"(?i)\b(?:supersed\w*|replac(?:e|ed|ing)|split into|rewritten as|"
    r"see adr[- ]?\d+)\b"
)
_CLEANUP_TEXT = re.compile(
    r"(?i)\b(?:renumber|re-number|rename[d]?|moved to|duplicate of|"
    r"editorial|wording only|same decision)\b"
)
_DROP_TEXT = re.compile(
    r"(?i)\b(?:no longer (?:needed|used|relevant)|obsolete|not used|"
    r"never used|feature (?:was )?removed|withdrawn?)\b"
)


@dataclass(frozen=True)
class Ending:
    label: str
    rule: str


def classify_ending(
    old_state: str | None,
    new_state: str | None,
    *,
    new_raw: str = "",
    old_raw: str = "",
    message: str = "",
    replacement: str | None = None,
    renamed: bool = False,
    deleted: bool = False,
) -> Ending:
    """Return the script label for one status transition.

    ``old_state`` is None when this is the first version of the file. Callers
    that only want real changes should skip that case. This function still
    classifies it, as ``cleanup-or-rename`` when nothing ended.
    """
    old = old_state or "unknown"
    new = new_state or "unknown"
    raw = f"{new_raw}\n{message}"
    if new == "deleted":
        deleted = True

    if deleted and renamed:
        renamed = True
        deleted = False

    pointer = replacement or find_replacement(new_raw) or find_replacement(message)

    if renamed and (old == new or new in {"unknown", old}):
        return Ending("cleanup-or-rename", "rename-without-status-change")

    if deleted:
        if pointer:
            return Ending("replaced", "deleted-with-replacement")
        if _DROP_MESSAGE.search(message):
            return Ending("no-longer-needed", "deleted-as-obsolete")
        return Ending("cleanup-or-rename", "deleted-without-replacement-pointer")

    if old == new:
        return Ending("cleanup-or-rename", "status-unchanged")

    if new == "rejected":
        if pointer:
            return Ending("replaced", "rejected-but-points-at-replacement")
        if old in {"accepted", "deprecated", "superseded"}:
            return Ending("no-longer-needed", "rejected-after-acceptance")
        return Ending("rejected-before-use", "rejected-from-proposal")

    if new == "deprecated":
        if pointer:
            return Ending("replaced", "deprecated-but-points-at-replacement")
        return Ending("no-longer-needed", "deprecated")

    if new == "superseded":
        if _CLEANUP_TEXT.search(raw) and not pointer:
            return Ending("cleanup-or-rename", "superseded-wording-is-a-rename")
        if _DROP_TEXT.search(raw) and not pointer:
            return Ending("no-longer-needed", "superseded-means-obsolete")
        if pointer or _REPLACE_MESSAGE.search(new_raw):
            return Ending("replaced", "superseded-by-pointer")
        return Ending("replaced", "superseded-default")

    if new in {"accepted", "proposed", "unknown"} and old in {"proposed", "unknown", "accepted"}:
        if _RENAME_MESSAGE.search(message) or renamed:
            return Ending("cleanup-or-rename", "accepted-during-cleanup")
        # proposed -> accepted is adoption, not an ending of a prior decision.
        return Ending("cleanup-or-rename", "not-an-ending")

    if _RENAME_MESSAGE.search(message) and not pointer:
        return Ending("cleanup-or-rename", "message-says-rename")

    return Ending("cleanup-or-rename", "unclassified-status-edit")
