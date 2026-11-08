"""AI-adoption signals.

Official signals follow the study plan: agent instruction files
(AGENTS.md, CLAUDE.md, .cursorrules, copilot-instructions.md),
AI co-author trailers, and commits authored by AI coding agents.

A mention of the word "cursor" in a commit message is not, by itself, an
official adoption signal. Check 2 searches those words separately when it
looks for hidden use.
"""

from __future__ import annotations

import re

PRIMARY_FILE_NAMES = {
    "claude.md",
    "claude.local.md",
    "agents.md",
    "agents.override.md",
    ".cursorrules",
    "copilot-instructions.md",
}

# Secondary path fragments. Matched against the whole path.
SECONDARY_PATH_FRAGMENTS = (
    "/.cursor/rules/",
    "/.github/agents/",
    "/.windsurf/",
)

_VENDOR = re.compile(
    r"(?i)(?:^|/)(?:vendor|third_party|third-party|node_modules|external|"
    r"site-packages|dist-packages)/"
)

_COAUTHOR = re.compile(
    r"(?im)^[ \t]*co-authored-by:[ \t]*(?P<name>.*?)"
    r"(?:[ \t]*<(?P<email>[^>\n]+)>)?[ \t]*$"
)

_TOOL_EMAIL = re.compile(
    r"(?i)(copilot|chatgpt|codeium|devin\.ai|openhands|aider@|cursor\.com|"
    r"anthropic\.com|gemini-code|amazon-q|q-developer|codegen)"
)
_TOOL_NAME = re.compile(
    r"(?i)^(copilot|claude|chatgpt|devin|codeium|cursor|cursor agent|"
    r"github copilot|amazon q|aider|openhands|codegen|gemini code assist)$"
)
_NOT_AI = re.compile(r"(?i)dependabot|renovate|greenkeeper|pyup|snyk-bot|imgbot|allcontributors")

# Check 2 hidden-use search. Bare "cursor" is too common (UI cursor, DB cursor).
# "composer" is also a UI widget, so it does not count as Cursor the editor.
_CURSOR_FALSE = re.compile(r"(?i)\bcursor\s+(?:position|offset|index|row|column|pointer)\b")
_MENTION = re.compile(
    r"(?i)(\bgithub copilot\b|\bcopilot\b|\bchatgpt\b|\bclaude\b|"
    r"\bcursor\b.{0,24}\b(?:ai|agent|rules|ide)\b|"
    r"\b(?:ai coding|coding agent)\b.{0,24}\bcursor\b)"
)
_MENTION_LITERAL = re.compile(r"(?i)\b(copilot|claude|cursor|chatgpt)\b")


def is_vendor_path(path: str) -> bool:
    return bool(_VENDOR.search(path.replace("\\", "/")))


def classify_signal_path(path: str) -> str | None:
    """Return 'primary', 'secondary', or None for an instruction-file path."""
    if is_vendor_path(path):
        return None
    name = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if name in PRIMARY_FILE_NAMES:
        return "primary"
    lowered = "/" + path.replace("\\", "/").lower().lstrip("/")
    if any(fragment in lowered for fragment in SECONDARY_PATH_FRAGMENTS):
        return "secondary"
    if name in {"gemini.md", ".windsurfrules"}:
        return "secondary"
    return None


def ai_coauthor_hits(message: str) -> list[str]:
    """Return the co-author lines that are AI tools, not human names."""
    if not message or _NOT_AI.search(message):
        # A message can mix a bot and a human. Filter per line instead.
        pass
    hits: list[str] = []
    for match in _COAUTHOR.finditer(message or ""):
        line = match.group(0).strip()
        if _NOT_AI.search(line):
            continue
        name = re.sub(r"\s+", " ", (match.group("name") or "")).strip()
        email = (match.group("email") or "").strip()
        if _TOOL_NAME.match(name) or _TOOL_EMAIL.search(email) or "[bot]" in name.lower():
            if re.search(r"(?i)copilot|claude|chatgpt|cursor|devin|codeium|aider|openhands|codegen|gemini|amazon q", name + " " + email):
                hits.append(line)
    return hits


def is_agent_author(name: str, email: str) -> bool:
    blob = f"{name} {email}"
    if _NOT_AI.search(blob):
        return False
    if _TOOL_NAME.match(name.strip()) or _TOOL_EMAIL.search(email or ""):
        return True
    if "[bot]" in (name or "").lower() and re.search(
        r"(?i)copilot|claude|cursor|devin|codeium|codegen|aider|openhands", blob
    ):
        return True
    return False


def mention_kind(text: str) -> str | None:
    """Classify a commit message for the hidden-use search.

    Returns 'strict', 'literal-only', or None. 'literal-only' means the
    message contains cursor/claude/copilot/chatgpt but not the stricter
    pattern (for example a database cursor). Check 2 counts strict hits.
    """
    if not text:
        return None
    if _CURSOR_FALSE.search(text) and not re.search(r"(?i)\b(copilot|chatgpt|claude)\b", text):
        return "literal-only"
    if _MENTION.search(text):
        return "strict"
    if _MENTION_LITERAL.search(text):
        return "literal-only"
    return None
