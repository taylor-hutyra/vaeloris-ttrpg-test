---
name: wb-consistency
description: Audit the world for contradictions, timeline gaps, broken links, missing data, one-sided relationships, and logical inconsistencies.
---

# wb-consistency

Comprehensive audit of the world for structural, relational, temporal, and logical consistency.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## Steps

### 1. Structural Validation

Run the built-in validator:

```bash
$WB --vault <vault_root> --pretty validate
```

This checks each entity for:
- Required frontmatter fields present
- Valid wb-type values
- Properly formatted relationships and timeline arrays
- Valid period formats

Collect all reported issues.

### 2. Cross-Store Consistency

Verify all three data stores (SQLite, NetworkX graph, ChromaDB vectors) agree:

```bash
$WB --vault <vault_root> --pretty sync --verify
```

If inconsistencies are found, note which entities are missing from which stores.

### 3. Broken Wikilinks

Use the Grep tool to find all wikilinks across entity files:

```
Pattern: \[\[([^\]]+)\]\]
Path: <vault_root>
Glob: **/*.md (excluding _meta/ and _templates/)
```

For each unique wikilink target found, check if a corresponding `.md` file exists using Glob:
```
Pattern: **/<Target Name>.md
```

Report any wikilinks that do not resolve to an existing file. Categorize as:
- **Likely forward references**: intentional placeholders for entities not yet created
- **Likely typos**: close matches exist (suggest corrections)
- **Unknown**: no close matches

### 4. Relationship Bidirectionality

For each entity with relationships, verify the inverse exists:

1. Query all entities: `$WB --vault <vault_root> --pretty query`
2. For each entity, read its file and extract `relationships` from frontmatter
3. For each relationship `{target: "[[B]]", type: "allied-with"}` on entity A:
   - Find entity B's file
   - Check if B has a relationship pointing back to A
   - If the relationship type has a known inverse (e.g., leader-of / member-of, parent-of / child-of), check for the inverse type specifically

Known inverse pairs:
```
allied-with    <-> allied-with
enemy-of       <-> enemy-of
rival-of       <-> rival-of
leader-of      <-> member-of
parent-of      <-> child-of
mentor-of      <-> student-of
ruler-of       <-> subject-of
founded-by     <-> founder-of
trade-partner  <-> trade-partner
```

Report one-sided relationships.

To fix all one-sided relationships in bulk, use:

```bash
$WB --vault <vault_root> --pretty ensure-inverses --all
```

Review the output, then apply:

```bash
$WB --vault <vault_root> --pretty ensure-inverses --all --apply
```

### 5. Timeline Consistency

For each person entity:
- If `born` and `died` are set, verify no timeline entries fall outside that range
- Verify the entity is not a `participant` in events dated outside their lifespan
- Check that timeline entries are not contradictory (e.g., "became king in 500" and "was exiled in 490" followed by "ruled from 480-520")

For each event entity:
- If `participants` are listed, verify those people were alive at the event's `date`
- If `location` is set, verify the place existed at that time

Read `_meta/calendar.md` for era definitions to correctly interpret era-qualified periods.

### 6. Spatial Consistency

For entities referencing places:
- `residence`, `birthplace`, `location`, `headquarters`, `territory` fields should point to existing place entities
- `parent` fields in places should form a valid tree (no cycles, no orphaned references)

```bash
$WB --vault <vault_root> --pretty spatial "<place_name>"
```

Run for a sample of places to check hierarchy validity.

### 7. Logical Consistency (AI-Powered)

Read a sample of entity files and check for narrative contradictions:
- A character described as "reclusive hermit" but with 20 active relationships
- A "destroyed" city that is listed as someone's current residence
- A faction with goals that directly contradict its stated actions
- Timeline entries that imply impossible travel or simultaneous presence

This step requires reading entity content and reasoning about it. Focus on entities that have the most relationships and timeline entries, as they are most likely to contain contradictions.

### 8. Present Findings

Organize all issues by severity:

**Critical** (data integrity):
- Broken store consistency (step 2)
- Invalid frontmatter (step 1)
- Broken wikilinks that are likely typos

**Important** (narrative integrity):
- One-sided relationships
- Timeline violations (dead people at events, etc.)
- Spatial reference errors

**Minor** (polish):
- Forward-reference wikilinks (not errors, just noting them)
- Missing optional fields
- Logical oddities from AI analysis

For each issue, show:
- The entity/file affected
- What the issue is
- A suggested fix

### 9. Offer Fixes

Check `_meta/wb-config.md` for autonomy mode:

- **ask mode**: For each issue, ask whether to fix it. Apply approved fixes using the Edit tool, then sync.
- **autonomous mode**: Auto-fix Critical and Important issues. Log all fixes to `_meta/changelog.md`.

After applying fixes:
```bash
$WB --vault <vault_root> --pretty sync --full
```

## Query Strategy

This skill requires all stores for cross-validation:

1. **SQLite** (`validate`, `sync --verify`): Structural validation and cross-store consistency checks — run these first as the baseline.
2. **SQLite** (`query --type`, `query`): Get full entity listings for relationship bidirectionality checks and timeline range validation.
3. **Graph** (`spatial`): Verify spatial hierarchy integrity — no cycles, valid parent chains.
4. **Grep tool**: Find all `[[wikilinks]]` across files to check for broken links. This is a file-level operation, not a store query.
5. **File read**: Read individual entity files for logical consistency checks (step 7). Focus on the 10-15 most connected entities, identified via graph degree.
6. **Anti-pattern**: Do not read all files upfront. Use SQLite/graph to identify problematic entities, then read only those for detailed inspection.

## Guidelines

- Do NOT modify entity files during the audit phase (steps 1-7). Only modify during the fix phase (step 9) if approved.
- For large worlds (50+ entities), focus the AI-powered logical consistency check (step 7) on the 10-15 most connected entities rather than reading everything.
- Report issue counts at the top of the output so the user gets the headline immediately.

## Content Integrity

- **Fixes must be minimal and precise.** When fixing issues, make the smallest change that resolves the problem. Do not "improve" or "enrich" entity content while fixing a broken wikilink or missing relationship inverse.
- **Do not resolve ambiguity yourself.** If an issue has multiple valid fixes (e.g., entity A says allied, entity B says enemy), present both options to the user rather than picking one. The user knows their intended canon.
- **Logical consistency findings are observations, not verdicts.** Step 7 (AI-powered checks) produces inferences, not hard errors. Present them as "potential issue" or "worth reviewing" — the user may have intentional reasons for apparent contradictions.
