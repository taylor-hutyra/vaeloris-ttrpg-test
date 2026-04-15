"""SQLite store for structured entity data.

Database file lives at _meta/wb.db relative to vault root.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wb_core.frontmatter import strip_wikilink
from wb_core.period import parse_period


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT,
    wb_type TEXT,
    path TEXT UNIQUE,
    aliases TEXT,
    tags TEXT,
    parent TEXT,
    created TEXT,
    modified TEXT,
    content_hash TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    target_id TEXT,
    rel_type TEXT,
    period TEXT,
    notes TEXT,
    FOREIGN KEY(source_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,
    period_start REAL,
    period_end REAL,
    label TEXT,
    state_json TEXT,
    FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS tags (
    entity_id TEXT,
    tag TEXT,
    PRIMARY KEY(entity_id, tag)
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_entities USING fts5(
    name, aliases, body_text
);

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,
    store TEXT,
    action TEXT,
    timestamp TEXT,
    content_hash TEXT
);

-- Tracks which chunk IDs belong to which entity. Used for safe orphan
-- deletion via delete(ids=...) — chromadb's delete/get(where=...) Rust
-- binding segfaults on Windows, so we avoid it entirely.
CREATE TABLE IF NOT EXISTS entity_chunks (
    entity_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    PRIMARY KEY (entity_id, chunk_id)
);
CREATE INDEX IF NOT EXISTS idx_entity_chunks_entity ON entity_chunks(entity_id);

CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_timeline_entity ON timeline(entity_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(wb_type);
CREATE INDEX IF NOT EXISTS idx_entities_parent ON entities(parent);
"""


