---
name: wb-ingest
description: Parse unstructured text (documents, notes, braindumps, existing lore) into structured world-building entities with relationships and timelines.
---

# wb-ingest

Parse unstructured text into structured world-building entities with proper frontmatter, relationships, and timelines.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## Type-to-Folder Mapping

```
person   -> People/
place    -> Places/
event    -> Events/
faction  -> Factions/
item     -> Items/
concept  -> Concepts/
creature -> Creatures/
language -> Languages/
```

## Steps

### 1. Read Source Text

Get the source text from one of:
- A file path in `$ARGUMENTS` -> read it with the Read tool
- Pasted text in the conversation
- Multiple files via a glob pattern -> read each with the Read tool

**Binary file formats (.docx, .pdf, etc.):** The Read tool cannot read `.docx` files directly. Use the Python `docx` library via Bash instead:
```bash
python -c "import docx; doc = docx.Document(r'<path>'); [print(p.text) for p in doc.paragraphs]"
```
For `.pdf` files, the Read tool supports them natively with the `pages` parameter.

### 2. Load Existing World Context

Query existing entities to avoid duplicates and to establish correct cross-references:

```bash
$WB --vault <vault_root> --pretty query --type person
$WB --vault <vault_root> --pretty query --type place
$WB --vault <vault_root> --pretty query --type faction
$WB --vault <vault_root> --pretty query --type event
```

Also read `_meta/calendar.md` for era information to correctly assign periods.

### 3. Analyze and Extract

From the source text, identify:

- **Entities**: Named people, places, factions, events, items, creatures, concepts
- **Types**: Classify each entity by its wb-type
- **Attributes**: Extract attributes specific to each type (birthplace, population, leader, etc.)
- **Relationships**: Identify connections between entities (allied-with, member-of, located-in, etc.)
- **Timeline entries**: Extract temporal events with periods where mentioned
- **Cross-references**: Map which entities reference which others

For each identified entity, note:
- Whether it already exists in the world (match against existing entities)
- Confidence level (clearly stated vs. implied vs. speculative)

### 4. Present Extraction Plan

**Always present the plan before creating files, regardless of autonomy mode.** Ingestion is a high-impact batch operation.

Show the user:
1. **New entities to create** (name, type, key attributes)
2. **Existing entities to update** (what would be added/changed)
3. **Relationships discovered** (source -> target, type)
4. **Timeline entries extracted** (entity, period, event)
5. **Ambiguities or conflicts** (entity mentioned with conflicting info, unclear type, etc.)

Ask the user to:
- Approve the plan as-is
- Remove specific entities from the plan
- Correct any misclassifications
- Resolve ambiguities

### 5. Create Entity Files

For each approved new entity, generate a full Markdown file following the same structure as `/wb-create`:

- YAML frontmatter with all type-specific fields
- `[[wikilinks]]` for all cross-references
- Relationship arrays with target, type, period
- Timeline arrays where temporal info was found
- Body text with description and relevant sections
- `created` and `modified` set to today's date

Write each file to the correct type folder using the Write tool.

### 6. Update Existing Entities

For entities that already exist and need updates:
- Read the existing file with the Read tool
- Use the Edit tool to add new relationships, timeline entries, or body content
- Do NOT overwrite existing content -- only append or fill in null fields

### 6.5. Propagate Inverse Relationships

After all entity files are written/updated, ensure inverse relationship consistency:

```bash
$WB --vault <vault_root> --pretty ensure-inverses --all
```

Review the count of missing inverses. Since the extraction plan (step 4) was already approved, inverse relationships that are direct consequences of approved relationships can be auto-applied:

```bash
$WB --vault <vault_root> --pretty ensure-inverses --all --apply
```

This runs before the full sync in step 7, so all changes are picked up in one pass.

### 7. Full Sync

After all files are written/updated:

```bash
$WB --vault <vault_root> --pretty sync --full
```

Use `--full` because multiple entities were created/modified and cross-references need rebuilding.

### 8. Report

Present a summary:
- Number of entities created (by type)
- Number of entities updated
- Total relationships established
- Any warnings (entities referenced but not created, ambiguous timeline entries)
- Suggest running `/wb-consistency` to verify the ingested data

## Query Strategy

1. **SQLite** (`query --name`): Check for duplicate names/aliases before creating.
2. **Vector** (`query --semantic`): Search for semantically similar entities to catch near-duplicates the name check would miss.
3. **File read**: Read existing entities that will be updated to avoid overwriting content.

## Guidelines

- Prefer creating entities with sparse but accurate data over filling fields with speculation.
- If the source text is ambiguous about a detail, leave the field as `null` rather than guessing.
- Always use `[[wikilinks]]` for cross-references.
- Deduplicate: if the source mentions "King Aldric" and "Aldric the Bold", check if they are the same entity and use `aliases` to track alternate names.
- Period format: `"500"` (point), `"200-500"` (range), `"501-"` (ongoing), `"SA:200"` (era-qualified).

## Content Integrity

- **Extract, don't embellish.** Only include information that is stated or clearly implied in the source text. Do not generate backstory, motivations, or relationships that the source doesn't support. The body text should summarize what the source says, not what the AI imagines.
- **The extraction plan (step 4) is mandatory.** Even in autonomous mode. Ingestion is a batch operation that creates multiple entities — always show the user what will be created and let them correct misclassifications before any files are written.
- **Flag confidence levels.** In the extraction plan, mark each entity/relationship as "explicit" (directly stated in source) or "inferred" (implied by context). Let the user decide whether to keep inferences.
