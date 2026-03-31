#!/usr/bin/env python3
"""wb — World Builder CLI.

Main entry point for the world-building toolkit. Operates relative to vault root
(current working directory by default).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Load .env file if present (for API keys)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is installed as a dep of pydantic-settings
    pass

# Ensure our lib directory is on the path
_LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

from wb_core.frontmatter import parse_markdown, strip_wikilink, extract_wikilinks
from wb_core.period import parse_period, parse_time_point
from wb_core.temporal import get_state_at, get_timeline
from wb_core.validation import validate_entity, RELATIONSHIP_INVERSES
from wb_core.spatial import build_spatial_tree, get_containment_chain, get_contained_entities
from wb_core.propagation import propagate_change, Change

import yaml


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(vault_root: str) -> dict:
    """Load wb-config.md from _meta/ and parse its YAML frontmatter."""
    config_path = os.path.join(vault_root, "_meta", "wb-config.md")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    parsed = parse_markdown(content, config_path)
    return parsed.get("frontmatter", {})


def create_embedding_provider(config: dict):
    """Create an embedding provider based on config settings.

    Reads from the nested 'embeddings' dict in wb-config.md frontmatter:
      embeddings:
        provider: openai
        model: text-embedding-3-large
        configs:
          openai:
            model: text-embedding-3-large
    """
    embeddings_config = config.get("embeddings", {})
    if not isinstance(embeddings_config, dict):
        return None

    provider_name = embeddings_config.get("provider", "").lower()
    if not provider_name:
        return None

    # Get provider-specific config from the configs sub-dict
    configs = embeddings_config.get("configs", {})
    provider_config = configs.get(provider_name, {}) if isinstance(configs, dict) else {}

    if provider_name == "gemini":
        from wb_embeddings.gemini import GeminiEmbeddingProvider
        return GeminiEmbeddingProvider(
            model=provider_config.get("model", embeddings_config.get("model", "text-embedding-004")),
        )
    elif provider_name == "openai":
        from wb_embeddings.openai import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider(
            model=provider_config.get("model", embeddings_config.get("model", "text-embedding-3-large")),
        )
    elif provider_name == "ollama":
        from wb_embeddings.ollama import OllamaEmbeddingProvider
        return OllamaEmbeddingProvider(
            model=provider_config.get("model", embeddings_config.get("model", "nomic-embed-text")),
            host=provider_config.get("endpoint", "http://localhost:11434"),
        )
    elif provider_name == "custom":
        from wb_embeddings.custom import CustomEmbeddingProvider
        command = provider_config.get("command", "")
        dims = int(provider_config.get("dimensions", 384))
        if not command:
            print("Error: custom embedding provider requires 'command' in config", file=sys.stderr)
            return None
        return CustomEmbeddingProvider(command=command, dimensions=dims)
    else:
        print(f"Warning: unknown embedding provider '{provider_name}', using ChromaDB default", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Store initialization (lazy)
# ---------------------------------------------------------------------------

_sqlite_store = None
_graph_store = None
_vector_store = None


def get_sqlite(vault_root: str):
    global _sqlite_store
    if _sqlite_store is None:
        from wb_stores.sqlite_store import SqliteStore
        _sqlite_store = SqliteStore(vault_root)
    return _sqlite_store


def get_graph(vault_root: str):
    global _graph_store
    if _graph_store is None:
        from wb_stores.graph_store import NetworkXGraphStore
        _graph_store = NetworkXGraphStore(vault_root)
    return _graph_store


def get_vector(vault_root: str, config: dict = None):
    global _vector_store
    if _vector_store is None:
        from wb_stores.vector_store import VectorStore
        provider = create_embedding_provider(config or {})
        _vector_store = VectorStore(vault_root, embedding_provider=provider)
    return _vector_store


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_hash(content: str) -> str:
    """SHA-256 hash of file content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_md_files(vault_root: str) -> list[str]:
    """Find all .md files in the vault, excluding _meta/ and _templates/."""
    md_files: list[str] = []
    skip_dirs = {"_meta", "_templates", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(vault_root):
        # Skip hidden dirs, _meta, and _templates
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in skip_dirs]
        for fname in filenames:
            if fname.endswith(".md"):
                md_files.append(os.path.join(dirpath, fname))
    return md_files