class SqliteStore:
    """SQLite-backed structured store for world-builder entities."""

    def __init__(self, vault_root: str):
        self.vault_root = vault_root
        meta_dir = os.path.join(vault_root, "_meta")
        os.makedirs(meta_dir, exist_ok=True)
        db_path = os.path.join(meta_dir, "wb.db")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self):
        """Run schema creation / migration."""
        self.conn.executescript(_SCHEMA_SQL)
        self.conn.commit()

    def upsert_entity(
        self,
        entity_id: str,
        frontmatter: dict,
        body: str,
        path: str,
        content_hash: str,
    ):
        """Insert or update an entity across all tables."""
        name = frontmatter.get("name", os.path.basename(path).replace(".md", ""))
        wb_type = frontmatter.get("wb-type", "")
        aliases = json.dumps(frontmatter.get("aliases", []))
        tags_list = frontmatter.get("tags", [])
        if not isinstance(tags_list, list):
            tags_list = []
        tags_json = json.dumps(tags_list)
        parent_raw = frontmatter.get("parent", "")
        parent = strip_wikilink(str(parent_raw)) if parent_raw else ""
        now = datetime.now(timezone.utc).isoformat()

        # Check if entity exists to preserve created timestamp
        existing = self.conn.execute(
            "SELECT created FROM entities WHERE id = ?", (entity_id,)
        ).fetchone()
        created = existing["created"] if existing else now

        self.conn.execute(
            """INSERT INTO entities (id, name, wb_type, path, aliases, tags, parent, created, modified, content_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, wb_type=excluded.wb_type, path=excluded.path,
                 aliases=excluded.aliases, tags=excluded.tags, parent=excluded.parent,
                 modified=excluded.modified, content_hash=excluded.content_hash""",
            (entity_id, name, wb_type, path, aliases, tags_json, parent, created, now, content_hash),
        )

        # --- Relationships ---
        self.conn.execute("DELETE FROM relationships WHERE source_id = ?", (entity_id,))
        rels = frontmatter.get("relationships", [])
        if isinstance(rels, list):
            for rel in rels:
                if not isinstance(rel, dict):
                    continue
                target_raw = rel.get("target", "")
                target_name = strip_wikilink(str(target_raw))
                rel_type = rel.get("type", "")
                period = rel.get("period", "")
                notes = rel.get("notes", "")
                # Use target name as target_id (will be resolved to actual id if available)
                self.conn.execute(
                    "INSERT INTO relationships (source_id, target_id, rel_type, period, notes) VALUES (?, ?, ?, ?, ?)",
                    (entity_id, target_name, rel_type, str(period), notes),
                )

        # --- Timeline ---
        self.conn.execute("DELETE FROM timeline WHERE entity_id = ?", (entity_id,))
        timeline_entries = frontmatter.get("timeline", [])
        if isinstance(timeline_entries, list):
            for entry in timeline_entries:
                if not isinstance(entry, dict):
                    continue
                period_str = entry.get("period")
                if not period_str:
                    continue
                try:
                    parsed = parse_period(str(period_str))
                    period_start = float(parsed.start.year)
                    period_end = float(parsed.end.year) if parsed.end is not None else None
                except (ValueError, TypeError):
                    period_start = 0.0
                    period_end = None
                label = entry.get("label", "")
                state = {k: v for k, v in entry.items() if k not in ("period", "label")}
                self.conn.execute(
                    "INSERT INTO timeline (entity_id, period_start, period_end, label, state_json) VALUES (?, ?, ?, ?, ?)",
                    (entity_id, period_start, period_end, label, json.dumps(state)),
                )

        # --- Tags ---
        self.conn.execute("DELETE FROM tags WHERE entity_id = ?", (entity_id,))
        for tag in tags_list:
            self.conn.execute(
                "INSERT OR IGNORE INTO tags (entity_id, tag) VALUES (?, ?)",
                (entity_id, str(tag)),
            )

        # --- FTS ---
        self.conn.execute("DELETE FROM fts_entities WHERE rowid IN (SELECT rowid FROM fts_entities WHERE name = ?)", (name,))
        # Use a deterministic rowid approach: delete any existing FTS row for this entity
        # and reinsert. We use the entity's hash to find it.
        self.conn.execute(
            "INSERT INTO fts_entities (name, aliases, body_text) VALUES (?, ?, ?)",
            (name, " ".join(frontmatter.get("aliases", [])), body[:5000]),
        )

        self.conn.commit()

    def remove_entity(self, entity_id: str):
        """Remove an entity and all its related data."""
        # Get name for FTS cleanup
        row = self.conn.execute("SELECT name FROM entities WHERE id = ?", (entity_id,)).fetchone()
        if row:
            name = row["name"]
            self.conn.execute("DELETE FROM fts_entities WHERE name = ?", (name,))

        self.conn.execute("DELETE FROM relationships WHERE source_id = ? OR target_id = ?", (entity_id, entity_id))
        self.conn.execute("DELETE FROM timeline WHERE entity_id = ?", (entity_id,))
        self.conn.execute("DELETE FROM tags WHERE entity_id = ?", (entity_id,))
        self.conn.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
        self.conn.commit()

    def query(
        self,
        type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        name: Optional[str] = None,
        within: Optional[str] = None,
        related_to: Optional[str] = None,
        free_text: Optional[str] = None,
    ) -> list[dict]:
        """Query entities with optional filters."""
        conditions = []
        params = []

        if type:
            conditions.append("e.wb_type = ?")
            params.append(type)

        if name:
            conditions.append("e.name LIKE ?")
            params.append(f"%{name}%")

        if within:
            conditions.append("e.parent = ?")
            params.append(within)

        base_query = "SELECT DISTINCT e.* FROM entities e"
        joins = []

        if tags:
            joins.append("JOIN tags t ON e.id = t.entity_id")
            placeholders = ",".join("?" for _ in tags)
            conditions.append(f"t.tag IN ({placeholders})")
            params.extend(tags)

        if related_to:
            joins.append(
                "LEFT JOIN relationships r ON (e.id = r.source_id OR e.id = r.target_id)"
            )
            conditions.append("(r.source_id = ? OR r.target_id = ?)")
            params.extend([related_to, related_to])

        sql = base_query
        for j in joins:
            sql += f" {j}"

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        rows = self.conn.execute(sql, params).fetchall()
        results = [dict(row) for row in rows]

        # Free-text search via FTS
        if free_text:
            fts_rows = self.conn.execute(
                "SELECT name FROM fts_entities WHERE fts_entities MATCH ?",
                (free_text,),
            ).fetchall()
            fts_names = {row["name"] for row in fts_rows}
            if results:
                results = [r for r in results if r["name"] in fts_names]
            else:
                # FTS-only query
                name_list = ",".join("?" for _ in fts_names)
                if fts_names:
                    rows = self.conn.execute(
                        f"SELECT * FROM entities WHERE name IN ({name_list})",
                        list(fts_names),
                    ).fetchall()
                    results = [dict(row) for row in rows]

        # Deserialize JSON fields for output
        for r in results:
            try:
                r["aliases"] = json.loads(r.get("aliases", "[]"))
            except (json.JSONDecodeError, TypeError):
                r["aliases"] = []
            try:
                r["tags"] = json.loads(r.get("tags", "[]"))
            except (json.JSONDecodeError, TypeError):
                r["tags"] = []

        return results

    def get_entity(self, entity_id: str) -> Optional[dict]:
        """Get a single entity by ID."""
        row = self.conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        try:
            result["aliases"] = json.loads(result.get("aliases", "[]"))
        except (json.JSONDecodeError, TypeError):
            result["aliases"] = []
        try:
            result["tags"] = json.loads(result.get("tags", "[]"))
        except (json.JSONDecodeError, TypeError):
            result["tags"] = []

        # Attach relationships
        rels = self.conn.execute(
            "SELECT * FROM relationships WHERE source_id = ?", (entity_id,)
        ).fetchall()
        result["relationships"] = [dict(r) for r in rels]

        # Attach timeline
        tl = self.conn.execute(
            "SELECT * FROM timeline WHERE entity_id = ? ORDER BY period_start",
            (entity_id,),
        ).fetchall()
        result["timeline"] = [dict(t) for t in tl]

        return result

    def get_all_entities(self) -> list[dict]:
        """Get all entities."""
        rows = self.conn.execute("SELECT * FROM entities").fetchall()
        results = []
        for row in rows:
            r = dict(row)
            try:
                r["aliases"] = json.loads(r.get("aliases", "[]"))
            except (json.JSONDecodeError, TypeError):
                r["aliases"] = []
            try:
                r["tags"] = json.loads(r.get("tags", "[]"))
            except (json.JSONDecodeError, TypeError):
                r["tags"] = []
            results.append(r)
        return results

    def log_sync(self, entity_id: str, store: str, action: str, content_hash: str):
        """Log a sync event."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO sync_log (entity_id, store, action, timestamp, content_hash) VALUES (?, ?, ?, ?, ?)",
            (entity_id, store, action, now, content_hash),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Entity chunk tracking (for safe orphan deletion)
    # ------------------------------------------------------------------

    def get_entity_chunk_ids(self, entity_id: str) -> list[str]:
        """Return chunk IDs previously stored for this entity."""
        rows = self.conn.execute(
            "SELECT chunk_id FROM entity_chunks WHERE entity_id = ?",
            (entity_id,),
        ).fetchall()
        return [row["chunk_id"] for row in rows]

    def set_entity_chunk_ids(self, entity_id: str, chunk_ids: list[str]) -> None:
        """Replace the set of chunk IDs for this entity."""
        self.conn.execute("DELETE FROM entity_chunks WHERE entity_id = ?", (entity_id,))
        if chunk_ids:
            self.conn.executemany(
                "INSERT INTO entity_chunks (entity_id, chunk_id) VALUES (?, ?)",
                [(entity_id, cid) for cid in chunk_ids],
            )
        self.conn.commit()

    def get_sync_status(self) -> dict:
        """Return sync health info."""
        entity_count = self.conn.execute("SELECT COUNT(*) as c FROM entities").fetchone()["c"]
        rel_count = self.conn.execute("SELECT COUNT(*) as c FROM relationships").fetchone()["c"]
        tl_count = self.conn.execute("SELECT COUNT(*) as c FROM timeline").fetchone()["c"]

        last_sync = self.conn.execute(
            "SELECT MAX(timestamp) as ts FROM sync_log"
        ).fetchone()["ts"]

        log_count = self.conn.execute("SELECT COUNT(*) as c FROM sync_log").fetchone()["c"]

        return {
            "entity_count": entity_count,
            "relationship_count": rel_count,
            "timeline_count": tl_count,
            "last_sync": last_sync,
            "sync_log_entries": log_count,
        }

    def close(self):
        """Close the database connection."""
        self.conn.close()
