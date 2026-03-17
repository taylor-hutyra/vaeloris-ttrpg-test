"""Change propagation engine (port of propagation.ts).

Instead of a StorageAdapter the Python version receives a plain dict
mapping entity path -> parsed entity dict.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Callable, Any, Optional

from .frontmatter import strip_wikilink, extract_wikilinks


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Change:
    entity_path: str
    entity_name: str
    entity_type: str   # wb-type value
    change_type: str   # "create" | "update" | "delete"
    field: str         # field that changed (or "*" for whole-entity)
    old_value: Any = None
    new_value: Any = None
    full_entity: Optional[dict] = None


@dataclass
class PropagationRule:
    name: str
    description: str
    trigger: Callable[[Change], bool]
    compute: Callable[[Change, dict[str, dict]], list[dict]]


# ---------------------------------------------------------------------------
# Helper: build a lookup from entity name -> entity data
# ---------------------------------------------------------------------------

def _name_index(entities_data: dict[str, dict]) -> dict[str, dict]:
    """Map entity name (from frontmatter.name or filename) -> entity dict."""
    idx: dict[str, dict] = {}
    for path, entity in entities_data.items():
        fm = entity.get("frontmatter", {})
        name = fm.get("name", path.rsplit("/", 1)[-1].replace(".md", ""))
        idx[name] = entity
    return idx


# ---------------------------------------------------------------------------
# Built-in propagation rules
# ---------------------------------------------------------------------------

def _trigger_event_affects(change: Change) -> bool:
    return change.entity_type == "event" and change.change_type in ("create", "update")


def _compute_event_affects(change: Change, entities_data: dict[str, dict]) -> list[dict]:
    """When an event is created/updated, flag affected entities."""
    suggestions: list[dict] = []
    entity = change.full_entity or {}
    fm = entity.get("frontmatter", {})
    body = entity.get("body", "")

    # Gather all referenced entity names from body + relationships
    referenced: set[str] = set()
    for link in extract_wikilinks(body):
        referenced.add(link)
    for rel in fm.get("relationships", []):
        target = rel.get("target", "")
        referenced.add(strip_wikilink(str(target)))

    name_idx = _name_index(entities_data)
    event_name = fm.get("name", change.entity_name)

    for ref_name in referenced:
        if ref_name in name_idx:
            suggestions.append({
                "type": "suggestion",
                "rule": "event_affects_entities",
                "target_entity": ref_name,
                "message": f"Event '{event_name}' may affect '{ref_name}'. "
                           f"Consider adding a timeline entry.",
            })
    return suggestions


def _trigger_leader_death(change: Change) -> bool:
    return (
        change.entity_type == "person"
        and change.change_type == "update"
        and change.field in ("status", "*")
    )


def _compute_leader_death(change: Change, entities_data: dict[str, dict]) -> list[dict]:
    """When a person's status becomes 'dead', suggest vacating leadership."""
    new_val = change.new_value
    if not isinstance(new_val, str) or new_val.lower() != "dead":
        # Also check full entity
        if change.full_entity:
            fm = change.full_entity.get("frontmatter", {})
            if str(fm.get("status", "")).lower() != "dead":
                return []
        else:
            return []

    suggestions: list[dict] = []
    person_name = change.entity_name

    for path, entity in entities_data.items():
        fm = entity.get("frontmatter", {})
        if fm.get("wb-type") != "faction":
            continue
        leader = fm.get("leader", "")
        if strip_wikilink(str(leader)) == person_name:
            faction_name = fm.get("name", path)
            suggestions.append({
                "type": "suggestion",
                "rule": "leader_death_vacates_faction",
                "target_entity": faction_name,
                "message": f"Leader '{person_name}' is dead. "
                           f"Faction '{faction_name}' may need a new leader.",
            })
    return suggestions


def _trigger_faction_dissolved(change: Change) -> bool:
    return (
        change.entity_type == "faction"
        and change.change_type == "update"
        and change.field in ("status", "*")
    )


def _compute_faction_dissolved(change: Change, entities_data: dict[str, dict]) -> list[dict]:
    """When a faction is dissolved, suggest updating member affiliations."""
    new_val = change.new_value
    if not isinstance(new_val, str) or new_val.lower() != "dissolved":
        if change.full_entity:
            fm = change.full_entity.get("frontmatter", {})
            if str(fm.get("status", "")).lower() != "dissolved":
                return []
        else:
            return []

    suggestions: list[dict] = []
    faction_name = change.entity_name

    for path, entity in entities_data.items():
        fm = entity.get("frontmatter", {})
        for rel in fm.get("relationships", []):
            target = strip_wikilink(str(rel.get("target", "")))
            if target == faction_name and rel.get("type") == "member-of":
                member_name = fm.get("name", path)
                suggestions.append({
                    "type": "suggestion",
                    "rule": "faction_dissolved_members_unaffiliated",
                    "target_entity": member_name,
                    "message": f"Faction '{faction_name}' dissolved. "
                               f"Member '{member_name}' may be unaffiliated.",
                })
    return suggestions


def _trigger_place_conquered(change: Change) -> bool:
    return (
        change.entity_type == "place"
        and change.change_type == "update"
        and change.field in ("controlled-by", "ruler", "*")
    )


def _compute_place_conquered(change: Change, entities_data: dict[str, dict]) -> list[dict]:
    """When a place changes controller, suggest updating sub-locations."""
    suggestions: list[dict] = []
    place_name = change.entity_name

    for path, entity in entities_data.items():
        fm = entity.get("frontmatter", {})
        parent_raw = fm.get("parent", "")
        if strip_wikilink(str(parent_raw)) == place_name:
            child_name = fm.get("name", path)
            suggestions.append({
                "type": "suggestion",
                "rule": "place_conquered_propagates",
                "target_entity": child_name,
                "message": f"Place '{place_name}' changed control. "
                           f"Sub-location '{child_name}' may also be affected.",
            })
    return suggestions


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

BUILTIN_RULES: list[PropagationRule] = [
    PropagationRule(
        name="event_affects_entities",
        description="Flag entities referenced by a new/updated event",
        trigger=_trigger_event_affects,
        compute=_compute_event_affects,
    ),
    PropagationRule(
        name="leader_death_vacates_faction",
        description="Suggest leadership vacancy when a leader dies",
        trigger=_trigger_leader_death,
        compute=_compute_leader_death,
    ),
    PropagationRule(
        name="faction_dissolved_members_unaffiliated",
        description="Suggest updating members when a faction dissolves",
        trigger=_trigger_faction_dissolved,
        compute=_compute_faction_dissolved,
    ),
    PropagationRule(
        name="place_conquered_propagates",
        description="Suggest updating sub-locations when a place changes control",
        trigger=_trigger_place_conquered,
        compute=_compute_place_conquered,
    ),
]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def propagate_change(
    change: Change,
    entities_data: dict[str, dict],
    rules: Optional[list[PropagationRule]] = None,
) -> list[dict]:
    """Run all matching propagation rules and return suggestions.

    Each suggestion is a dict with keys: type, rule, target_entity, message.
    """
    if rules is None:
        rules = BUILTIN_RULES

    results: list[dict] = []
    for rule in rules:
        if rule.trigger(change):
            results.extend(rule.compute(change, entities_data))
    return results
