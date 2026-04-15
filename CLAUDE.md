# World Builder

AI-powered world-building toolkit. Everything stored in Markdown with YAML frontmatter.

## Working Scope (Campaign vs. Canonical World)

**All active work happens inside `Campaign/`.** The canonical world — root-level `World/`, `People/`, `Factions/`, `Religions/`, `Species/`, `Events/`, `Magic/`, `Technology/`, `Items/`, `Governments/`, `Lore/`, `Stories/` — is frozen reference material. The campaign is *based off* the canonical world but is **not** being merged into it until the campaign concludes.

- New entities, session prep, NPCs, and locations for the active campaign go under `Campaign/` mirroring the root structure (e.g. `Campaign/World/Vael/...`, `Campaign/People/...`, `Campaign/Factions/...`).
- Do **not** create or modify files in root-level canonical folders unless the user explicitly requests a canonical change.
- Do **not** create entity files at the repo root (e.g. `/Lux Æterna.md`). Campaign entities live under `Campaign/`.
- Wikilinks from Campaign files **may** reference canonical entities (e.g. `[[Lothari Desert]]`) — that's expected read-only reference, not a merge.

### Markdown formatting & tooling

We use Obsidian-style wikilinks (`[[Name]]`) and YAML frontmatter for convenience, but **we are not using Obsidian** — the vault must work with plain filesystem tooling first, with future Obsidian compatibility. Practical implications:

- Wikilinks resolve by **filename** (Obsidian) or **frontmatter `name`** (wb.py). For a folder with rich content, use the folder-note pattern: `Foo/Foo.md` rather than `Foo/_index.md`, so `[[Foo]]` resolves in both worlds.
- Do not rely on Obsidian-only plugins (Dataview, folder-note, etc.) for anything load-bearing.

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

Commands: `sync`, `query`, `resolve`, `validate`, `propagate`, `spatial`, `calendar`, `ensure-inverses`

## CRITICAL: Always sync and propagate after mutations

After creating, editing, or deleting any entity `.md` file, **always**:

1. Sync the changed file:
```bash
wb.py sync <path-to-changed-file>
```

2. Propagate inverse relationships to target entities:
```bash
wb.py ensure-inverses <path-to-changed-file> --apply
```

For bulk operations, use `wb.py sync --full` and `wb.py ensure-inverses --all --apply`.

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
- Automatic relationship tracking in the graph store
- Wikilink-based entity resolution

## Relationships — Canonical Types (26 + custom)

Use ONLY these types. Specifics go in `metadata` dict. Be abstract: `sibling` not `brother`, `parent` not `father`.

| Category | Types |
|----------|-------|
| **Kinship** | `parent`, `child`, `sibling`, `spouse`, `identity` |
| **Creation** | `creator`, `created-by`, `founder`, `founded-by`, `origin`, `origin-of` |
| **Authority** | `ruler`, `ruled-by`, `member`, `has-member`, `controls`, `controlled-by`, `serves`, `served-by`, `successor`, `predecessor` |
| **Knowledge** | `teacher`, `student`, `worships`, `worshipped-by` |
| **Diplomacy** | `ally`, `enemy`, `rival`, `trade` (all symmetric) |
| **Spatial** | `located-in`, `contains`, `borders`, `homeland`, `native` |
| **Temporal** | `caused`, `caused-by`, `involved`, `involved-in`, `preceded`, `followed`, `contemporary` |
| **Catch-all** | `related`, `custom` |

### Schema

```yaml
relationships:
  - target: "[[Entity Name]]"
    type: member                # canonical type only
    period: "SA:100-SA:500"     # start-end range
    metadata:
      description: "Served as Captain of the Eastern Watch"
      rank: Captain
      nature: covert            # optional qualifier
```

All inverse pairs are automatically propagated via `ensure-inverses`. Use `metadata.description` for context (legacy `note` field still readable).

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

## Query Strategy

Match the question type to the right store. Based on benchmarking (42 tests across 14 categories):

### Which Store for Which Question

| Question Type | Use | Example |
|---------------|-----|---------|
| **"Who/what is connected to X?"** | Graph | `query --related-to "Kael'Zorai" --hops 1` |
| **"What would be affected if X changes?"** | Graph (depth 2-3) | `query --related-to "Kael'Zorai" --hops 2` |
| **"How are X and Y connected?"** | Graph (depth 3-4) | `query --related-to "Halflings" --hops 4` |
| **"Who are X's enemies/allies?"** | Graph (type filter) | `query --related-to "Varnathi"` then filter |
| **"Find something about [theme]"** | Vector | `query --semantic "betrayal loyalty broken trust"` |
| **"Suggest a scene about X"** | Vector | `query --semantic "Orkin theological schism"` |
| **"Where do [topic A] and [topic B] intersect?"** | Vector | `query --semantic "magic politics power"` |
| **"Find the passage about [specific term]"** | Vector | `query --semantic "Durâk Thul dwarven fracture"` |
| **"Find entities similar to X"** | Vector (thematic) or Graph (structural) | Either works depending on what "similar" means |
| **"List all X" / "Count X"** | SQLite | `query --type person --tags divine` |
| **"What's inside [place]?"** | SQLite | `query --within "Novaterra"` |
| **"Find entity by name"** | SQLite | `query --name "Thorgar"` |
| **"What does [exact phrase] say?"** | Grep tool | Exact phrase matching in body text |
| **"Get full prose for writing"** | Read file | After identifying entities via other stores |

### Decision Flowchart

1. **Do I know which entity?** -> Graph (connections) or SQLite (metadata) or Read file (prose)
2. **Am I looking for a theme/concept?** -> Vector semantic search
3. **Am I listing/counting/filtering?** -> SQLite
4. **Am I tracing cause-and-effect?** -> Graph depth 2-3
5. **Am I writing a scene and need context?** -> Vector, then Read the top results
6. **Do I need an exact phrase?** -> Grep tool on the project

### Anti-Patterns

- **Do NOT read all files** — 314,000+ tokens wasted.
- **Do NOT use SQLite FTS** for body-text search — use Grep or Vector instead.
- **Do NOT use Vector for structural questions** ("who is connected to X") — Graph is faster and more accurate.
- **Do NOT use Graph for thematic questions** ("find something about betrayal") — Graph has no semantic understanding.

### Relationship Notes

- Frontmatter uses `note` (singular) for relationship context. The graph stores this as `notes` on edges.
- Every relationship should have: `target`, `type`, `period`, and `note` (describing why/how the relationship exists)
- The graph automatically creates inverse edges (e.g., if A is "creator" of B, B gets "created-by" back to A)
