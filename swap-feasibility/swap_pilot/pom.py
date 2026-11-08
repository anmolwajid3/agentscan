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


def _direct_properties(root: ET.Element) -> dict[str, str]:
    found: dict[str, str] = {}
    for elem in list(root):
        if _local(elem.tag) != "properties":
            continue
        for child in list(elem):
            if child.text and child.text.strip():
                found[_local(child.tag)] = child.text.strip()
    return found


def _parent_coordinates(root: ET.Element) -> dict[str, str]:
    for elem in list(root):
        if _local(elem.tag) != "parent":
            continue
        return {
            "project.parent.groupId": _child_text(elem, "groupId"),
            "project.parent.artifactId": _child_text(elem, "artifactId"),
            "project.parent.version": _child_text(elem, "version"),
        }
    return {}


def parent_relative_path(text: str) -> str | None:
    """Relative path of the parent pom inside this repository.

    Maven's default is ../pom.xml. An empty relativePath means the parent is
    not read from this repository.
    """
    if not text or not text.strip():
        return None
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    for elem in list(root):
        if _local(elem.tag) != "parent":
            continue
        seen = False
        raw = ""
        for child in list(elem):
            if _local(child.tag) == "relativePath":
                seen = True
                raw = (child.text or "").strip()
        if not seen:
            return "../pom.xml"
        return raw or None
    return None


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


def _expand_map(props: dict[str, str]) -> dict[str, str]:
    expanded = dict(props)
    for _ in range(len(expanded) + 1):
        changed = False
        for key, value in list(expanded.items()):
            resolved = _resolve(value, expanded)
            if resolved is not None and resolved != value:
                expanded[key] = resolved
                changed = True
        if not changed:
            break
    return expanded


def _apply_identity(props: dict[str, str], root: ET.Element) -> None:
    """A missing group, artifact, or version is inherited from the parent map."""
    group = _child_text(root, "groupId")
    artifact = _child_text(root, "artifactId")
    version = _child_text(root, "version")
    if group:
        props["project.groupId"] = group
        props["groupId"] = group
    elif props.get("project.parent.groupId"):
        props["project.groupId"] = props["project.parent.groupId"]
        props["groupId"] = props["project.parent.groupId"]
    if artifact:
        props["project.artifactId"] = artifact
        props["artifactId"] = artifact
    if version:
        props["project.version"] = version
        props["version"] = version
    elif props.get("project.parent.version"):
        props["project.version"] = props["project.parent.version"]
        props["version"] = props["project.parent.version"]


def parse_pom(text: str, parents: list[str] | None = None) -> tuple[set[str], list[str]]:
    """Return coordinates and unparsed dependency notes.

    `parents` is the nearest parent pom first, then its parent. An empty file
    returns no coordinates and no notes. Broken XML returns one unparsed note
    and no coordinates.
    """
    if not text or not text.strip():
        return set(), []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return set(), [f"xml: {exc}"]
    props: dict[str, str] = {}
    for parent_text in reversed(parents or []):
        if not parent_text or not parent_text.strip():
            continue
        try:
            parent_root = ET.fromstring(parent_text)
        except ET.ParseError:
            continue
        props.update({key: value for key, value in _parent_coordinates(parent_root).items() if value})
        _apply_identity(props, parent_root)
        props.update(_direct_properties(parent_root))
    props.update({key: value for key, value in _parent_coordinates(root).items() if value})
    _apply_identity(props, root)
    props.update(_direct_properties(root))
    props = _expand_map(props)
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
