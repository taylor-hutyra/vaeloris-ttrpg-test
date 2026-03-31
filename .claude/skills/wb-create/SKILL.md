---
name: wb-create
description: Create a new world-building entity (person, place, event, faction, etc.) with conversational refinement, creative options, recursive ripple analysis, and changelog-driven execution.
---

# wb-create

Create a new world-building entity using the 7-phase workflow: research & converse, generate options with recursive ripple analysis, build changelog, execute.

## Setup

Detect the vault root (the directory containing `_meta/`). All commands run from there.

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

## Type-to-Folder Mapping

```
person   -> People/
place    -> World/ (hierarchy)
event    -> Events/
faction  -> Factions/
item     -> Items/
religion -> Religions/
government -> Governments/
species  -> Species/
magic    -> Magic/
technology -> Technology/
```

## The 7-Phase Workflow

### Phase 1: Research & Converse

**Goal:** Understand the user's intent and refine the idea through conversation.

1. **Quick knowledge pass** to understand the landscape:
   - Vector: `$WB --vault <root> --pretty query --semantic "<user's description>"` — find thematically related entities
   - Graph: `$WB --vault <root> --pretty query --related-to "<mentioned entity>" --hops 2` — structural context around any entities the user mentioned
   - SQLite: `$WB --vault <root> --pretty query --type <type>` — see what already exists of this type
   - Read `_meta/calendar.md` for era context

2. **Ask clarifying questions** based on what you found:
   - When does this happen? (era, specific date)
   - Where? (location in the world)
   - Who is involved? (existing entities, or new ones needed?)
   - What's the narrative purpose? (fills a gap, creates tension, resolves a thread)
   - What tone? (tragic, triumphant, mysterious, political)

3. **Iterate** — the user answers, you ask follow-ups based on their answers. Continue until the change is well-defined. This is a conversation, not a form.

### Phase 2: Generate 2-3 Options

For each option, produce:

**a) The entity itself:**
- Name, type, key attributes
- Relationships it would have
- Timeline entries
- Brief narrative description

**b) Recursive ripple analysis (severity-gated):**

Trace consequences depth by depth, but only recurse into significant changes:

```
For each affected entity, assign severity:
  🔴 Critical — canon breaks if not updated (e.g., dead deity still listed as active teacher)
  🟡 Important — significant narrative impact (e.g., culture loses divine guidance)
  🟢 Minor — flavor/polish (e.g., a sibling notes the loss, a place gets an atmospheric update)

Recursion rule:
  🔴 Critical → RECURSE (trace what this change causes)
  🟡 Important → RECURSE (trace what this change causes)
  🟢 Minor → STOP (record it, but don't trace its downstream effects)
```

Applied depth by depth:
```
Depth 1 (Direct): Entities with relationships to the new entity
  → Assign severity to each. Recurse into 🔴 and 🟡 only.

Depth 2 (Cascade): For each 🔴/🟡 from Depth 1, check ITS neighbors
  → Assign severity. Recurse into 🔴 and 🟡 only.

Depth 3+: Continue until all remaining changes are 🟢 Minor
```

For changes that break existing connections (e.g., a deity dying), trace BOTH:
- **What is lost** — existing relationships that break, dependencies that fail
- **What is gained** — new narrative opportunities, power vacuums, cultural shifts

**c) Impact summary:**
- Total entities affected per depth
- Severity breakdown: 🔴 Critical / 🟡 Important / 🟢 Minor

### Phase 3: User Selects Option

Present all options side-by-side with their ripple chains. The user picks one, or asks for refinement/combination.

### Phase 4: Build Changelog

For the chosen option, build a comprehensive changelog:

1. **Deep recursive search** — re-examine the chosen option with full file reads of every affected entity
2. **Document every change** with priority:

```markdown
### 🔴 Critical (canon-breaking if omitted)
| File | Action | Change | Reason |
|------|--------|--------|--------|
| Events/New Event.md | CREATE | Full event entity | The new entity itself |
| People/Deity.md | EDIT | Add timeline + update status | Directly involved |

### 🟡 Important (significant narrative impact)
| File | Action | Change | Reason |
|------|--------|--------|--------|
| Species/Race.md | EDIT | Add timeline + body section | Loses divine teacher |

### 🟢 Minor (flavor/polish)
| File | Action | Change | Reason |
|------|--------|--------|--------|
| Species/SubRace.md | EDIT | Add cultural note | Downstream of parent change |
```

3. **Save the changelog** to `_meta/changelogs/YYYY-MM-DD-<change-name>.md`

### Phase 5: User Approves Changelog

Present the changelog. The user can:
- Approve all
- Reject specific items
- Request modifications
- Ask for more detail on specific changes

### Phase 6: Execute

For each approved item in the changelog:

1. **Create new files** — full entity files with frontmatter, relationships, timeline, and body prose
2. **Edit existing files** — add relationships, timeline entries, AND enrich body prose (not just frontmatter — update the narrative text to reflect the change)
3. **Run post-mutation steps:**
   ```bash
   $WB --vault <root> --pretty ensure-inverses --all --apply
   $WB --vault <root> sync --full
   ```
4. **Update the changelog** — mark each item as executed

### Phase 7: Report

- Summary of what was created/modified
- Count of entities affected
- Link to the changelog file
- Suggest running `/wb-consistency` for verification

## Query Strategy

1. **Vector** (`query --semantic`): Search for thematically similar entities to avoid overlap and find inspiration.
2. **Graph** (`query --related-to`): If the user specifies a connection, traverse from that entity for context.
3. **SQLite** (`query --name`, `query --type`): Check for name collisions and see existing entities of the same type.
4. **File read**: Read the template + 2-3 most relevant entity files for prose style.

## Guidelines

- Always use `[[wikilinks]]` for entity references in both frontmatter and body text.
- Period format: `"500"` (point), `"200-500"` (range), `"501-"` (ongoing), `"SA:200"` (era-qualified).
- **Event date vs period:** For events, `date` is the start date (or sole date for point events). `period` is the era-qualified period format used for temporal queries. Both should be set.
- Use canonical relationship types ONLY (26 + custom). Specifics go in `metadata` dict.
- If the entity references other entities that do not yet exist, still use wikilinks (they become forward references).

## Content Integrity

- **Ground in existing lore.** Query related entities and use them as the basis for generated content. Do not invent facts that contradict existing canon.
- **The recursive ripple analysis must be thorough.** Don't stop at depth 1. Trace the chain until it naturally terminates.
- **The changelog is mandatory.** Even in autonomous mode. World changes are high-impact operations.
- **Enrich body prose during execution.** When editing affected entities, don't just update frontmatter — add or modify body text to reflect the narrative impact.
