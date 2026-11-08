"""AI adoption for the library-swap sample.

Instruction files still come from the ADR pilot. Names and emails do not.
A commit counts only when its author name, author email, or co-author name
or email is an exact entry in the allowlist in config.yaml.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2] / "adr-feasibility"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from adr_pilot.analyze import _signal_events  # noqa: E402
from adr_pilot.report import adoption_event  # noqa: E402

from swap_pilot.config import load_config

_KIND = {
    "file:primary": "instruction file",
    "coauthor": "co-author",
    "agent-author": "agent author",
}

_COAUTHOR = re.compile(
    r"(?im)^[ \t]*co-authored-by:[ \t]*(?P<name>.*?)"
    r"(?:[ \t]*<(?P<email>[^>\n]+)>)?[ \t]*$"
)

_CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"
_ALLOW: tuple[set[str], set[str]] | None = None


def allowlists(config: dict | None = None) -> tuple[set[str], set[str]]:
    """Exact bot names and exact co-author emails, compared case-insensitively."""
    global _ALLOW
    if config is None and _ALLOW is not None:
        return _ALLOW
    loaded = config if config is not None else load_config(_CONFIG)
    names = {str(item).strip().casefold() for item in loaded.get("ai_bot_names") or [] if str(item).strip()}
    emails = {str(item).strip().casefold() for item in loaded.get("ai_coauthor_emails") or [] if str(item).strip()}
    if config is None:
        _ALLOW = (names, emails)
    return names, emails


def identity_allowed(name: str | None, email: str | None, names: set[str], emails: set[str]) -> bool:
    """True only when the whole name or the whole email is on the allowlist."""
    candidate_name = (name or "").strip().casefold()
    candidate_email = (email or "").strip().casefold()
    if candidate_name and candidate_name in names:
        return True
    if candidate_email and candidate_email in emails:
        return True
    return False


def coauthor_allowed(message: str | None, names: set[str], emails: set[str]) -> bool:
    for match in _COAUTHOR.finditer(message or ""):
        if identity_allowed(match.group("name"), match.group("email"), names, emails):
            return True
    return False


def event_allowed(event: dict, names: set[str] | None = None, emails: set[str] | None = None) -> bool:
    if names is None or emails is None:
        names, emails = allowlists()
    kind = str(event.get("kind") or "")
    if kind == "file:primary":
        return True
    if kind == "coauthor":
        return coauthor_allowed(event.get("name") or "", names, emails)
    if kind == "agent-author":
        return identity_allowed(event.get("author"), event.get("email"), names, emails)
    return False


def adoption(repo_dir: str) -> dict:
    """Return ai_signal, adoption_date, and signal_type.

    adoption_date is empty when there is no strong signal. It is never zero.
    """
    names, emails = allowlists()
    events = [event for event in _signal_events(repo_dir) if event_allowed(event, names, emails)]
    chosen = adoption_event({"ai_signals": events})
    if chosen is None:
        return {"ai_signal": "no", "adoption_date": "", "signal_type": ""}
    when, event = chosen
    kind = str(event.get("kind") or "")
    return {
        "ai_signal": "yes",
        "adoption_date": when.isoformat(),
        "signal_type": _KIND.get(kind, kind),
    }


def commit_is_ai(author: str, email: str, message: str) -> bool:
    names, emails = allowlists()
    if identity_allowed(author, email, names, emails):
        return True
    return coauthor_allowed(message, names, emails)
