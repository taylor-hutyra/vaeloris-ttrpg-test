---
name: wb-create
description: Create a new world-building entity (person, place, event, faction, etc.) with AI-generated backstory, relationships, and timeline entries.
---

# wb-create

Create a new world-building entity with enriched frontmatter, relationships, and narrative description.

## Setup

Detect the vault root (the directory containing `_meta/`). All commands run from there.

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

## Type-to-Folder Mapping

```
TYPE_FOLDERS:
  person   -> People/
  place    -> Places/
  event    -> Events/
  faction  -> Factions/
  item     -> Items/
  concept  -> Concepts/
  creature -> Creatures/
  language -> Languages/
  narrative -> Stories/
  lore     -> Lore/
```

If the folder does not exist, create it.

## Steps

### 1. Parse Input

Extract entity type and name from `$ARGUMENTS` or ask the user. Examples:
- `$ARGUMENTS = "person Kael Draemor"` -> type=person, name=Kael Draemor
- `$ARGUMENTS = "faction The Iron Covenant"` -> type=faction, name=The Iron Covenant
- `$ARGUMENTS = ""` -> ask the user for type and name

### 2. Load World Context

Run these commands to gather context for AI generation:

```bash
$WB --vault <vault_root> calendar                          # era info
$WB --vault <vault_root> query --type <related_types>      # existing entities
```

For a person, query factions and places. For a place, query parent places. For an event, query people and factions. Use `--pretty` for readability.

Also read `_meta/calendar.md` with the Read tool for era details.

### 3. Read the Template

Read the template from `_templates/<type>.md` if it exists. Use it as a structural guide for frontmatter fields. If no template exists, use the base fields: `wb-type`, `wb-id`, `name`, `aliases`, `relationships`, `timeline`, `tags`, `created`, `modified`.

### 4. Check Autonomy Mode

Read `_meta/wb-config.md` and check the `mode` field:
- **ask**: Generate the entity, show it to the user, and wait for approval before writing.
- **autonomous**: Generate and write directly.

### 5. Generate the Entity

Create the full Markdown file with:

**Frontmatter (YAML):**
- `wb-type`: the entity type
- `wb-id`: lowercase name with spaces replaced by hyphens
- `name`: the entity name
- All type-specific fields from the template
- `relationships`: array of `{target: "[[Entity Name]]", type: "relationship-type", period: "time-range"}`. Use `[[wikilinks]]` for all entity references.
- `timeline`: array of `{period: "time", event: "description"}` entries
- `tags`: array including the type and any relevant tags
- `created` and `modified`: today's date in ISO format

**Body (Markdown):**
- H1 heading with entity name
- Description paragraph with generated backstory
- Relevant sections based on type (Background, Personality, Geography, etc.)
- Use `[[wikilinks]]` for ALL cross-references to other entities

### 6. Write the File

Write to `<TYPE_FOLDER>/<Entity Name>.md` using the Write tool.

Filename: use the entity name exactly as provided (preserving spaces and capitalization), with `.md` extension.

### 7. Sync

```bash
$WB --vault <vault_root> sync "<TYPE_FOLDER>/<Entity Name>.md"
```

### 8. Report

Show the user the created entity path and a summary of what was generated (name, type, key relationships, timeline entries).

## Guidelines

- Always use `[[wikilinks]]` for entity references in both frontmatter and body text.
- Period format: `"500"` (point), `"200-500"` (range), `"501-"` (ongoing), `"SA:200"` (era-qualified).
- Relationship types: allied-with, enemy-of, member-of, leader-of, parent-of, child-of, located-in, ruler-of, founded-by, created-by, mentor-of, student-of, rival-of, trade-partner.
- If the entity references other entities that do not yet exist, still use wikilinks (they become forward references).

## Content Integrity

- **Ground in existing lore.** Query related entities in step 2 and use them as the basis for generated content. Do not invent facts that contradict or ignore what already exists.
- **Only generate what the user asked for.** If the user says "create a blacksmith named Torin", create that — do not embellish with an elaborate secret identity or world-altering prophecy unless the user asks for it.
- **Label AI-generated content.** When generating backstory, relationships, or timeline entries that go beyond what the user specified, briefly note what you invented vs. what was provided or derived from existing entities.
- **Prefer minimal viable entity.** Fill required fields and what the user specified. Leave optional fields empty rather than guessing. The user can always enrich later.
