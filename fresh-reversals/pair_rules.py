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
    r"docs/architecture/decisions|doc/architecture/decisions|documentation/architecture/decisions|"
    r"docs/architecture/adrs|docs/architecture/adr|doc/architecture/adr|"
    r"docs/architecture-decisions|doc/architecture-decisions|"
    r"source/architecture_decision_records|"
    r"docs/architecture|doc/architecture|documentation/architecture|doc/arch|"
    r"docs/adr|doc/adr|docs/adrs|doc/adrs|docs/decisions|doc/decisions|"
    r"architecture/decisions|src/adr|"
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


_THIS_OLD = re.compile(
    r"(?i)\b(?:superseded|superceded|replaced)\s+by\b|\bdeprecated\s+in\s+favou?r\s+of\b"
)
_THIS_NEW = re.compile(r"(?i)\b(?:supersedes|supercedes|superseding|replaces|replacing)\b")
_PARTIAL = re.compile(r"(?i)\bpartially\s+supersedes\b")
_NOTHING = re.compile(r"(?i)\bsupersedes\s+nothing\b")
_REAL = re.compile(
    r"(?i)\b(?:superseded|superceded|replaced)\s+by\b|"
    r"\b(?:supersedes|supercedes|superseding|replaces|replacing)\b|"
    r"\bdeprecated\s+in\s+favou?r\s+of\b|\bpartially\s+supersedes\b"
)
_ADR_MENTION = re.compile(r"(?i)\badr[\s#_:-]*\d{1,5}\b")
_COPY_PARTS = {
    "vendor", "node_modules", "third_party", "third-party", "examples", "example",
    "samples", "templates", "fixtures", "fixture", "testdata", "test-fixtures",
    "test_fixtures", "dbt_packages", "site-packages",
}
_SPECIFIC_BITS = (
    "docs/adr/", "doc/adr/", "docs/adrs/", "doc/adrs/", "docs/decisions/", "doc/decisions/",
    "architecture/decisions/", "docs/architecture/decisions/", "doc/architecture/decisions/",
    "docs/architecture/adr/", "docs/architecture/adrs/", "doc/architecture/adr/",
    "docs/architecture-decisions/", "doc/architecture-decisions/", "src/adr/",
    "source/architecture_decision_records/", "documentation/architecture/decisions/",
    "guides/architecture/decisions/", "/adr/", "/adrs/",
)
_GENERAL_BITS = (
    "docs/architecture/", "doc/architecture/", "doc/arch/", "documentation/architecture/",
)
_DEP_NAMES = {
    "pom.xml", "build.gradle", "build.gradle.kts", "package.json", "package-lock.json",
    "yarn.lock", "pnpm-lock.yaml", "go.mod", "go.sum", "cargo.toml", "cargo.lock",
    "requirements.txt", "pyproject.toml", "setup.py", "composer.json", "gemfile", "gemfile.lock",
}


def is_copied_path(path: str) -> bool:
    parts = [part.lower() for part in path.split("/")]
    if any(part in _COPY_PARTS for part in parts):
        return True
    low = path.lower()
    return "dbt_utils" in low or "dbt-utils" in low or "/dbt_packages/" in low


def is_foreign_copy(path: str, text: str, project: str) -> bool:
    """An ADR carried in from another project, such as vendored dbt_utils records."""
    if is_copied_path(path):
        return True
    head = "\n".join((text or "").splitlines()[:8]).lower()
    repo = (project or "").split("/")[-1].lower()
    if ("dbt_utils" in head or "dbt-labs" in head) and "dbt" not in repo:
        return True
    if re.search(r"(?i)\bcopied from\b|\bvendored from\b", head):
        return True
    return False


