"""Entity validation and schema definitions (port of schemas.ts / types.ts).

Simple dict-based validation without Zod.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENTITY_TYPES: list[str] = [
    "person",
    "place",
    "event",
    "faction",
    "religion",
    "government",
    "species",
    "magic",
    "technology",
    "item",
    "narrative",
]

TYPE_FOLDERS: dict[str, str] = {
    "person": "People/",
    "place": "Places/",
    "event": "Events/",
    "faction": "Factions/",
    "religion": "Religions/",
    "government": "Governments/",
    "species": "Species/",
    "magic": "Magic/",
    "technology": "Technology/",
    "item": "Items/",
    "narrative": "Narratives/",
}

# Relationship inverse pairs.  Symmetric relationships map to themselves.
RELATIONSHIP_INVERSES: dict[str, str] = {
    # Asymmetric pairs
    "parent-of": "child-of",
    "child-of": "parent-of",
    "mentor-of": "student-of",
    "student-of": "mentor-of",
    "leader-of": "led-by",
    "led-by": "leader-of",
    "member-of": "has-member",
    "has-member": "member-of",
    "controls": "controlled-by",
    "controlled-by": "controls",
    "serves": "served-by",
    "served-by": "serves",
    "worships": "worshipped-by",
    "worshipped-by": "worships",
    "created": "created-by",
    "created-by": "created",
    "vassal-of": "overlord-of",
    "overlord-of": "vassal-of",
    "successor-of": "predecessor-of",
    "predecessor-of": "successor-of",
    "rules": "ruled-by",
    "ruled-by": "rules",
    "founded": "founded-by",
    "founded-by": "founded",
    "employs": "employed-by",
    "employed-by": "employs",
    "owns": "owned-by",
    "owned-by": "owns",
    "protects": "protected-by",
    "protected-by": "protects",
    "teaches": "taught-by",
    "taught-by": "teaches",
    # Symmetric
    "ally": "ally",
    "enemy": "enemy",
    "spouse": "spouse",
    "sibling": "sibling",
    "rival": "rival",
    "friend": "friend",
    "trades-with": "trades-with",
}


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

# Each schema: required_fields and optional_fields
# required_fields: list of field names that MUST be present
# optional_fields: dict of field_name -> type description (for documentation)

ENTITY_SCHEMAS: dict[str, dict[str, Any]] = {
    "person": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "status": "str (alive|dead|unknown)",
            "species": "str (wikilink)",
            "birth": "str (period)",
            "death": "str (period)",
            "gender": "str",
            "title": "str",
            "parent": "str (wikilink to place)",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "place": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "place-type": "str (continent|region|city|building|etc.)",
            "parent": "str (wikilink to parent place)",
            "population": "int",
            "ruler": "str (wikilink)",
            "controlled-by": "str (wikilink)",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "event": {
        "required_fields": ["wb-type", "name", "period"],
        "optional_fields": {
            "event-type": "str (battle|treaty|founding|etc.)",
            "location": "str (wikilink)",
            "participants": "list[str] (wikilinks)",
            "outcome": "str",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "faction": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "faction-type": "str (guild|army|order|etc.)",
            "status": "str (active|dissolved|unknown)",
            "leader": "str (wikilink)",
            "headquarters": "str (wikilink)",
            "founded": "str (period)",
            "dissolved": "str (period)",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "religion": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "deity": "str or list[str]",
            "domains": "list[str]",
            "headquarters": "str (wikilink)",
            "founded": "str (period)",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "government": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "government-type": "str (monarchy|republic|theocracy|etc.)",
            "territory": "str (wikilink)",
            "leader": "str (wikilink)",
            "founded": "str (period)",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "species": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "habitat": "str",
            "lifespan": "str",
            "intelligence": "str (sentient|semi-sentient|animal|etc.)",
            "population": "str",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "magic": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "magic-type": "str (arcane|divine|natural|etc.)",
            "source": "str",
            "practitioners": "list[str] (wikilinks)",
            "limitations": "str",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "technology": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "tech-level": "str",
            "inventor": "str (wikilink)",
            "period": "str (period)",
            "prerequisites": "list[str]",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "item": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "item-type": "str (weapon|artifact|tool|etc.)",
            "creator": "str (wikilink)",
            "owner": "str (wikilink)",
            "location": "str (wikilink)",
            "magical": "bool",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
    "narrative": {
        "required_fields": ["wb-type", "name"],
        "optional_fields": {
            "narrative-type": "str (chapter|arc|vignette|lore|era)",
            "period": "str (period)",
            "pov": "str (wikilink)",
            "location": "str (wikilink)",
            "characters": "list[str] (wikilinks)",
            "relationships": "list[dict]",
            "timeline": "list[dict]",
            "tags": "list[str]",
        },
    },
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_entity(data: dict) -> dict:
    """Validate an entity frontmatter dict.

    Returns {"valid": bool, "errors": list[str]}.
    """
    errors: list[str] = []

    # Must have wb-type
    wb_type = data.get("wb-type")
    if not wb_type:
        errors.append("Missing required field: wb-type")
        return {"valid": False, "errors": errors}

    if wb_type not in ENTITY_SCHEMAS:
        errors.append(f"Unknown wb-type: {wb_type}")
        return {"valid": False, "errors": errors}

    schema = ENTITY_SCHEMAS[wb_type]

    # Check required fields
    for field in schema["required_fields"]:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    # Validate relationships structure
    relationships = data.get("relationships")
    if relationships is not None:
        if not isinstance(relationships, list):
            errors.append("'relationships' must be a list")
        else:
            for i, rel in enumerate(relationships):
                if not isinstance(rel, dict):
                    errors.append(f"relationships[{i}]: must be a dict")
                    continue
                if "target" not in rel:
                    errors.append(f"relationships[{i}]: missing 'target'")
                if "type" not in rel:
                    errors.append(f"relationships[{i}]: missing 'type'")

    # Validate timeline entries
    timeline = data.get("timeline")
    if timeline is not None:
        if not isinstance(timeline, list):
            errors.append("'timeline' must be a list")
        else:
            for i, entry in enumerate(timeline):
                if not isinstance(entry, dict):
                    errors.append(f"timeline[{i}]: must be a dict")
                    continue
                if "period" not in entry:
                    errors.append(f"timeline[{i}]: missing 'period'")

    return {"valid": len(errors) == 0, "errors": errors}
