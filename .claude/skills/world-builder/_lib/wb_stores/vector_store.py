"""ChromaDB vector store for semantic search.

Supports hierarchical chunking: multiple chunks per entity at different
granularity levels (summary, frontmatter, section, overflow).

Persistent storage at _meta/chroma/ relative to vault root.
"""

from __future__ import annotations

import hashlib
import os
import struct
from typing import Any, Optional

import chromadb

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wb_core.frontmatter import strip_wikilink


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _vector_to_bytes(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _bytes_to_vector(buf: bytes) -> list[float]:
    n = len(buf) // 4
    return list(struct.unpack(f"{n}f", buf))


# ---------------------------------------------------------------------------
# Legacy helpers (kept for backward compat with old sync code)
# ---------------------------------------------------------------------------

def build_embedding_text(frontmatter: dict, body: str) -> str:
    """Build a single text string for embedding (legacy flat approach)."""
    parts: list[str] = []

    name = frontmatter.get("name", "")
    wb_type = frontmatter.get("wb-type", "")
    if name:
        parts.append(f"{name} ({wb_type})" if wb_type else name)

    if body:
        desc = body.strip()[:500]
        if desc:
            parts.append(desc)

    rels = frontmatter.get("relationships", [])
    if isinstance(rels, list):
        rel_strs: list[str] = []
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            target = strip_wikilink(str(rel.get("target", "")))
            rel_type = rel.get("type", "related to")
            if target:
                rel_strs.append(f"{rel_type.replace('-', ' ')} {target}")
        if rel_strs:
            parts.append("Relationships: " + ", ".join(rel_strs))

    timeline = frontmatter.get("timeline", [])
    if isinstance(timeline, list):
        tl_strs: list[str] = []
        for entry in timeline[:10]:
            if not isinstance(entry, dict):
                continue
            label = entry.get("label", "") or entry.get("event", "")
            period = entry.get("period", "")
            if label:
                tl_strs.append(f"{period}: {label}" if period else label)
        if tl_strs:
            parts.append("Timeline: " + "; ".join(tl_strs))

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

    period_str = frontmatter.get("period", "")
    if period_str and ":" in str(period_str):
        era = str(period_str).split(":")[0]
        meta["era"] = era

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


# ---------------------------------------------------------------------------
# VectorStore
# ---------------------------------------------------------------------------

class VectorStore:
    """ChromaDB-backed vector store with hierarchical chunk support."""

    def __init__(
        self,
        vault_root: str,
        embedding_provider=None,
        sqlite_store=None,
        embedding_cache=None,
    ):
        self.vault_root = vault_root
        self.embedding_provider = embedding_provider
        self.sqlite_store = sqlite_store  # For entity_chunks ID tracking
        self.embedding_cache = embedding_cache  # Portable (text_hash, model) -> vec
        chroma_path = os.path.join(vault_root, "_meta", "chroma")
        os.makedirs(chroma_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=chroma_path)

        # Legacy collection (flat, one embedding per entity)
        self.collection = self.client.get_or_create_collection(
            name="wb_entities",
            metadata={"hnsw:space": "cosine"},
        )

        # Chunked collection (hierarchical, multiple embeddings per entity)
        self.chunks_collection = self.client.get_or_create_collection(
            name="wb_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def _embed_with_cache(self, texts: list[str]) -> list[list[float]]:
        """Embed texts, consulting embedding_cache first.

        Cache-miss texts are sent to the embedding provider in one batch, then
        their vectors are persisted before being returned. If no cache or
        embedding_provider is configured, falls through to the provider.
        """
        if not texts:
            return []
        if not self.embedding_provider:
            return [[] for _ in texts]
        if not self.embedding_cache:
            return self.embedding_provider.embed(texts)

        model = getattr(self.embedding_provider, "model", "unknown")
        dims = self.embedding_provider.dimensions

        hashes = [_hash_text(t) for t in texts]
        cached = self.embedding_cache.get(list(set(hashes)), model)

        # Figure out which texts we need to actually embed
        miss_indices = [i for i, h in enumerate(hashes) if h not in cached]
        miss_texts = [texts[i] for i in miss_indices]

        new_entries: list[tuple[str, str, int, bytes]] = []
        if miss_texts:
            new_vectors = self.embedding_provider.embed(miss_texts)
            for idx, vec in zip(miss_indices, new_vectors):
                h = hashes[idx]
                buf = _vector_to_bytes(vec)
                cached[h] = buf
                new_entries.append((h, model, dims, buf))
            self.embedding_cache.put(new_entries)

        return [_bytes_to_vector(cached[h]) for h in hashes]

    def set_embedding_provider(self, provider) -> None:
        self.embedding_provider = provider

    # ------------------------------------------------------------------
    # Legacy single-embedding methods (kept for backward compat)
    # ------------------------------------------------------------------

    def upsert_entity(self, entity_id: str, text: str, metadata: dict) -> None:
        """Embed text and store with metadata (legacy flat approach)."""
        if self.embedding_provider:
            embedding = self._embed_with_cache([text])[0]
            self.collection.upsert(
                ids=[entity_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
            )
        else:
            self.collection.upsert(
                ids=[entity_id],
                documents=[text],
                metadatas=[metadata],
            )

    # ------------------------------------------------------------------
    # Hierarchical chunk methods
    # ------------------------------------------------------------------

    def upsert_chunks(self, entity_id: str, chunks: list) -> int:
        """Store multiple chunks for an entity.

        Parameters
        ----------
        entity_id : str
            The parent entity ID (used to delete old chunks before upserting).
        chunks : list[Chunk]
            Chunk objects from wb_core.chunking.chunk_entity().

        Returns
        -------
        int
            Number of chunks stored.
        """
        if not chunks:
            # Entity now has no chunks — still purge any orphans from before.
            self._remove_entity_chunks(entity_id)
            if self.sqlite_store:
                self.sqlite_store.set_entity_chunk_ids(entity_id, [])
            return 0

        # Batch embed all chunks at once for efficiency
        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [self._chunk_meta(c) for c in chunks]

        # Delete any previously-tracked chunk IDs for this entity that are
        # NOT in the new set (orphans from removed sections).
        new_id_set = set(ids)
        if self.sqlite_store:
            old_ids = self.sqlite_store.get_entity_chunk_ids(entity_id)
            orphan_ids = [i for i in old_ids if i not in new_id_set]
            if orphan_ids:
                try:
                    self.chunks_collection.delete(ids=orphan_ids)
                except Exception:
                    pass
        else:
            # Fallback (no sqlite): use the legacy where-based removal.
            self._remove_entity_chunks(entity_id)

        if self.embedding_provider:
            embeddings = self._embed_with_cache(texts)
            self.chunks_collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
        else:
            self.chunks_collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
            )

        if self.sqlite_store:
            self.sqlite_store.set_entity_chunk_ids(entity_id, ids)

        return len(chunks)

    def _chunk_meta(self, chunk) -> dict:
        """Convert Chunk metadata to ChromaDB-compatible dict."""
        meta = {}
        for k, v in chunk.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                meta[k] = v
            elif v is not None:
                meta[k] = str(v)
        return meta

    def _remove_entity_chunks(self, entity_id: str) -> None:
        """Remove all chunks belonging to an entity.

        Uses delete(where=...) directly — chromadb's Rust binding for
        get(where=...) segfaults on Windows when the collection is in certain
        states. delete(where=...) takes the same filter and is a no-op when
        nothing matches, so we skip the probe step entirely.
        """
        try:
            self.chunks_collection.delete(where={"entity_id": entity_id})
        except Exception:
            # Collection might be empty or entity doesn't exist — not an error.
            pass

    def search_chunks(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[dict] = None,
        deduplicate_entities: bool = True,
    ) -> list[dict]:
        """Semantic search across all chunk levels.

        Parameters
        ----------
        query_text : str
            Natural language query.
        n_results : int
            Max results to return.
        where : dict, optional
            ChromaDB metadata filter (e.g., {"wb_type": "person"}).
        deduplicate_entities : bool
            If True, return only the best-matching chunk per entity.

        Returns
        -------
        list[dict]
            Results with: entity_id, entity_name, chunk_level, section_name,
            distance, document snippet.
        """
        chunk_count = self.chunks_collection.count()
        if chunk_count == 0:
            return []

        kwargs: dict[str, Any] = {
            # Fetch more than needed if we'll deduplicate
            "n_results": min(n_results * 3, chunk_count) if deduplicate_entities else min(n_results, chunk_count),
        }

        if where:
            kwargs["where"] = where

        if self.embedding_provider:
            embedding = self.embedding_provider.embed_one(query_text)
            kwargs["query_embeddings"] = [embedding]
        else:
            kwargs["query_texts"] = [query_text]

        results = self.chunks_collection.query(**kwargs)

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        documents = results["documents"][0] if results.get("documents") else [None] * len(ids)
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [None] * len(ids)

        output: list[dict] = []
        seen_entities: set[str] = set()

        for i, cid in enumerate(ids):
            meta = metadatas[i] or {}
            entity_id = meta.get("entity_id", cid.split("::")[0])

            if deduplicate_entities:
                if entity_id in seen_entities:
                    continue
                seen_entities.add(entity_id)

            output.append({
                "entity_id": entity_id,
                "entity_name": meta.get("entity_name", ""),
                "wb_type": meta.get("wb_type", ""),
                "chunk_id": cid,
                "chunk_level": meta.get("chunk_level", ""),
                "section_name": meta.get("section_name", ""),
                "distance": distances[i],
                "document": documents[i][:200] if documents[i] else "",
            })

            if len(output) >= n_results:
                break

        return output

    # ------------------------------------------------------------------
    # Unified search (tries chunks first, falls back to legacy)
    # ------------------------------------------------------------------

    def search(
        self,
        query_text: str,
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> list[dict]:
        """Semantic search — uses chunk collection if populated, legacy otherwise."""
        # Prefer chunks collection
        if self.chunks_collection.count() > 0:
            return self.search_chunks(query_text, n_results=n_results, where=where)

        # Fall back to legacy
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

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from both legacy and chunks collections."""
        try:
            self.collection.delete(ids=[entity_id])
        except Exception:
            pass
        self._remove_entity_chunks(entity_id)

    def get_all_ids(self) -> list[str]:
        result = self.collection.get()
        return result["ids"] if result and result["ids"] else []

    def count(self) -> int:
        return self.collection.count()

    def chunk_count(self) -> int:
        return self.chunks_collection.count()