def is_template_file(path: str, text: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    if "template" in name:
        return True
    head = (text or "")[:1800]
    return bool(re.search(r"(?i)this is a template|template for (?:writing )?architecture decision", head))


def is_specific_adr_path(path: str) -> bool:
    low = "/" + path.lower().lstrip("/")
    return any(bit in low for bit in _SPECIFIC_BITS) or low.startswith("/adr/")


def is_general_folder_path(path: str) -> bool:
    if is_specific_adr_path(path):
        return False
    low = "/" + path.lower().lstrip("/")
    return any(bit in low or low.startswith("/" + bit.lstrip("/")) for bit in _GENERAL_BITS)


def filename_has_number(path: str) -> bool:
    return bool(re.search(r"\d", path.rsplit("/", 1)[-1]))


def has_status_section(text: str) -> bool:
    return bool(_status_region(text) or _front_matter_status(text))


def _refs_with_pos(sentence: str, known_names: set[str]) -> list[tuple[int, str]]:
    """ADR references in one sentence, with the position of each reference."""
    refs: list[tuple[int, str]] = []
    occupied: list[tuple[int, int]] = []
    for match in LINK.finditer(sentence):
        label = match.group("label").strip()
        url = match.group("url").strip()
        if _looks_like_adr_target(label, url, known_names):
            refs.append((match.start(), f"{label} ({url})"))
            occupied.append((match.start(), match.end()))
    for match in _ADR_MENTION.finditer(sentence):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        refs.append((match.start(), match.group(0)))
    return refs


def pairs_in_repo(records: list[dict], project: str = "") -> tuple[list[dict], int, int]:
    """Build real replacement pairs. Direction follows the sentence, not the file order.

    Returns pairs, rejected ADR-link count, and unresolved replacement sentences.
    """
    paths = [row["path"] for row in records]
    names = {path.rsplit("/", 1)[-1].lower() for path in paths}
    by_path = {row["path"]: row.get("text") or "" for row in records}
    rejected = 0
    unresolved = 0
    emitted: list[dict] = []
    for row in records:
        text = row.get("text") or ""
        status = parse_status(text)
        for match in LINK.finditer(text):
            label = match.group("label").strip()
            url = match.group("url").strip()
            if not _looks_like_adr_target(label, url, names):
                continue
            sentence = _sentence_around(text, match.start(), match.end())
            if not _REAL.search(sentence):
                rejected += 1
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            if _NOTHING.search(sentence) or not _REAL.search(sentence):
                continue
            refs = _refs_with_pos(sentence, names)
            if not refs:
                unresolved += 1
                continue
            old_verb = _THIS_OLD.search(sentence)
            new_verb = _THIS_NEW.search(sentence)
            partial = "yes" if _PARTIAL.search(sentence) else "no"
            seen_targets: set[str] = set()
            for pos, ref in refs:
                target = resolve_target(ref, row["path"], paths)
                if not target or target == row["path"] or target in seen_targets:
                    if not target or target == row["path"]:
                        unresolved += 1
                    continue
                seen_targets.add(target)
                # "Superseded by ADR-X" / "replaced by" / "deprecated in favour of":
                # this file is the old ADR. "Supersedes ADR-X" (the reference follows
                # the verb) means this file is the new ADR. "ADR-X supersedes ..."
                # (the reference is the subject) means ADR-X is the new ADR.
                if old_verb:
                    current_is_new = False
                    prefer = True
                elif new_verb and pos > new_verb.start():
                    current_is_new = True
                    prefer = False
                else:
                    current_is_new = False
                    prefer = True
                if current_is_new:
                    old_path, new_path = target, row["path"]
                else:
                    old_path, new_path = row["path"], target
                emitted.append(
                    {
                        "old_adr": old_path,
                        "new_adr": new_path,
                        "supersede_wording": " ".join(sentence.split())[:300],
                        "old_status": status.raw[:300] if old_path == row["path"] else "",
                        "partial": partial,
                        "old_text": by_path.get(old_path, ""),
                        "new_text": by_path.get(new_path, ""),
                        "_prefer": prefer,
                    }
                )
    found: dict[tuple[str, str], dict] = {}
    for pair in emitted:
        key = (pair["old_adr"], pair["new_adr"])
        previous = found.get(key)
        if previous is None or (pair["_prefer"] and not previous.get("_prefer")):
            found[key] = pair
    # One row per pair of files. "Superseded by" wins over the reverse sentence.
    unique: dict[tuple[str, str], dict] = {}
    for pair in found.values():
        mirror = unique.get((pair["new_adr"], pair["old_adr"]))
        if mirror is not None and not pair.get("_prefer"):
            continue
        if mirror is not None and pair.get("_prefer"):
            unique.pop((pair["new_adr"], pair["old_adr"]), None)
        unique[(pair["old_adr"], pair["new_adr"])] = pair
    cleaned = []
    for pair in unique.values():
        pair.pop("_prefer", None)
        if not pair.get("old_status"):
            pair["old_status"] = (parse_status(pair.get("old_text") or "").raw or "")[:300]
        cleaned.append(pair)
    return cleaned, rejected, unresolved


def loose_keywords(text: str) -> list[str]:
    words = []
    seen: set[str] = set()
    normalized = (text or "").replace("-", " ").replace("_", " ")
    for token in re.findall(r"[A-Za-z][A-Za-z0-9+#.]{3,}", normalized):
        word = token.lower().strip(".")
        if len(word) < 4 or word in STOPWORDS or word in seen or word.isdigit():
            continue
        seen.add(word)
        words.append(word)
    return words


def _word_in(word: str, text: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(word)}[a-z0-9]*", text or ""))


def _split_change(raw: str) -> tuple[str, str]:
    if "\t" not in raw:
        return "M", raw.strip()
    action, _, rest = raw.partition("\t")
    path = rest.split("\t")[-1].strip()
    kind = action[:1].upper() if action else "M"
    return kind, path


def _is_dep(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    extra = {
        "libs.versions.toml", "gradle.lockfile", "poetry.lock", "pipfile",
        "pipfile.lock", "composer.lock", "packages.lock.json", "paket.lock",
    }
    return name in _DEP_NAMES or name in extra


def _is_source(path: str) -> bool:
    if _is_dep(path):
        return False
    low = path.lower()
    if "/.github/" in f"/{low}" or low.startswith(".github/") or ".circleci" in low or "jenkinsfile" in low:
        return False
    if "azure-pipelines" in low:
        return False
    return is_application_path(path)


def choose_best_commit(commits: list[dict], new_title: str, old_text: str, new_text: str, new_number: str) -> dict | None:
    """Pick one implementing commit. Title match outranks a dependency-only edit."""
    new_words = loose_keywords(new_title)
    old_words = loose_keywords(title_of(old_text))
    old_tech = technologies_in(old_text)
    ranked = []
    for commit in commits:
        subject = commit.get("subject") or ""
        low = subject.lower()
        title_hits = [word for word in new_words if _word_in(word, low)]
        score = 0
        why = []
        if new_number and re.search(rf"(?i)\badr[\s#_:-]*0*{re.escape(new_number)}\b", subject):
            score += 30
            why.append(f"commit title names ADR {new_number}")
        if len(title_hits) >= 2 or any(len(word) >= 8 for word in title_hits):
            score += 100 + 5 * len(title_hits)
            why.append("commit title matches the new ADR: " + ", ".join(title_hits))
        removed = False
        source_paths = []
        config_paths = []
        dep_paths = []
        for raw in commit.get("files") or []:
            kind, path = _split_change(raw)
            if not path:
                continue
            blob = path.lower().replace("-", " ").replace("_", " ")
            names_old = any(_word_in(word, blob) for word in old_words) or any(tech in path.lower() for tech in old_tech)
            if kind in {"D", "R"} and names_old:
                removed = True
            if _is_dep(path):
                dep_paths.append(path)
                continue
            if _is_source(path):
                source_paths.append(path)
            elif is_config_or_schema(path):
                config_paths.append(path)
        if removed:
            score += 40
            why.append("removes or replaces something named in the old ADR")
        if source_paths:
            score += 10
            why.append("changes application code")
        config_hits = keyword_hits(config_paths, new_words + old_words)
        if config_hits:
            score += 5
            why.append("changes configuration or schema named in the ADR: " + ", ".join(config_hits))
        topic = keyword_hits(source_paths + dep_paths + config_paths, new_words + old_words)
        ranked.append((score, len(title_hits), commit, why, topic, source_paths, dep_paths, config_hits))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2].get("sha") or ""))
    if not ranked or ranked[0][0] <= 0:
        return None
    score, _hits, commit, why, topic, source_paths, dep_paths, config_hits = ranked[0]
    others = [item[2] for item in ranked[1:] if item[0] > 0][:8]
    title_matched = any(item.startswith("commit title matches") for item in why)
    if source_paths and topic:
        confidence = "high_topic"
    elif dep_paths and topic and title_matched:
        confidence = "high_topic"
    elif source_paths:
        confidence = "high_cooccur"
    elif config_hits or (topic and not source_paths):
        confidence = "medium"
    else:
        confidence = "low"
    return {
        "commit": commit,
        "why": "; ".join(why),
        "confidence": confidence,
        "keywords": topic,
        "others": others,
        "score": score,
    }


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
