# World Builder

AI-powered world-building toolkit for Obsidian. Everything stored in Markdown with YAML frontmatter.

## Ground Rules

1. **Existing entity files are canonical truth.** Never contradict established lore. If unsure whether something is established, query or read the entity first.
2. **Never fabricate lore unprompted.** Only create, update, or delete entities when the user explicitly asks. Read-only operations (query, validate, timeline) are always safe.
3. **Show before writing.** In `ask` mode, always present proposed content and get user approval before writing files. In `autonomous` mode, write directly but log everything to `_meta/changelog.md`.
4. **Label what you invent.** When generating content, distinguish: (a) facts from existing entities, (b) logical inferences, (c) new content you are creating. Be transparent about category (c).
5. **Sparse over speculative.** Prefer leaving fields empty over filling them with guesses. Use `null` for unknown values.
6. **If a query returns nothing, say so.** Never fill gaps with plausible-sounding lore.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/wb-create` | Create entities with AI assistance |
| `/wb-query` | Query the world (structured, temporal, semantic) |
| `/wb-ingest` | Import unstructured text as entities |
| `/wb-suggest` | AI suggestions (characters, factions, plot) |
| `/wb-consequences` | Trace ripple effects of changes |
| `/wb-consistency` | Audit for contradictions and gaps |
| `/wb-write` | Generate narrative content |
| `/wb-timeline` | Compile timeline summaries |

## Python CLI

All data operations go through `wb.py`. Always use the venv Python:

```bash
# Unix/Mac
_meta/.wb-venv/bin/python .claude/skills/world-builder/_lib/wb.py <command>
# Windows
_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py <command>
```

Commands: `sync`, `query`, `resolve`, `validate`, `propagate`, `spatial`, `calendar`

## CRITICAL: Always sync after mutations

After creating, editing, or deleting any entity `.md` file, **always** run:
```bash
wb.py sync <path-to-changed-file>
```
For bulk operations, use `wb.py sync --full`.

## Entity Types

| Type | Folder | Key Fields |
|------|--------|------------|
| person | People/ | species, born, died, birthplace, residence, faction, role, title |
| place | World/ (hierarchy) | parent, spatial-type, population, ruler, faction, climate |
| event | Events/ | date, duration, location, participants, causes, consequences |
| faction | Factions/ | type, founded, dissolved, headquarters, leader, territory |
| religion | Religions/ | type, founded, founder, deities, tenets |
| government | Governments/ | type, founded, territory, leader, capital |
| species | Species/ | origin, lifespan, traits, habitat |
| magic | Magic/ | type, source, practitioners, limitations |
| technology | Technology/ | type, inventor, invented, used-by |
| item | Items/ | type, owner, creator, location, properties, magical |
| narrative | Stories/ or Lore/ | narrative-type, story, chapter, period, pov |

## Frontmatter Format

All entities use YAML frontmatter with `wb-type` as the discriminator:

```yaml
---
wb-type: person
wb-id: queen-mirael
name: Queen Mirael
aliases: [The Silver Queen]
tags: [person, ruler]
relationships:
  - target: "[[King Aldric]]"
    type: spouse
    period: "495-"
timeline:
  - period: "480-495"
    label: "Princess of Valdris"
    role: princess
  - period: "495-"
    label: "Queen of Eldara"
    role: queen
created: 2026-03-15
modified: 2026-03-15
---
```

## Period Formats

| Format | Example | Meaning |
|--------|---------|---------|
| Point | `"500"` | Year 500 |
| Range | `"200-500"` | Years 200 to 500 |
| Ongoing | `"501-"` | From year 501 onward |
| Era point | `"SA:200"` | Second Age year 200 |
| Era range | `"SA:200-SA:500"` | SA 200 to SA 500 |
| Cross-era | `"FA:800-SA:100"` | First Age 800 to Second Age 100 |

Eras configured in `_meta/calendar.md`.

## Wikilinks

Use `[[Entity Name]]` for ALL cross-references. This enables:
- Obsidian graph view and backlinks
- Automatic relationship tracking in the graph store
- Wikilink-based entity resolution

## Relationships

Use the `relationships` array in frontmatter. Each relationship has:
- `target`: wikilink to the related entity
- `type`: relationship type (see inverse pairs below)
- `period`: optional time period
- `notes`: optional description

**Inverse pairs** (automatically tracked bidirectionally):
parent-of/child-of, mentor-of/student-of, leader-of/led-by, member-of/has-member, controls/controlled-by, serves/served-by, worships/worshipped-by, created/created-by, vassal-of/overlord-of, successor-of/predecessor-of

**Symmetric** (same in both directions): ally, enemy, spouse, sibling, rival, friend, trades-with

## Autonomy Mode

Configured in `_meta/wb-config.md` field `mode`:
- `ask` (default): AI proposes changes and waits for approval
- `autonomous`: AI applies changes directly, logs to `_meta/changelog.md`

## Three-Store Architecture

Markdown files are the source of truth. Three derived stores stay in sync:
1. **SQLite** (`_meta/wb.db`): Structured queries, full-text search
2. **NetworkX** (`_meta/wb-graph.json`): Relationship graph traversal
3. **ChromaDB** (`_meta/chroma/`): Semantic vector search with metadata filtering

Always sync after changes. Use `wb.py sync --verify` to check consistency.
