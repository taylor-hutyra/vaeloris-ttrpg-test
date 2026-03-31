---
name: wb-modify
description: Modify an existing world-building entity with conversational refinement, creative options, recursive ripple analysis of both what is lost and gained, and changelog-driven execution.
---

# wb-modify

Modify an existing world-building entity using the 7-phase workflow. Traces both what is LOST (old state breaking) and what is GAINED (new state forming) through recursive ripple analysis.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## The 7-Phase Workflow

### Phase 1: Research & Converse

**Goal:** Understand the current state and refine the proposed change through conversation.

1. **Read the entity's current state:**
   - Read the full `.md` file (frontmatter + body prose)
   - Graph: `$WB --vault <root> --pretty query --related-to "<entity>" --hops 2` — everything connected
   - SQLite: `$WB --vault <root> --pretty query --name "<entity>"` — metadata

2. **Understand the blast radius:**
   - Vector: `$WB --vault <root> --pretty query --semantic "<entity> <proposed change context>"` — thematically related entities that might not be in the graph
   - Read the 3-5 most connected entity files for full context

3. **Converse with the user:**
   - Explain what the entity currently IS and how it connects to the world
   - Ask: "You want to change X to Y — here's what that would affect at first glance. Is that what you intend?"
   - Clarify: scope (just this entity, or cascade to connected?), timeline (retroactive change or new development?), narrative purpose
   - Iterate until the change is well-defined

### Phase 2: Generate 2-3 Options

For each option, produce:

**a) The modification delta:**
- What changes on the entity itself (frontmatter fields, relationships, body text)
- What stays the same

**b) Recursive ripple analysis — BOTH directions (severity-gated):**

Assign severity to each affected entity, then only recurse into significant changes:

```
Severity levels:
  🔴 Critical — canon breaks if not updated (e.g., old domain still referenced)
  🟡 Important — significant narrative impact (e.g., culture loses foundation)
  🟢 Minor — flavor/polish (e.g., atmospheric update, footnote change)

Recursion rule:
  🔴 Critical → RECURSE (trace downstream)
  🟡 Important → RECURSE (trace downstream)
  🟢 Minor → STOP (record but don't trace further)
```

**LOST (what breaks when the old state is removed):**
```
Depth 1: Entities directly connected to the OLD state
  → Which relationships become invalid? Assign severity. Recurse 🔴/🟡.

Depth 2: For each 🔴/🟡 break, what does IT cascade into?
  → Assign severity. Recurse 🔴/🟡.

Continue until all remaining effects are 🟢 Minor.
```

**GAINED (what forms when the new state is established):**
```
Depth 1: New connections the NEW state creates
  → Which entities gain new relationships? Assign severity. Recurse 🔴/🟡.

Depth 2: What do those new connections enable?
  → Assign severity. Recurse 🔴/🟡.

Continue until all remaining effects are 🟢 Minor.
```

**c) Impact summary:**
- Entities affected (lost vs gained)
- Severity breakdown: 🔴 Critical / 🟡 Important / 🟢 Minor
- Net narrative impact: does this make the world richer or does it break too much?

### Phase 3: User Selects Option

Present all options with their LOST and GAINED ripple chains. The user picks one.

### Phase 4: Build Changelog

For the chosen option:

1. **Deep pass** — re-read every affected entity file
2. **Document every change:**

```markdown
### The Modification
| Entity | Field | Old Value | New Value |
|--------|-------|-----------|-----------|

### 🔴 Critical Cascading Changes
| File | Action | Change | Reason |

### 🟡 Important Cascading Changes
| File | Action | Change | Reason |

### 🟢 Minor Cascading Changes
| File | Action | Change | Reason |
```

3. **Save** to `_meta/changelogs/YYYY-MM-DD-modify-<entity-name>.md`

### Phase 5: User Approves Changelog

Present for review. User can approve all, reject items, or request changes.

### Phase 6: Execute

For each approved changelog item:

1. **Edit the target entity** — apply the modification delta
2. **Edit cascading entities** — update relationships, timelines, AND body prose
3. **Post-mutation:**
   ```bash
   $WB --vault <root> --pretty ensure-inverses --all --apply
   $WB --vault <root> sync --full
   ```
4. **Update changelog** — mark each item as executed

### Phase 7: Report

- Summary of modification + cascading changes
- Link to changelog
- Suggest `/wb-consistency` for verification

## Query Strategy

1. **File read**: Read the entity being modified FIRST — full prose context is essential.
2. **Graph** (`query --related-to --hops 2-3`): Map the full connection network to understand blast radius.
3. **Vector** (`query --semantic`): Find thematically related entities not in the graph.
4. **SQLite** (`query --name`, `resolve --at`): Get metadata and temporal state.

## Guidelines

- **Never modify without understanding.** Always read the entity and its connections first.
- **Trace both LOST and GAINED.** A modification is a removal AND an addition simultaneously.
- **The changelog is mandatory.** No exceptions, even in autonomous mode.
- **Enrich body prose.** When cascading changes to affected entities, update narrative text — don't just touch frontmatter.
- **Retroactive vs progressive:** Ask the user if the change is retroactive (always was this way) or progressive (changed at a specific point in the timeline). This affects whether you update historical references or add new timeline entries.
- Use canonical relationship types ONLY (26 + custom).

## Content Integrity

- **Preserve what works.** Don't rewrite entity body text that isn't affected by the change.
- **Flag contradictions.** If the modification creates a contradiction with existing lore that the ripple analysis can't resolve, flag it to the user rather than guessing.
- **The recursive analysis must be honest.** If Option A breaks too much, say so. Don't sugarcoat impact summaries.
