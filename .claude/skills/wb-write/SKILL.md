---
name: wb-write
description: Generate narrative content — chapters, era histories, in-world lore documents, or character vignettes. Supports delegation to external models (Gemini, etc.).
---

# wb-write

Generate narrative prose grounded in world data. Supports four content types and multi-model delegation.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## Content Types

Determine the content type from `$ARGUMENTS` or user intent:

| Type | Trigger phrases | Output folder |
|------|----------------|---------------|
| **chapter** | "write a chapter", "story chapter", "scene" | Stories/ |
| **era** | "write era history", "history of the First Age" | Lore/ |
| **lore** | "write a letter", "treaty", "myth", "scholarly text" | Lore/ |
| **vignette** | "write a vignette", "character scene", "short scene" | Stories/ |

## Steps

### 1. Determine Content Type and Parameters

**Chapter:**
- Story name (which story does this belong to?)
- Chapter number/title
- POV character
- Setting (location)
- Key events to cover
- Characters involved
- Tone/style notes

**Era:**
- Era name (from `_meta/calendar.md`)
- Focus: overview, or specific aspect (political, cultural, military)
- Key events to cover
- Key figures to mention

**Lore:**
- Document type: letter, treaty, myth, legend, scholarly text, journal, proclamation, prophecy
- In-world author (who "wrote" this document?)
- Time period (when was it written?)
- Subject matter
- Intended audience (within the world)

**Vignette:**
- POV character
- Setting (location + time)
- Emotional focus or theme
- Other characters present
- Scene prompt or situation

### 2. Load World Context

```bash
$WB --vault <vault_root> calendar --pretty
```

Then load context specific to the content:

For **chapter/vignette**: Read POV character file, setting file, and files for all involved characters. Query relationships:
```bash
$WB --vault <vault_root> query --related-to "<pov_character>" --pretty
$WB --vault <vault_root> resolve "<pov_character>" --at "<period>" --pretty
```

For **era**: Query all events in the era's period range, plus key factions and people:
```bash
$WB --vault <vault_root> query --type event --at "<era_start>-<era_end>" --pretty
$WB --vault <vault_root> query --type faction --pretty
```

For **lore**: Read the in-world author's file (if they exist as an entity), the subject entities, and any relevant events.

### 3. Check Model Routing

Read `_meta/wb-config.md` and check `model-routing` for the content type:
- `write-chapter` -> typically routed to `creative` model
- `write-era` -> typically routed to `creative` model
- `write-lore` -> typically routed to `creative` model
- `write-vignette` -> typically routed to `creative` model

Look up the routed model in the `models.available` section to get the CLI command and prompt method.

### 4. Generate Content

**If routed to Claude (or model is "default"/"claude"):**
Write the content directly in this conversation. No external tool needed.

**If routed to an external model (e.g., gemini, ollama):**

Build a prompt that includes:
1. World context summary (key entities, relationships, timeline)
2. Specific instructions for the content type
3. Style/tone guidance
4. Character voice notes (for lore documents with an in-world author)
5. Constraints ("must reference these events", "POV character doesn't know about X")

Send via the configured CLI:
```bash
echo '<full_prompt>' | <cli_command>
```

For example, if `gemini` is configured with `prompt-via: stdin`:
```bash
echo '<full_prompt>' | gemini
```

Read the response from stdout.

### 5. Add Frontmatter

Wrap the generated content in a proper entity file:

```yaml
---
wb-type: narrative
narrative-type: chapter|era|lore|vignette
story: "Story Name"          # for chapters
chapter: 1                    # for chapters
period: "SA:200-SA:210"       # when the content takes place
pov: "[[Character Name]]"    # for chapters/vignettes
locations:
  - "[[Place Name]]"
characters:
  - "[[Character Name]]"
events:
  - "[[Event Name]]"
lore-type: letter|treaty|myth|scholarly|journal|proclamation|prophecy  # for lore
in-world-author: "[[Author]]"  # for lore
generated-by: claude|gemini|ollama
reviewed: false
tags:
  - narrative
  - <narrative-type>
created: "<today>"
modified: "<today>"
---
```

### 6. Write the File

Determine filename:
- **Chapter**: `Stories/<Story Name>/Chapter <N> - <Title>.md`
- **Era**: `Lore/Era - <Era Name>.md`
- **Lore**: `Lore/<Document Title>.md`
- **Vignette**: `Stories/Vignettes/<Title>.md`

Create subdirectories if they do not exist. Write with the Write tool.

### 7. Sync

```bash
$WB --vault <vault_root> sync "<file_path>"
```

### 8. Present

Show the user:
- Where the file was saved
- A brief summary (word count, characters involved, period covered)
- Note that `reviewed: false` is set -- remind them to mark it `true` after review
- If an external model was used, note which model generated it

## Guidelines

- All entity references in the narrative body should use `[[wikilinks]]`.
- For in-world lore documents, write in the voice and knowledge level of the in-world author. They should not know things their character would not know.
- For chapters and vignettes, respect POV constraints. The narration should only reveal what the POV character perceives and knows.
- If the external model produces content that contradicts world lore, note the discrepancies and offer to edit them before saving.

## Content Integrity

- **Canon compliance is mandatory.** Before writing, read entity files for all characters, places, and events that will appear. Do not contradict their established attributes, relationships, timelines, or personality. If you need to deviate for narrative purposes, flag it explicitly.
- **Do not invent major lore.** Narrative content should work within the existing world. Do not introduce new factions, magic systems, historical events, or world-altering facts that aren't already established — unless the user explicitly asks for it. Minor atmospheric details (a tavern name, a weather description, an unnamed NPC) are fine.
- **Present before saving.** Always show the generated content to the user before writing it to a file, regardless of autonomy mode. Narrative is high-stakes content that directly becomes canon once written.
- **Track provenance.** The `generated-by` frontmatter field records which model produced the content. The `reviewed: false` field signals it has not been user-verified. Remind the user to review and set `reviewed: true`.
- **Character consistency.** When writing dialogue or actions for existing characters, re-read their entity file. Respect their established personality, speech patterns, goals, and knowledge. Do not have characters act out of character without narrative justification.
