"""Spatial hierarchy / containment tree (port of hierarchy.ts)."""

from __future__ import annotations

from typing import Optional

from .frontmatter import strip_wikilink


def build_spatial_tree(
    entities: list[dict],
    name_to_path: dict[str, str],
) -> dict:
    """Build a spatial containment tree from a list of parsed entities.

    *entities* — list of {"path": str, "frontmatter": dict, ...}
    *name_to_path* — mapping from entity display name to its vault path

    Returns {"nodes": {path: node_dict}, "roots": [path, ...]} where each
    node_dict is {"path", "name", "parent", "children": [path, ...]}.
    """
    nodes: dict[str, dict] = {}

    # First pass: create nodes
    for entity in entities:
        path = entity.get("path", "")
        fm = entity.get("frontmatter", {})
        wb_type = fm.get("wb-type", "")

        name = fm.get("name", path.rsplit("/", 1)[-1].replace(".md", ""))

        parent_raw = fm.get("parent")
        parent_path: Optional[str] = None
        if parent_raw:
            parent_name = strip_wikilink(str(parent_raw))
            parent_path = name_to_path.get(parent_name)

        nodes[path] = {
            "path": path,
            "name": name,
            "wb_type": wb_type,
            "parent": parent_path,
            "children": [],
        }

    # Second pass: link children
    for path, node in nodes.items():
        pp = node["parent"]
        if pp and pp in nodes:
            nodes[pp]["children"].append(path)

    # Roots: nodes with no parent (or parent not in the set)
    roots = [p for p, n in nodes.items() if n["parent"] is None or n["parent"] not in nodes]

    return {"nodes": nodes, "roots": roots}


def get_contained_entities(
    tree: dict,
    place_path: str,
    max_depth: float = float("inf"),
) -> list[str]:
    """Return paths of all entities contained within *place_path* up to *max_depth*.

    Depth 1 = direct children only.
    """
    nodes = tree["nodes"]
    if place_path not in nodes:
        return []

    result: list[str] = []
    _collect(nodes, place_path, 0, max_depth, result)
    return result


def _collect(
    nodes: dict,
    path: str,
    current_depth: int,
    max_depth: float,
    result: list[str],
) -> None:
    for child_path in nodes[path]["children"]:
        result.append(child_path)
        if current_depth + 1 < max_depth:
            _collect(nodes, child_path, current_depth + 1, max_depth, result)


def get_containment_chain(tree: dict, entity_path: str) -> list[str]:
    """Return the chain of ancestors from the entity up to the root.

    The first element is the entity itself; the last is the root ancestor.
    """
    nodes = tree["nodes"]
    chain: list[str] = []
    current = entity_path
    visited: set[str] = set()

    while current and current in nodes:
        if current in visited:
            break  # guard against cycles
        visited.add(current)
        chain.append(current)
        current = nodes[current]["parent"]

    return chain


def is_contained_within(
    tree: dict,
    entity_path: str,
    container_path: str,
) -> bool:
    """Check whether *entity_path* is contained (at any depth) within *container_path*."""
    chain = get_containment_chain(tree, entity_path)
    # chain[0] is the entity itself; container must appear later in the chain
    return container_path in chain[1:]
