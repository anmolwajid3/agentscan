"""AI adoption, using the ADR pilot's rule without changing it."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2] / "adr-feasibility"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from adr_pilot.analyze import _signal_events  # noqa: E402
from adr_pilot.report import adoption_event  # noqa: E402
from adr_pilot.signals import ai_coauthor_hits, is_agent_author  # noqa: E402

_KIND = {
    "file:primary": "instruction file",
    "coauthor": "co-author",
    "agent-author": "agent author",
}


def adoption(repo_dir: str) -> dict:
    """Return ai_signal, adoption_date, and signal_type.

    adoption_date is empty when there is no strong signal. It is never zero.
    """
    events = _signal_events(repo_dir)
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
    if is_agent_author(author, email):
        return True
    return bool(ai_coauthor_hits(message))