def entity_id_from_path(path: str, vault_root: str) -> str:
    """Derive a stable entity ID from the file path relative to vault root."""
    rel = os.path.relpath(path, vault_root).replace("\\", "/")
    return rel.replace(".md", "").replace("/", ".")


def relative_path(path: str, vault_root: str) -> str:
    """Get path relative to vault root with forward slashes."""
    return os.path.relpath(path, vault_root).replace("\\", "/")


# ---------------------------------------------------------------------------
# Sync operations
# ---------------------------------------------------------------------------

def sync_entity(
    file_path: str,
    vault_root: str,
    config: dict,
    force: bool = False,
) -> dict:
    """Sync a single entity file to all three stores.

    Returns a summary dict.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_markdown(content, file_path)
    fm = parsed["frontmatter"]
    body = parsed["body"]

    # Must have wb-type to be an entity
    if not fm.get("wb-type"):
        return {"status": "skipped", "message": "No wb-type in frontmatter", "path": file_path}

    content_hash = compute_hash(content)
    rel_path = relative_path(file_path, vault_root)
    entity_id = entity_id_from_path(file_path, vault_root)

    # Check if already up to date
    sqlite = get_sqlite(vault_root)
    existing = sqlite.get_entity(entity_id)
    if not force and existing and existing.get("content_hash") == content_hash:
        return {"status": "unchanged", "entity_id": entity_id, "path": rel_path}

    action = "update" if existing else "create"

    # 1. SQLite
    sqlite.upsert_entity(entity_id, fm, body, rel_path, content_hash)
    sqlite.log_sync(entity_id, "sqlite", action, content_hash)

    # 2. NetworkX graph
    graph = get_graph(vault_root)
    name = fm.get("name", os.path.basename(file_path).replace(".md", ""))
    graph.add_entity(entity_id, {
        "type": fm.get("wb-type", ""),
        "name": name,
        "tags": fm.get("tags", []),
    })

    # Remove old edges from this entity before adding new ones
    old_edges = list(graph.graph.out_edges(entity_id, keys=True))
    for u, v, k in old_edges:
        graph.graph.remove_edge(u, v, key=k)
    # Also remove inverse edges that were added for this entity
    old_in_edges = list(graph.graph.in_edges(entity_id, keys=True))
    for u, v, k in old_in_edges:
        graph.graph.remove_edge(u, v, key=k)

    rels = fm.get("relationships", [])
    re_embed_targets: set[str] = set()
    if isinstance(rels, list):
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            target_name = strip_wikilink(str(rel.get("target", "")))
            if not target_name:
                continue
            rel_type = rel.get("type", "")
            period = str(rel.get("period", ""))
            # Support both legacy (note) and new schema (metadata.description)
            metadata = rel.get("metadata") or {}
            notes = metadata.get("description", "") or rel.get("note", "") or rel.get("notes", "")
            # Resolve target name to entity ID:
            # 1. Check the name→ID cache (populated during sync_full)
            # 2. Fall back to SQLite query
            # 3. Fall back to raw name
            target_id = _name_to_id_cache.get(target_name)
            if not target_id:
                target_results = sqlite.query(name=target_name)
                for t in target_results:
                    if t["name"] == target_name:
                        target_id = t["id"]
                        break
            if not target_id:
                target_id = target_name  # fallback to raw name
            graph.add_relationship(entity_id, target_id, {
                "type": rel_type,
                "period": period,
                "notes": notes,
            })
            re_embed_targets.add(target_name)

    graph.serialize()
    sqlite.log_sync(entity_id, "graph", action, content_hash)

    # 3. ChromaDB vector store
    from wb_stores.vector_store import build_embedding_text, _build_metadata
    from wb_core.chunking import chunk_entity
    vector = get_vector(vault_root, config)

    # Legacy flat embedding (backward compat)
    embed_text = build_embedding_text(fm, body)
    metadata = _build_metadata(fm)
    vector.upsert_entity(entity_id, embed_text, metadata)

    # Hierarchical chunks (new)
    name = fm.get("name", os.path.splitext(os.path.basename(file_path))[0])
    wb_type = fm.get("wb-type", "")
    chunks = chunk_entity(entity_id, name, wb_type, fm, body)
    if chunks:
        vector.upsert_chunks(entity_id, chunks)

    sqlite.log_sync(entity_id, "vector", action, content_hash)

    # Re-embed related entities (bidirectionality: when A->B added, re-embed B)
    for target_name in re_embed_targets:
        # Find target entity in SQLite by name
        target_results = sqlite.query(name=target_name)
        for t in target_results:
            if t["name"] == target_name:
                target_id = t["id"]
                target_path = os.path.join(vault_root, t["path"])
                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as f:
                        t_content = f.read()
                    t_parsed = parse_markdown(t_content, target_path)
                    t_text = build_embedding_text(t_parsed["frontmatter"], t_parsed["body"])
                    t_meta = _build_metadata(t_parsed["frontmatter"])
                    vector.upsert_entity(target_id, t_text, t_meta)
                break

    return {
        "status": action + "d",
        "entity_id": entity_id,
        "name": name,
        "path": rel_path,
        "content_hash": content_hash,
    }


def sync_full(vault_root: str, config: dict) -> dict:
    """Full sync: scan all .md files and rebuild all stores.

    Two-pass approach:
    1. First pass: upsert all entities into SQLite (builds the name→ID index)
    2. Second pass: build graph relationships and vector embeddings
       (now that all entity IDs are resolvable)
    """
    md_files = find_md_files(vault_root)
    results = {"synced": 0, "skipped": 0, "errors": 0, "details": []}

    # Build a name→entity_id lookup from all files first
    # This lets graph relationships resolve target names to IDs
    name_to_id: dict[str, str] = {}
    file_data: list[tuple[str, dict, str, str, str]] = []  # (fpath, fm, body, entity_id, content_hash)

    for fpath in md_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            parsed = parse_markdown(content, fpath)
            fm = parsed["frontmatter"]
            body = parsed["body"]
            if not fm.get("wb-type"):
                results["skipped"] += 1
                results["details"].append({"status": "skipped", "path": fpath, "message": "No wb-type"})
                continue

            entity_id = entity_id_from_path(fpath, vault_root)
            content_hash = compute_hash(content)
            rel_path = relative_path(fpath, vault_root)

            # Register name and aliases for lookup
            name = fm.get("name", os.path.basename(fpath).replace(".md", ""))
            name_to_id[name] = entity_id
            for alias in fm.get("aliases", []):
                if isinstance(alias, str) and alias:
                    name_to_id[alias] = entity_id

            file_data.append((fpath, fm, body, entity_id, content_hash))
        except Exception as e:
            results["errors"] += 1
            results["details"].append({"status": "error", "path": fpath, "message": str(e)})

    # Store the lookup globally so sync_entity can use it
    global _name_to_id_cache
    _name_to_id_cache = name_to_id

    # Now sync each entity with the full name lookup available
    for fpath, fm, body, entity_id, content_hash in file_data:
        try:
            result = sync_entity(fpath, vault_root, config, force=True)
            if result["status"] in ("created", "updated"):
                results["synced"] += 1
            elif result["status"] == "skipped":
                results["skipped"] += 1
            results["details"].append(result)
        except Exception as e:
            results["errors"] += 1
            results["details"].append({"status": "error", "path": fpath, "message": str(e)})

    # Save graph after full sync
    graph = get_graph(vault_root)
    graph.serialize()

    # Clear the cache
    _name_to_id_cache = {}

    return results

# Global name→ID cache, populated during sync_full
_name_to_id_cache: dict[str, str] = {}


def sync_status(vault_root: str, config: dict) -> dict:
    """Show sync health across all stores."""
    sqlite = get_sqlite(vault_root)
    graph = get_graph(vault_root)
    vector = get_vector(vault_root, config)

    sqlite_status = sqlite.get_sync_status()

    return {
        "sqlite": {
            "entities": sqlite_status["entity_count"],
            "relationships": sqlite_status["relationship_count"],
            "timeline_entries": sqlite_status["timeline_count"],
            "last_sync": sqlite_status["last_sync"],
        },
        "graph": {
            "nodes": graph.node_count(),
            "edges": graph.edge_count(),
        },
        "vector": {
            "entities": vector.count(),
        },
        "sync_log_entries": sqlite_status["sync_log_entries"],
    }


def sync_verify(vault_root: str, config: dict) -> dict:
    """Verify all three stores have the same entity set."""
    sqlite = get_sqlite(vault_root)
    graph = get_graph(vault_root)
    vector = get_vector(vault_root, config)

    sqlite_entities = {e["id"] for e in sqlite.get_all_entities()}
    graph_entities = set(graph.get_all_ids())
    vector_entities = set(vector.get_all_ids())

    all_ids = sqlite_entities | graph_entities | vector_entities

    issues: list[dict] = []
    for eid in sorted(all_ids):
        in_sqlite = eid in sqlite_entities
        in_graph = eid in graph_entities
        in_vector = eid in vector_entities
        if not (in_sqlite and in_graph and in_vector):
            issues.append({
                "entity_id": eid,
                "in_sqlite": in_sqlite,
                "in_graph": in_graph,
                "in_vector": in_vector,
            })

    return {
        "consistent": len(issues) == 0,
        "sqlite_count": len(sqlite_entities),
        "graph_count": len(graph_entities),
        "vector_count": len(vector_entities),
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_sync(args, vault_root: str, config: dict) -> dict:
    if args.status:
        return sync_status(vault_root, config)
    elif args.verify:
        return sync_verify(vault_root, config)
    elif args.full:
        return sync_full(vault_root, config)
    elif args.path:
        file_path = os.path.abspath(args.path)
        return sync_entity(file_path, vault_root, config)
    else:
        return {"error": "Specify a file path, --full, --status, or --verify"}


def cmd_query(args, vault_root: str, config: dict) -> dict:
    # Semantic search via ChromaDB
    if args.semantic:
        vector = get_vector(vault_root, config)
        where = {}
        if args.type:
            where["wb_type"] = args.type
        results = vector.search(
            args.semantic,
            n_results=20,
            where=where if where else None,
        )
        return {"results": results, "store": "vector", "query": args.semantic}

    # Graph query via NetworkX
    if args.related_to:
        graph = get_graph(vault_root)
        hops = args.hops or 1
        neighbors = graph.neighbors(args.related_to, depth=hops)
        return {"results": neighbors, "store": "graph", "root": args.related_to, "hops": hops}

    # Structured query via SQLite
    sqlite = get_sqlite(vault_root)

    # Temporal resolution
    at_time = None
    if args.at:
        at_time = parse_time_point(args.at)

    results = sqlite.query(
        type=args.type,
        tags=args.tags.split(",") if args.tags else None,
        name=args.name,
        within=args.within,
        free_text=args.text,
    )

    # If --at specified, resolve temporal state for each result
    if at_time:
        resolved = []
        for r in results:
            entity_path = os.path.join(vault_root, r["path"])
            if os.path.exists(entity_path):
                with open(entity_path, "r", encoding="utf-8") as f:
                    content = f.read()
                parsed = parse_markdown(content, entity_path)
                state = get_state_at(parsed, at_time)
                resolved.append({**r, "state_at": state})
            else:
                resolved.append(r)
        results = resolved

    return {"results": results, "store": "sqlite", "count": len(results)}


def cmd_resolve(args, vault_root: str, config: dict) -> dict:
    entity_name = args.entity
    time_str = args.at

    if not time_str:
        return {"error": "--at <time> is required for resolve"}

    time_point = parse_time_point(time_str)

    # Find entity file
    sqlite = get_sqlite(vault_root)
    matches = sqlite.query(name=entity_name, type=getattr(args, "type", None))
    if not matches:
        return {"error": f"Entity not found: {entity_name}"}

    # Prefer exact name match over substring match
    exact = [m for m in matches if m["name"] == entity_name]
    entity_data = exact[0] if exact else matches[0]
    entity_path = os.path.join(vault_root, entity_data["path"])
    if not os.path.exists(entity_path):
        return {"error": f"File not found: {entity_path}"}

    with open(entity_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_markdown(content, entity_path)
    state = get_state_at(parsed, time_point)
    timeline = get_timeline(parsed)

    # Clean up internal fields
    for entry in timeline:
        entry.pop("_parsed_period", None)

    return {
        "entity": entity_name,
        "at": time_str,
        "state": state,
        "timeline": timeline,
    }


def cmd_validate(args, vault_root: str, config: dict) -> dict:
    md_files = find_md_files(vault_root)
    results: list[dict] = []
    valid_count = 0
    invalid_count = 0

    for fpath in md_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        parsed = parse_markdown(content, fpath)
        fm = parsed["frontmatter"]

        if not fm.get("wb-type"):
            continue

        validation = validate_entity(fm)
        rel_path = relative_path(fpath, vault_root)

        if validation["valid"]:
            valid_count += 1
        else:
            invalid_count += 1
            results.append({
                "path": rel_path,
                "name": fm.get("name", ""),
                "errors": validation["errors"],
            })

    return {
        "valid": valid_count,
        "invalid": invalid_count,
        "issues": results,
    }


def cmd_propagate(args, vault_root: str, config: dict) -> dict:
    entity_name = args.entity

    # Find entity
    sqlite = get_sqlite(vault_root)
    matches = sqlite.query(name=entity_name)
    if not matches:
        return {"error": f"Entity not found: {entity_name}"}

    entity_data = matches[0]
    entity_path = os.path.join(vault_root, entity_data["path"])
    if not os.path.exists(entity_path):
        return {"error": f"File not found: {entity_path}"}

    with open(entity_path, "r", encoding="utf-8") as f:
        content = f.read()
    parsed = parse_markdown(content, entity_path)

    # Build entities_data from all SQLite entities
    all_entities = sqlite.get_all_entities()
    entities_data: dict[str, dict] = {}
    for e in all_entities:
        e_path = os.path.join(vault_root, e["path"])
        if os.path.exists(e_path):
            with open(e_path, "r", encoding="utf-8") as f:
                e_content = f.read()
            e_parsed = parse_markdown(e_content, e_path)
            entities_data[e["path"]] = e_parsed

    change = Change(
        entity_path=entity_data["path"],
        entity_name=entity_name,
        entity_type=entity_data.get("wb_type", ""),
        change_type="update",
        field="*",
        full_entity=parsed,
    )

    suggestions = propagate_change(change, entities_data)
    return {
        "entity": entity_name,
        "suggestions": suggestions,
        "count": len(suggestions),
    }


def cmd_spatial(args, vault_root: str, config: dict) -> dict:
    place_name = args.place

    # Build spatial tree from all entities
    sqlite = get_sqlite(vault_root)
    all_entities = sqlite.get_all_entities()

    parsed_entities: list[dict] = []
    name_to_path: dict[str, str] = {}

    for e in all_entities:
        e_path = os.path.join(vault_root, e["path"])
        if os.path.exists(e_path):
            with open(e_path, "r", encoding="utf-8") as f:
                content = f.read()
            parsed = parse_markdown(content, e_path)
            parsed_entities.append(parsed)
            name = parsed["frontmatter"].get("name", "")
            if name:
                name_to_path[name] = e_path

    tree = build_spatial_tree(parsed_entities, name_to_path)

    # Find the target place
    target_path = name_to_path.get(place_name)
    if not target_path:
        return {"error": f"Place not found: {place_name}"}

    chain = get_containment_chain(tree, target_path)
    children = get_contained_entities(tree, target_path, max_depth=3)

    # Build readable output
    chain_names = []
    for p in chain:
        node = tree["nodes"].get(p, {})
        chain_names.append(node.get("name", p))

    child_names = []
    for p in children:
        node = tree["nodes"].get(p, {})
        child_names.append({"name": node.get("name", p), "type": node.get("wb_type", "")})

    return {
        "place": place_name,
        "containment_chain": chain_names,
        "contained_entities": child_names,
    }


def cmd_ensure_inverses(args, vault_root: str, config: dict) -> dict:
    """Ensure bidirectional relationship consistency."""
    from wb_core.relationship_sync import (
        ensure_inverses_for_entity,
        ensure_inverses_all,
    )

    do_apply = getattr(args, "apply", False)
    do_all = getattr(args, "all", False)

    if do_all:
        result = ensure_inverses_all(vault_root, apply=do_apply)
        # If we applied changes, sync modified files
        if do_apply and result["total_applied"] > 0:
            sync_full(vault_root, config)
        return result

    path = getattr(args, "path", None)
    if not path:
        return {"error": "Provide a file path or use --all"}

    result = ensure_inverses_for_entity(path, vault_root, apply=do_apply)
    # If we applied changes, sync modified targets
    if do_apply and result["applied"] > 0:
        sync_full(vault_root, config)
    return result


def cmd_calendar(args, vault_root: str, config: dict) -> dict:
    calendar_path = os.path.join(vault_root, "_meta", "calendar.md")
    if not os.path.exists(calendar_path):
        return {"error": "No calendar file found at _meta/calendar.md"}

    with open(calendar_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_markdown(content, calendar_path)
    return {
        "calendar": parsed["frontmatter"],
        "description": parsed["body"].strip()[:2000],
    }


# ---------------------------------------------------------------------------
# CLI setup
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wb",
        description="World Builder CLI — manage and query world-building data",
    )
    parser.add_argument(
        "--vault", default=".",
        help="Path to vault root (default: current directory)",
    )
    parser.add_argument(
        "--pretty", action="store_true",
        help="Pretty-print JSON output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Sync entity files to stores")
    sync_parser.add_argument("path", nargs="?", help="Path to a single .md file to sync")
    sync_parser.add_argument("--full", action="store_true", help="Full rebuild of all stores")
    sync_parser.add_argument("--status", action="store_true", help="Show sync health")
    sync_parser.add_argument("--verify", action="store_true", help="Verify store consistency")

    # query
    query_parser = subparsers.add_parser("query", help="Query entities across stores")
    query_parser.add_argument("--type", help="Filter by wb-type")
    query_parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    query_parser.add_argument("--name", help="Filter by name (substring match)")
    query_parser.add_argument("--within", help="Filter by parent place")
    query_parser.add_argument("--at", help="Resolve temporal state at this time")
    query_parser.add_argument("--related-to", help="Find entities related to this one (graph query)")
    query_parser.add_argument("--hops", type=int, help="Depth for graph traversal (default: 1)")
    query_parser.add_argument("--text", help="Free-text search (FTS)")
    query_parser.add_argument("--semantic", help="Semantic search query (vector)")

    # resolve
    resolve_parser = subparsers.add_parser("resolve", help="Resolve entity state at a time")
    resolve_parser.add_argument("entity", help="Entity name")
    resolve_parser.add_argument("--at", required=True, help="Time point (e.g. '500' or 'SA:200')")
    resolve_parser.add_argument("--type", help="Filter by wb-type for disambiguation (e.g. 'place')")

    # validate
    subparsers.add_parser("validate", help="Validate all entities")

    # propagate
    propagate_parser = subparsers.add_parser("propagate", help="Find affected entities after a change")
    propagate_parser.add_argument("entity", help="Entity name that changed")

    # spatial
    spatial_parser = subparsers.add_parser("spatial", help="Show spatial hierarchy")
    spatial_parser.add_argument("place", help="Place name")

    # calendar
    subparsers.add_parser("calendar", help="Display calendar info")

    # ensure-inverses
    inv_parser = subparsers.add_parser(
        "ensure-inverses",
        help="Ensure bidirectional relationship consistency",
    )
    inv_parser.add_argument(
        "path", nargs="?",
        help="Path to a single .md file (omit for --all)",
    )
    inv_parser.add_argument(
        "--all", action="store_true",
        help="Check all entities in the vault",
    )
    inv_parser.add_argument(
        "--apply", action="store_true",
        help="Apply missing inverses (default is dry-run)",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    vault_root = os.path.abspath(args.vault)
    if not os.path.isdir(vault_root):
        print(json.dumps({"error": f"Vault root not found: {vault_root}"}), file=sys.stderr)
        sys.exit(1)

    config = load_config(vault_root)

    command_map = {
        "sync": cmd_sync,
        "query": cmd_query,
        "resolve": cmd_resolve,
        "validate": cmd_validate,
        "propagate": cmd_propagate,
        "spatial": cmd_spatial,
        "calendar": cmd_calendar,
        "ensure-inverses": cmd_ensure_inverses,
    }

    handler = command_map.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(1)

    try:
        result = handler(args, vault_root, config)
    except Exception as e:
        result = {"error": str(e)}

    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, default=str))


if __name__ == "__main__":
    main()
