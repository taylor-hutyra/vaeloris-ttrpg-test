"""ChromaDB vector store for semantic search.

Persistent storage at _meta/chroma/ relative to vault root.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import chromadb

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wb_core.frontmatter import strip_wikilink


def build_embedding_text(frontmatter: dict, body: str) -> str:
    """Build a text string suitable for embedding from entity data.

    Combines: entity name, type, description (first 500 chars of body),
    relationships as natural language, key timeline events.
    """
    parts: list[str] = []

    name = frontmatter.get("name", "")
    wb_type = frontmatter.get("wb-type", "")
    if name:
        parts.append(f"{name} ({wb_type})" if wb_type else name)

    # Description: first 500 chars of body
    if body:
        desc = body.strip()[:500]
        if desc:
            parts.append(desc)

    # Relationships as natural language
    rels = frontmatter.get("relationships", [])
    if isinstance(rels, list):
        rel_strs: list[str] = []
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            target = strip_wikilink(str(rel.get("target", "")))
            rel_type = rel.get("type", "related to")
            if target:
                # Make it read naturally
                rel_strs.append(f"{rel_type.replace('-', ' ')} {target}")
        if rel_strs:
            parts.append("Relationships: " + ", ".join(rel_strs))

    # Timeline events
    timeline = frontmatter.get("timeline", [])
    if isinstance(timeline, list):
        tl_strs: list[str] = []
        for entry in timeline[:10]:  # limit to 10 entries
            if not isinstance(entry, dict):
                continue
            label = entry.get("label", "")
            period = entry.get("period", "")
            if label:
                tl_strs.append(f"{period}: {label}" if period else label)
        if tl_strs:
            parts.append("Timeline: " + "; ".join(tl_strs))

    # Tags
    tags = frontmatter.get("tags", [])
    if isinstance(tags, list) and tags:
        parts.append("Tags: " + ", ".join(str(t) for t in tags))

    return "\n".join(parts)


def _build_metadata(frontmatter: dict) -> dict:
    """Build ChromaDB-compatible metadata dict (values must be str/int/float)."""
    meta: dict[str, Any] = {}

    wb_type = frontmatter.get("wb-type", "")
    if wb_type:
        meta["wb_type"] = str(wb_type)

    tags = frontmatter.get("tags", [])
    if isinstance(tags, list) and tags:
        meta["tags"] = ",".join(str(t) for t in tags)

    parent = frontmatter.get("parent", "")
    if parent:
        meta["parent_place"] = strip_wikilink(str(parent))

    # Extract era from period if available
    period_str = frontmatter.get("period", "")
    if period_str and ":" in str(period_str):
        era = str(period_str).split(":")[0]
        meta["era"] = era

    # Period start/end for filtering
    from wb_core.period import parse_period
    period_raw = frontmatter.get("period", "")
    if period_raw:
        try:
            parsed = parse_period(str(period_raw))
            meta["period_start"] = float(parsed.start.year)
            if parsed.end is not None:
                meta["period_end"] = float(parsed.end.year)
        except (ValueError, TypeError):
            pass

    return meta


class VectorStore:
    """ChromaDB-backed vector store for semantic search."""

    def __init__(self, vault_root: str, embedding_provider=None):
        self.vault_root = vault_root
        self.embedding_provider = embedding_provider
        chroma_path = os.path.join(vault_root, "_meta", "chroma")
        os.makedirs(chroma_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=chroma_path)

        # Create or get the collection
        # If we have an embedding provider, we handle embeddings ourselves
        self.collection = self.client.get_or_create_collection(
            name="wb_entities",
            metadata={"hnsw:space": "cosine"},
        )

    def set_embedding_provider(self, provider) -> None:
        """Set the embedding provider."""
        self.embedding_provider = provider

    def upsert_entity(self, entity_id: str, text: str, metadata: dict) -> None:
        """Embed text and store with metadata."""
        if self.embedding_provider:
            embedding = self.embedding_provider.embed_one(text)
            self.collection.upsert(
                ids=[entity_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
            )
        else:
            # Store without embeddings (ChromaDB will use its default)
            self.collection.upsert(
                ids=[entity_id],
                documents=[text],
                metadatas=[metadata],
            )

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from the vector store."""
        try:
            self.collection.delete(ids=[entity_id])
        except Exception:
            pass  # Entity may not exist

    def search(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> list[dict]:
        """Semantic search with optional metadata filtering."""
        kwargs: dict[str, Any] = {
            "n_results": min(n_results, self.count()) if self.count() > 0 else n_results,
        }

        if self.count() == 0:
            return []

        if where:
            kwargs["where"] = where
        if where_document:
            kwargs["where_document"] = where_document

        if self.embedding_provider:
            embedding = self.embedding_provider.embed_one(query_text)
            kwargs["query_embeddings"] = [embedding]
        else:
            kwargs["query_texts"] = [query_text]

        results = self.collection.query(**kwargs)

        # Format results
        output: list[dict] = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            documents = results["documents"][0] if results.get("documents") else [None] * len(ids)
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            distances = results["distances"][0] if results.get("distances") else [None] * len(ids)

            for i, eid in enumerate(ids):
                output.append({
                    "id": eid,
                    "document": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i],
                })

        return output

    def get_all_ids(self) -> list[str]:
        """Get all entity IDs in the collection."""
        result = self.collection.get()
        return result["ids"] if result and result["ids"] else []

    def count(self) -> int:
        """Get the number of entities in the collection."""
        return self.collection.count()
