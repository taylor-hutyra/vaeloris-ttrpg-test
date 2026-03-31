"""Relationship inverse synchronization.

Ensures that when entity A has a relationship to entity B, entity B has the
corresponding inverse relationship back to A.  Operates on frontmatter YAML
in the Markdown source-of-truth files.
"""

from __future__ import annotations

import os
from typing import Optional

from wb_core.frontmatter import parse_markdown, serialize_markdown, strip_wikilink
from wb_core.validation import RELATIONSHIP_INVERSES


# ---------------------------------------------------------------------------
# Inverse computation
# ---------------------------------------------------------------------------

def inverse_type(rel_type: str) -> str:
    """Return the inverse relationship type.

    Known types use RELATIONSHIP_INVERSES.  Unknown types are treated as
    symmetric (same type returned) so ad-hoc types still get inverse edges.
    """
    return RELATIONSHIP_INVERSES.get(rel_type, rel_type)


def compute_inverse(rel: dict, source_name: str) -> dict:
    """Given a relationship dict from *source_name*, produce the inverse.

    Example:
        rel = {target: "[[Faction B]]", type: "member-of", period: "SA:100",
               note: "Joined during the Silver Boom"}
        source_name = "Aldric"
      =>
        {target: "[[Aldric]]", type: "has-member", period: "SA:100",
         note: "Joined during the Silver Boom"}
    """
    inv_type = inverse_type(rel.get("type", ""))
    inv = {
        "target": f"[[{source_name}]]",
        "type": inv_type,
    }
    if rel.get("period"):
        inv["period"] = rel["period"]
    # Carry over metadata if present (new schema), or note (legacy)
    if rel.get("metadata"):
        inv["metadata"] = dict(rel["metadata"])
    elif rel.get("note") or rel.get("notes"):
        inv["metadata"] = {"description": rel.get("note", "") or rel.get("notes", "")}
    return inv


# ---------------------------------------------------------------------------
# Missing-inverse detection
# ---------------------------------------------------------------------------

def _rel_key(rel: dict) -> tuple[str, str]:
    """Canonical key for deduplication: (target_name, type)."""
    target = strip_wikilink(str(rel.get("target", "")))
    return (target, rel.get("type", ""))


def find_missing_inverses(
    source_name: str,
    source_rels: list[dict],
    entities: dict[str, dict],
) -> list[dict]:
    """Find inverse relationships that should exist but don't.

    Parameters
    ----------
    source_name : str
        Display name of the entity whose relationships we're checking.
    source_rels : list[dict]
        The ``relationships`` array from the source entity's frontmatter.
    entities : dict[str, dict]
        Mapping of entity display-name -> {frontmatter, path} for every
        entity in the vault (used to look up target files and existing rels).

    Returns
    -------
    list[dict]
        Each item: {target_name, target_path, inverse_rel}
        where *inverse_rel* is the relationship dict to add to the target.
    """
    missing: list[dict] = []

    for rel in source_rels:
        if not isinstance(rel, dict):
            continue
        target_name = strip_wikilink(str(rel.get("target", "")))
        if not target_name:
            continue

        # Look up target entity
        target_data = entities.get(target_name)
        if target_data is None:
            # Target entity doesn't exist (forward reference) — skip
            continue

        inv = compute_inverse(rel, source_name)
        inv_key = _rel_key(inv)

        # Check if the target already has this inverse
        target_rels = target_data.get("frontmatter", {}).get("relationships") or []
        existing_keys = {_rel_key(r) for r in target_rels if isinstance(r, dict)}

        if inv_key not in existing_keys:
            missing.append({
                "target_name": target_name,
                "target_path": target_data["path"],
                "inverse_rel": inv,
            })

    return missing


# ---------------------------------------------------------------------------
# Apply inverses to files
# ---------------------------------------------------------------------------

