---
name: wb-consequences
description: Analyze ripple effects of world changes and propagate modifications across affected entities. Traces political, social, economic, military, and religious impacts.
---

# wb-consequences

Analyze the cascading effects of a world change and apply approved modifications to affected entities.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## Steps

### 1. Understand the Change

Parse `$ARGUMENTS` or the user's description to identify:
- **What changed**: Which entity was modified, created, or destroyed?
- **Nature of change**: Death, alliance shift, territorial conquest, discovery, betrayal, etc.
- **When**: The period/date of the change

Examples:
- "King Aldric was assassinated in SA:450"
- "The Iron Covenant conquered Valdris"
- "A new magic source was discovered in the Northern Wastes"

### 2. Run Deterministic Propagation

```bash
$WB --vault <vault_root> propagate "<entity_name>" --pretty
```

This returns rule-based suggestions from the propagation engine (e.g., relationship inverse updates, spatial hierarchy effects). Collect these as the baseline change set.

### 3. Load Context for Deeper Analysis

```bash
$WB --vault <vault_root> query --related-to "<entity_name>" --hops 2 --pretty
$WB --vault <vault_root> query --type faction --pretty
$WB --vault <vault_root> query --type event --pretty
```

Read the full Markdown files of the changed entity and its closest connections using the Read tool. Focus on:
- Relationships and their types
- Goals and motivations (for factions/people)
- Spatial hierarchy (for places)
- Timeline entries (for temporal context)

### 4. Analyze Ripple Effects

Trace effects across seven dimensions, organized by order:

**First-order effects** (direct, immediate):
- Entities with direct relationships to the changed entity
- Spatial children/parents of a changed place
- Members of a dissolved/changed faction

**Second-order effects** (indirect, near-term):
- Allies of affected entities react
- Economic networks disrupted
- Power vacuums created

**Third-order effects** (speculative, long-term):
- Cultural shifts
- New alliances forming
- Historical narratives changing

For each effect, specify:
- **Target entity**: Which entity is affected (use `[[wikilinks]]`)
- **Change type**: What field(s) to modify
- **Severity**: Critical (world breaks without this) / Important (strongly implied) / Optional (interesting but speculative)
- **Dimension**: Political / Social / Economic / Military / Religious / Geographic / Temporal
- **Proposed modification**: The specific edit to make

### 5. Present Proposed Changes

Organize changes by severity:

**Critical** (structural consistency):
- Broken relationship references
- Timeline contradictions
- Spatial hierarchy issues

**Important** (narrative consistency):
- Faction response updates
- Leadership changes
- Alliance shifts

**Optional** (enrichment):
- Mood/atmosphere changes for places
- Secondary character reactions
- Economic ripple effects

### 6. Check Autonomy Mode

Read `_meta/wb-config.md` and check the `mode` field:

- **ask mode**: Present all proposed changes grouped by severity. Wait for user to approve individually or in bulk ("apply all critical", "apply all", "skip optional", etc.).
- **autonomous mode**: Apply Critical changes automatically. Apply Important changes automatically. **Do not auto-apply Optional changes** — these are speculative and require user approval even in autonomous mode. Log everything to `_meta/changelog.md` with timestamp, change description, severity, and affected entities.

### 7. Apply Approved Changes

For each approved change:

1. Read the target entity file with the Read tool
2. Apply the modification using the Edit tool:
   - For frontmatter changes: edit the YAML block
   - For relationship additions: add to the `relationships` array
   - For timeline additions: add to the `timeline` array
   - For body text changes: edit the relevant section
3. Sync the modified file:
   ```bash
   $WB --vault <vault_root> sync "<entity_path>"
   ```

### 8. Report

Present a summary:
- Number of entities modified
- Changes applied by severity and dimension
- Any new entities that should be created (suggest using `/wb-create`)
- Suggest running `/wb-consistency` to verify no contradictions were introduced

## Changelog Format

When logging to `_meta/changelog.md` (autonomous mode), append:

```markdown
## <date> - Consequences of <change description>

- **<Entity>**: <what changed> (severity)
- **<Entity>**: <what changed> (severity)

Triggered by: <original change description>
```

## Guidelines

- Never delete existing timeline entries — only add new ones.
- When modifying relationships, preserve existing ones unless explicitly contradicted.
- Use `[[wikilinks]]` for all entity references in modifications.
- Period format for new timeline entries: use the same era system as existing entries.
- If a change would create a logical contradiction with existing lore, flag it rather than applying it silently.

## Content Integrity

- **Label confidence on every proposed change.** First-order effects (direct relationships) are high confidence. Second-order (ally reactions, economic shifts) are medium. Third-order (cultural shifts, new alliances) are speculative — label them clearly.
- **Do not invent entities.** Proposed changes should reference existing entities only. If a consequence implies a new entity should exist (e.g., "a successor would need to be named"), suggest creating it via `/wb-create` rather than inserting fabricated details.
- **Preserve authorial intent.** The user's world is their creation. Consequence analysis should show what logically follows, not rewrite the user's narrative direction. If multiple plausible outcomes exist, present them as options rather than picking one.
