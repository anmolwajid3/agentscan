"""Read Maven dependencies from one pom.xml.

A coordinate is groupId:artifactId. A version change of the same coordinate
is not a removal. An unresolved ${property} in the group or artifact is
unparsed and is not treated as a library.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(elem: ET.Element, name: str) -> str:
    for child in list(elem):
        if _local(child.tag) == name and child.text and child.text.strip():
            return child.text.strip()
    return ""


def _properties(root: ET.Element) -> dict[str, str]:
    found: dict[str, str] = {}
    for elem in root.iter():
        if _local(elem.tag) != "properties":
            continue
        for child in list(elem):
            if child.text and child.text.strip():
                found[_local(child.tag)] = child.text.strip()
    group = _child_text(root, "groupId")
    artifact = _child_text(root, "artifactId")
    version = _child_text(root, "version")
    if group:
        found.setdefault("project.groupId", group)
        found.setdefault("groupId", group)
    if artifact:
        found.setdefault("project.artifactId", artifact)
        found.setdefault("artifactId", artifact)
    if version:
        found.setdefault("project.version", version)
        found.setdefault("version", version)
    return found


def _resolve(value: str, props: dict[str, str]) -> str | None:
    if "${" not in value:
        return value
    seen = set()
    current = value
    while "${" in current:
        start = current.find("${")
        end = current.find("}", start)
        if end < 0:
            return None
        key = current[start + 2 : end]
        if key in seen or key not in props:
            return None
        seen.add(key)
        current = current[:start] + props[key] + current[end + 1 :]
    return current


def _dependency_parents(root: ET.Element) -> list[ET.Element]:
    parents = []
    for elem in root.iter():
        if _local(elem.tag) != "dependencies":
            continue
        # Plugin dependencies are not library dependencies.
        chain = []
        parent_map = {child: parent for parent in root.iter() for child in list(parent)}
        node: ET.Element | None = elem
        blocked = False
        while node is not None:
            if _local(node.tag) in {"plugin", "pluginManagement", "reporting"}:
                blocked = True
                break
            node = parent_map.get(node)
        if not blocked:
            parents.append(elem)
    return parents


def parse_pom(text: str) -> tuple[set[str], list[str]]:
    """Return coordinates and unparsed dependency notes.

    An empty file returns no coordinates and no notes. Broken XML returns one
    unparsed note and no coordinates.
    """
    if not text or not text.strip():
        return set(), []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return set(), [f"xml: {exc}"]
    props = _properties(root)
    coordinates: set[str] = set()
    unparsed: list[str] = []
    for block in _dependency_parents(root):
        for dep in list(block):
            if _local(dep.tag) != "dependency":
                continue
            group = _child_text(dep, "groupId")
            artifact = _child_text(dep, "artifactId")
            if not group or not artifact:
                unparsed.append("missing groupId or artifactId")
                continue
            resolved_group = _resolve(group, props)
            resolved_artifact = _resolve(artifact, props)
            if resolved_group is None or resolved_artifact is None:
                unparsed.append(f"unresolved property in {group}:{artifact}")
                continue
            coordinates.add(f"{resolved_group}:{resolved_artifact}")
    return coordinates, unparsed