def apply_inverse(target_path: str, inverse_rel: dict) -> bool:
    """Add an inverse relationship to a target entity file.

    Reads the file, checks for duplicates, appends if missing, writes back.
    Returns True if the file was modified, False if skipped (duplicate).
    """
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_markdown(content, target_path)
    fm = parsed.get("frontmatter", {})
    body = parsed.get("body", "")

    rels = fm.get("relationships") or []
    if not isinstance(rels, list):
        rels = []

    # Dedup check
    inv_key = _rel_key(inverse_rel)
    for existing in rels:
        if isinstance(existing, dict) and _rel_key(existing) == inv_key:
            return False  # already exists

    # Clean the inverse rel — remove empty fields
    clean_rel = {"target": inverse_rel["target"], "type": inverse_rel["type"]}
    if inverse_rel.get("period"):
        clean_rel["period"] = inverse_rel["period"]
    if inverse_rel.get("metadata"):
        clean_rel["metadata"] = inverse_rel["metadata"]

    rels.append(clean_rel)
    fm["relationships"] = rels

    new_content = serialize_markdown(fm, body)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def ensure_inverses_for_entity(
    entity_path: str,
    vault_root: str,
    entities: Optional[dict[str, dict]] = None,
    apply: bool = False,
) -> dict:
    """Ensure all relationship targets have inverse relationships back.

    Parameters
    ----------
    entity_path : str
        Path to the entity .md file (absolute or relative to vault_root).
    vault_root : str
        Vault root directory.
    entities : dict, optional
        Pre-loaded entity data.  If None, loads all entities from the vault.
    apply : bool
        If True, write changes to target files.  If False, dry-run only.

    Returns
    -------
    dict
        {entity, missing: [{target_name, target_path, inverse_rel}], applied: int}
    """
    abs_path = os.path.join(vault_root, entity_path) if not os.path.isabs(entity_path) else entity_path

    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_markdown(content, abs_path)
    fm = parsed.get("frontmatter", {})
    source_name = fm.get("name", os.path.splitext(os.path.basename(abs_path))[0])
    source_rels = fm.get("relationships") or []

    if entities is None:
        entities = _load_all_entities(vault_root)

    missing = find_missing_inverses(source_name, source_rels, entities)

    applied = 0
    if apply:
        for item in missing:
            if apply_inverse(item["target_path"], item["inverse_rel"]):
                applied += 1
                # Update the in-memory entity data so subsequent checks see the new rel
                target_name = item["target_name"]
                if target_name in entities:
                    rels = entities[target_name].get("frontmatter", {}).get("relationships") or []
                    rels.append(item["inverse_rel"])

    return {
        "entity": source_name,
        "missing": [
            {
                "target": m["target_name"],
                "inverse_type": m["inverse_rel"]["type"],
                "period": m["inverse_rel"].get("period", ""),
                "note": m["inverse_rel"].get("note", "")[:60],
            }
            for m in missing
        ],
        "missing_count": len(missing),
        "applied": applied,
    }


def ensure_inverses_all(
    vault_root: str,
    apply: bool = False,
) -> dict:
    """Ensure inverse relationships across the entire vault.

    Returns
    -------
    dict
        {total_missing, total_applied, entities_with_missing: int, details: [...]}
    """
    entities = _load_all_entities(vault_root)

    total_missing = 0
    total_applied = 0
    entities_with_missing = 0
    details: list[dict] = []

    for name, data in entities.items():
        result = ensure_inverses_for_entity(
            data["path"], vault_root, entities=entities, apply=apply
        )
        if result["missing_count"] > 0:
            entities_with_missing += 1
            total_missing += result["missing_count"]
            total_applied += result["applied"]
            details.append(result)

    return {
        "total_missing": total_missing,
        "total_applied": total_applied,
        "entities_with_missing": entities_with_missing,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_all_entities(vault_root: str) -> dict[str, dict]:
    """Load all entity files into a name -> {frontmatter, path} dict."""
    skip_dirs = {"_meta", "_templates", "node_modules"}
    entities: dict[str, dict] = {}

    for dirpath, dirnames, filenames in os.walk(vault_root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in skip_dirs]
        for fname in filenames:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                parsed = parse_markdown(content, fpath)
                fm = parsed.get("frontmatter", {})
                if fm.get("wb-type"):
                    name = fm.get("name", os.path.splitext(fname)[0])
                    entities[name] = {"frontmatter": fm, "path": fpath}
            except Exception:
                continue

    return entities
