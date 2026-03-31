"""Hierarchical contextual chunking for entity embedding.

Splits entity documents into multiple chunks at different granularity levels,
each with a contextual prefix so embeddings capture meaning in isolation.

Chunk levels:
  - summary:     AI-generated thorough summary (caller provides)
  - frontmatter: Structured data as natural language
  - section:     Each ## heading block from the body
  - overflow:    If body > 8192 chars, split into equal chunks at paragraph boundaries
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from wb_core.frontmatter import strip_wikilink


MAX_CHUNK_CHARS = 8192


@dataclass
class Chunk:
    """A single embeddable chunk from an entity."""
    chunk_id: str          # e.g. "People.Kael'Zorai::section::The Paroxysm"
    text: str              # The text to embed (includes contextual prefix)
    level: str             # summary | frontmatter | section | overflow
    metadata: dict = field(default_factory=dict)


def _context_prefix(name: str, wb_type: str, aliases: list[str] | None = None,
                    section: str | None = None) -> str:
    """Build a contextual prefix for a chunk."""
    parts = [f"Entity: {name} ({wb_type})"]
    if aliases:
        parts[0] += f" also known as: {', '.join(aliases[:5])}"
    if section:
        parts.append(f"Section: {section}")
    return "\n".join(parts) + "\n---\n"


def _relationships_as_text(rels: list[dict], entity_name: str) -> str:
    """Convert relationship dicts to natural language."""
    lines: list[str] = []
    for rel in rels:
        if not isinstance(rel, dict):
            continue
        target = strip_wikilink(str(rel.get("target", "")))
        rel_type = rel.get("type", "related to").replace("-", " ")
        period = rel.get("period", "")
        note = rel.get("note", "") or rel.get("notes", "")

        line = f"{entity_name} {rel_type} {target}"
        if period:
            line += f" (during {period})"
        if note:
            line += f" — {note}"
        lines.append(line)
    return "\n".join(lines)


def _timeline_as_text(timeline: list[dict]) -> str:
    """Convert timeline entries to natural language."""
    lines: list[str] = []
    for entry in timeline:
        if not isinstance(entry, dict):
            continue
        period = entry.get("period", "")
        event = entry.get("event", "") or entry.get("label", "")
        if event:
            lines.append(f"{period}: {event}" if period else event)
    return "\n".join(lines)


def _split_sections(body: str) -> list[tuple[str, str]]:
    """Split body text by ## headings. Returns [(heading, content), ...]."""
    # Split on ## headings (level 2)
    pattern = re.compile(r'^## (.+)$', re.MULTILINE)
    matches = list(pattern.finditer(body))

    if not matches:
        return []

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        if content:
            sections.append((heading, content))

    return sections


def _split_overflow(text: str) -> list[str]:
    """Split text into roughly equal chunks at paragraph boundaries.

    Splits into int(len / 8192) + 1 chunks.
    """
    n_chunks = (len(text) // MAX_CHUNK_CHARS) + 1
    if n_chunks <= 1:
        return [text]

    target_size = len(text) // n_chunks
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        current.append(para)
        current_len += len(para) + 2  # +2 for \n\n

        if current_len >= target_size and len(chunks) < n_chunks - 1:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0

    # Last chunk gets whatever remains
    if current:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_entity(
    entity_id: str,
    name: str,
    wb_type: str,
    frontmatter: dict,
    body: str,
    summary: Optional[str] = None,
) -> list[Chunk]:
    """Produce hierarchical chunks from an entity.

    Parameters
    ----------
    entity_id : str
        The entity's store ID (e.g., "People.Kael'Zorai").
    name : str
        Display name.
    wb_type : str
        Entity type (person, place, etc.).
    frontmatter : dict
        Parsed YAML frontmatter.
    body : str
        Markdown body (after the --- delimiters).
    summary : str, optional
        Pre-generated AI summary. If provided, creates a summary chunk.

    Returns
    -------
    list[Chunk]
        All chunks for this entity, each with contextual prefix.
    """
    chunks: list[Chunk] = []
    aliases = frontmatter.get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]

    base_meta = {
        "entity_id": entity_id,
        "entity_name": name,
        "wb_type": wb_type,
    }

    # --- Summary chunk (if provided) ---
    if summary:
        prefix = _context_prefix(name, wb_type, aliases)
        chunks.append(Chunk(
            chunk_id=f"{entity_id}::summary",
            text=prefix + summary,
            level="summary",
            metadata={**base_meta, "chunk_level": "summary"},
        ))

    # --- Frontmatter chunk ---
    fm_parts: list[str] = []

    rels = frontmatter.get("relationships") or []
    if rels:
        rel_text = _relationships_as_text(rels, name)
        if rel_text:
            fm_parts.append("Relationships:\n" + rel_text)

    timeline = frontmatter.get("timeline") or []
    if timeline:
        tl_text = _timeline_as_text(timeline)
        if tl_text:
            fm_parts.append("Timeline:\n" + tl_text)

    tags = frontmatter.get("tags") or []
    if tags:
        fm_parts.append("Tags: " + ", ".join(str(t) for t in tags))

    # Add other useful frontmatter fields
    for key in ("origin", "role", "title", "habitat", "traits", "tenets", "goals"):
        val = frontmatter.get(key)
        if val:
            if isinstance(val, list):
                fm_parts.append(f"{key}: {', '.join(str(v) for v in val)}")
            else:
                fm_parts.append(f"{key}: {val}")

    if fm_parts:
        prefix = _context_prefix(name, wb_type, aliases)
        chunks.append(Chunk(
            chunk_id=f"{entity_id}::frontmatter",
            text=prefix + "\n".join(fm_parts),
            level="frontmatter",
            metadata={**base_meta, "chunk_level": "frontmatter"},
        ))

    # --- Section chunks ---
    sections = _split_sections(body)
    for heading, content in sections:
        prefix = _context_prefix(name, wb_type, aliases, section=heading)
        # Skip very short sections
        if len(content) < 50:
            continue
        chunks.append(Chunk(
            chunk_id=f"{entity_id}::section::{heading}",
            text=prefix + content,
            level="section",
            metadata={**base_meta, "chunk_level": "section", "section_name": heading},
        ))

    # --- Overflow chunks (if body > 8192 chars) ---
    if len(body) > MAX_CHUNK_CHARS:
        overflow_parts = _split_overflow(body)
        for i, part in enumerate(overflow_parts):
            prefix = _context_prefix(name, wb_type, aliases,
                                     section=f"Content part {i + 1} of {len(overflow_parts)}")
            chunks.append(Chunk(
                chunk_id=f"{entity_id}::overflow::{i}",
                text=prefix + part,
                level="overflow",
                metadata={**base_meta, "chunk_level": "overflow", "chunk_index": i},
            ))

    # --- Fallback: if no sections and body is short, embed the whole body ---
    if not sections and body.strip() and len(body) <= MAX_CHUNK_CHARS:
        prefix = _context_prefix(name, wb_type, aliases)
        chunks.append(Chunk(
            chunk_id=f"{entity_id}::body",
            text=prefix + body.strip(),
            level="body",
            metadata={**base_meta, "chunk_level": "body"},
        ))

    return chunks
