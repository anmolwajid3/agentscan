"""Rules for superseded ADR pairs and for matching implementing commits.

The status parser is the one in adr-feasibility. This module adds the link
rule for the fresh candidate list: a markdown link to another ADR is a pair
only from the status section, or from a sentence that says the decision was
superseded, replaced, or deprecated.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath

_ADR = Path(__file__).resolve().parents[1] / "adr-feasibility"
if str(_ADR) not in sys.path:
    sys.path.insert(0, str(_ADR))

from adr_pilot.status import (
    _front_matter_status,
    _status_region,
    adr_identifier,
    adr_title,
    find_replacement,
    parse_status,
)

LINK = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<url>[^)\s]+)\)")
WORDING = re.compile(r"(?i)\b(?:supersed\w*|superced\w*|replac\w*|deprecat\w*)\b")
SENTENCE_GAP = re.compile(r"[.!?\n]+")
ADR_FILE = re.compile(
    r"(?i)(?:^|/)(?:"
    r"docs/adr|doc/adr|docs/adrs|doc/adrs|docs/decisions|doc/decisions|"
    r"architecture/decisions|docs/architecture/decisions|doc/architecture/decisions|"
    r"adr|adrs"
    r")/[^/]+\.md$"
)
SKIP_NAMES = {
    "readme.md",
    "readme.markdown",
    "index.md",
    "template.md",
    "adr-template.md",
    "decision-template.md",
}
STOPWORDS = {
    "about", "after", "again", "also", "and", "are", "because", "been", "before",
    "being", "between", "both", "but", "can", "could", "decision", "decisions",
    "does", "each", "for", "from", "have", "into", "more", "most", "not", "only",
    "other", "our", "over", "record", "records", "should", "some", "such", "than",
    "that", "the", "their", "then", "there", "these", "this", "those", "through",
    "under", "use", "used", "using", "with", "within", "without", "would",
    "accepted", "architecture", "deprecated", "proposed", "replaced", "status",
    "superseded", "superceded",
}
TECHNOLOGIES = (
    "postgres", "postgresql", "mysql", "mariadb", "sqlite", "mongodb", "redis",
    "memcached", "elasticsearch", "opensearch", "kafka", "rabbitmq", "activemq",
    "nats", "grpc", "graphql", "protobuf", "avro", "thrift", "kubernetes",
    "docker", "helm", "terraform", "ansible", "dynamodb", "firestore", "bigquery",
    "snowflake", "react", "angular", "vue", "svelte", "spring", "hibernate",
    "django", "flask", "fastapi", "rails", "laravel", "express", "nestjs",
    "micronaut", "quarkus", "webpack", "vite", "junit", "pytest", "testng",
    "maven", "gradle", "nginx", "envoy", "oauth", "oidc", "saml", "pulsar",
    "cassandra", "couchdb", "neo4j", "websocket", "log4j", "logback", "slf4j",
    "jackson", "jaxb", "flyway", "liquibase", "mockito", "hikari",
)
CONFIG_MARKERS = (
    "pom.xml", "build.gradle", "build.gradle.kts", "package.json", "go.mod",
    "cargo.toml", "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
    "composer.json", "gemfile", ".csproj", "application.yml", "application.yaml",
    "application.properties", "docker-compose", "dockerfile",
)
SCHEMA_MARKERS = ("migration", "migrate", "schema", "flyway", "liquibase", ".sql")
CODE_EXT = {
    ".java", ".kt", ".kts", ".scala", ".groovy", ".py", ".go", ".rs", ".js",
    ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".cs", ".fs", ".vb", ".rb", ".php",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".ex", ".exs", ".clj", ".xml",
    ".yml", ".yaml", ".json", ".toml", ".properties", ".sql", ".gradle",
}
BUILD_FILES = (
    ("pom.xml", "Java", "Maven"),
    ("build.gradle", "Java", "Gradle"),
    ("build.gradle.kts", "Java", "Gradle"),
    ("go.mod", "Go", "Go"),
    ("Cargo.toml", "Rust", "Cargo"),
    ("pyproject.toml", "Python", "pip"),
    ("setup.py", "Python", "pip"),
    ("requirements.txt", "Python", "pip"),
    ("package.json", "JavaScript", "npm"),
)


def is_adr_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    if name in SKIP_NAMES:
        return False
    return bool(ADR_FILE.search(path))


def build_files_from_names(names: list[str]) -> tuple[str, str]:
    """Language and build tool from file names at the repo root or one level down."""
    found: list[tuple[str, str]] = []
    lowered = [name.lower() for name in names]
    for marker, language, tool in BUILD_FILES:
        if marker in lowered or any(item.endswith("/" + marker) for item in lowered):
            found.append((language, tool))
    if any(item.endswith(".csproj") for item in lowered):
        found.append(("C#", "dotnet"))
    if not found:
        return "", ""
    languages = []
    tools = []
    for language, tool in found:
        if language not in languages:
            languages.append(language)
        if tool not in tools:
            tools.append(tool)
    return languages[0], ";".join(tools)


def _looks_like_adr_target(label: str, url: str, known: set[str]) -> bool:
    blob = f"{label} {url}"
    base = url.split("?", 1)[0].split("#", 1)[0]
    name = base.rsplit("/", 1)[-1].lower()
    if name in known:
        return True
    if re.search(r"(?i)\badr[\s#_:-]*\d", blob):
        return True
    if re.search(r"(?i)(?:adr|decisions)/[^)\s]+\.md", url):
        return True
    if re.search(r"(?i)\d{3,5}-.+\.md$", name) and re.search(r"(?i)adr|decision", url + label):
        return True
    return False


def _status_blob(text: str) -> str:
    parts = []
    front = _front_matter_status(text) or ""
    if front:
        parts.append(front)
    region = _status_region(text) or ""
    if region:
        parts.append(region)
    return "\n".join(parts)


def _sentence_around(text: str, start: int, end: int) -> str:
    left = max(text.rfind("\n", 0, start), text.rfind(".", 0, start), text.rfind("!", 0, start), text.rfind("?", 0, start))
    right_candidates = [text.find(mark, end) for mark in ("\n", ".", "!", "?")]
    right_candidates = [item for item in right_candidates if item != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1 : right]


def classify_links(text: str, known_names: set[str]) -> tuple[list[dict], int]:
    """Return accepted ADR links and how many ADR links were rejected."""
    status_blob = _status_blob(text)
    accepted = []
    rejected = 0
    for match in LINK.finditer(text or ""):
        label = match.group("label").strip()
        url = match.group("url").strip()
        if not _looks_like_adr_target(label, url, known_names):
            continue
        snippet = match.group(0)
        in_status = snippet in status_blob or (label in status_blob and url in status_blob)
        sentence = _sentence_around(text, match.start(), match.end())
        in_sentence = bool(WORDING.search(sentence))
        if in_status or in_sentence:
            accepted.append({"label": label, "url": url, "sentence": " ".join(sentence.split())[:300]})
        else:
            rejected += 1
    return accepted, rejected


def _resolve_number(token: str, by_id: dict[str, str]) -> str | None:
    match = re.search(r"(?i)(?:adr[\s#_:-]*)?(\d{1,5})\b", token)
    if not match:
        return None
    number = str(int(match.group(1)))
    return by_id.get(number)


def resolve_target(token: str, old_path: str, paths: list[str]) -> str | None:
    """Map a pointer or link onto another ADR path in this repository."""
    if not token:
        return None
    by_id: dict[str, str] = {}
    by_name: dict[str, str] = {}
    for path in paths:
        ident = adr_identifier(path)
        if ident and ident not in by_id:
            by_id[ident] = path
        by_name[path.rsplit("/", 1)[-1].lower()] = path
    url_match = re.search(r"\(([^)]+)\)", token)
    url = url_match.group(1) if url_match else token
    url = url.split("?", 1)[0].split("#", 1)[0].strip()
    name = url.rsplit("/", 1)[-1].lower()
    if name in by_name and by_name[name] != old_path:
        return by_name[name]
    if "/" in url:
        relative = str(PurePosixPath(old_path).parent.joinpath(url))
        # PurePosixPath keeps ".." segments until the next normalisation.
        parts: list[str] = []
        for part in relative.split("/"):
            if part in ("", "."):
                continue
            if part == ".." and parts:
                parts.pop()
            elif part != "..":
                parts.append(part)
        candidate = "/".join(parts)
        if candidate in paths and candidate != old_path:
            return candidate
    found = _resolve_number(token, by_id)
    if found and found != old_path:
        return found
    return None


def pairs_in_repo(records: list[dict]) -> tuple[list[dict], int, int]:
    """Build superseded pairs from ADR texts.

    records: {path, text}. Returns pairs, rejected link count, unresolved count.
    """
    paths = [row["path"] for row in records]
    names = {path.rsplit("/", 1)[-1].lower() for path in paths}
    rejected = 0
    unresolved = 0
    found: dict[tuple[str, str], dict] = {}
    for row in records:
        text = row.get("text") or ""
        status = parse_status(text)
        links, rejected_here = classify_links(text, names)
        rejected += rejected_here
        targets: list[tuple[str, str]] = []
        pointer = find_replacement(_status_blob(text)) or status.replacement
        if status.state in {"superseded", "deprecated"} or pointer:
            if pointer:
                targets.append((pointer, status.raw or pointer))
            elif status.state == "superseded":
                unresolved += 1
        for link in links:
            targets.append((f"{link['label']} ({link['url']})", link["sentence"] or status.raw))
        for token, wording in targets:
            target = resolve_target(token, row["path"], paths)
            if not target:
                unresolved += 1
                continue
            key = (row["path"], target)
            found.setdefault(
                key,
                {
                    "old_adr": row["path"],
                    "new_adr": target,
                    "supersede_wording": (wording or "")[:300],
                    "old_status": status.raw[:300],
                    "old_text": text,
                    "new_text": "",
                },
            )
    by_path = {row["path"]: row.get("text") or "" for row in records}
    for pair in found.values():
        pair["new_text"] = by_path.get(pair["new_adr"], "")
    return list(found.values()), rejected, unresolved


def keywords_from(*texts: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{3,}", text or ""):
            word = token.lower().strip(".-")
            if len(word) < 4 or word in STOPWORDS or word in seen:
                continue
            if word.isdigit():
                continue
            seen.add(word)
            found.append(word)
    return found


def technologies_in(*texts: str) -> list[str]:
    blob = "\n".join(texts).lower()
    return [name for name in TECHNOLOGIES if re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", blob)]


def is_application_path(path: str) -> bool:
    if is_adr_path(path):
        return False
    low = path.lower()
    name = low.rsplit("/", 1)[-1]
    if name in {"readme.md", "license", "license.md", "changelog.md", "contributing.md", "copying"}:
        return False
    if low.endswith((".md", ".rst", ".adoc")):
        return False
    suffix = PurePosixPath(low).suffix
    if suffix in CODE_EXT:
        return True
    if name in {"dockerfile", "makefile", "gemfile", "rakefile"}:
        return True
    return any(marker in low for marker in CONFIG_MARKERS)


def is_config_or_schema(path: str) -> bool:
    low = path.lower()
    return any(marker in low for marker in CONFIG_MARKERS + SCHEMA_MARKERS)


def keyword_hits(paths: list[str], keywords: list[str]) -> list[str]:
    matched: list[str] = []
    blob = " ".join(paths).lower()
    for word in keywords:
        if re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", blob):
            matched.append(word)
    return matched


def mentions_adr(message: str, numbers: list[str], titles: list[str]) -> bool:
    text = message or ""
    for number in numbers:
        if not number:
            continue
        if re.search(rf"(?i)\badr[\s#_:-]*0*{re.escape(number)}\b", text):
            return True
        if re.search(rf"(?i)\b0*{re.escape(number)}\b", text) and re.search(r"(?i)\badr\b|decision", text):
            return True
    for title in titles:
        words = [word for word in keywords_from(title) if len(word) >= 5]
        if len(words) >= 2 and sum(1 for word in words if word in text.lower()) >= 2:
            return True
    return False


def first_paragraph(text: str) -> str:
    """Prose after the title, skipping a leading status section."""
    cleaned = re.sub(r"(?s)\A---\s*\n.*?\n---\s*\n", "", text or "")
    lines = cleaned.splitlines()
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index < len(lines) and lines[index].lstrip().startswith("#"):
        index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index < len(lines) and re.match(r"(?i)^#{1,6}\s*status\b", lines[index].strip()):
        index += 1
        while index < len(lines) and not re.match(r"^#{1,6}\s+\S", lines[index]) and lines[index].strip():
            index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1
    chunk: list[str] = []
    while index < len(lines) and lines[index].strip() and not re.match(r"^#{1,6}\s+\S", lines[index]):
        chunk.append(lines[index].strip())
        index += 1
    return " ".join(chunk)[:500]


def title_of(text: str) -> str:
    return adr_title(text)
