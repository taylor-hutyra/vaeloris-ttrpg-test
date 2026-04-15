"""Embedding cache — portable across clones.

Lives in a dedicated SQLite file (`_meta/embedding_cache.db`) so it can be
committed to version control without dragging along the rest of the derived
world-builder state. Keyed on (text_hash, model) → vector bytes.

The cache makes ChromaDB disposable: if the vector store corrupts or is
missing (fresh clone, wiped directory, OS migration), `sync --full` rebuilds
it from these cached vectors at zero OpenAI cost.
"""

from __future__ import annotations

import os
import sqlite3


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS embedding_cache (
    text_hash TEXT NOT NULL,
    model TEXT NOT NULL,
    dims INTEGER NOT NULL,
    vector BLOB NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (text_hash, model)
);
"""


class EmbeddingCacheStore:
    """Portable SQLite-backed cache of (text, model) → embedding vector."""

    def __init__(self, vault_root: str):
        self.vault_root = vault_root
        meta_dir = os.path.join(vault_root, "_meta")
        os.makedirs(meta_dir, exist_ok=True)
        self.db_path = os.path.join(meta_dir, "embedding_cache.db")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # WAL mode has better concurrent-read behavior and matches wb.db setup.
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(_SCHEMA_SQL)
        self.conn.commit()

    def get(self, text_hashes: list[str], model: str) -> dict[str, bytes]:
        if not text_hashes:
            return {}
        placeholders = ",".join("?" * len(text_hashes))
        rows = self.conn.execute(
            f"SELECT text_hash, vector FROM embedding_cache "
            f"WHERE model = ? AND text_hash IN ({placeholders})",
            (model, *text_hashes),
        ).fetchall()
        return {row["text_hash"]: row["vector"] for row in rows}

    def put(self, entries: list[tuple[str, str, int, bytes]]) -> None:
        """entries = [(text_hash, model, dims, vector_bytes), ...]."""
        if not entries:
            return
        self.conn.executemany(
            "INSERT OR REPLACE INTO embedding_cache "
            "(text_hash, model, dims, vector) VALUES (?, ?, ?, ?)",
            entries,
        )
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) as c FROM embedding_cache"
        ).fetchone()["c"]
