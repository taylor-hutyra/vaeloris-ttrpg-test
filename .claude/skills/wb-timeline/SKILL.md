---
name: wb-timeline
description: Compile chronological timeline summaries for an entity, location, faction, or the entire world. Shows cause-and-effect chains and flags gaps.
---

# wb-timeline

Compile and present chronological timelines with cause-and-effect analysis and gap detection.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## Steps

### 1. Determine Scope

Parse `$ARGUMENTS` or user request to determine the timeline scope:

| Scope | Example requests |
|-------|-----------------|
| **Entity** | "timeline of Kael", "what happened to Kael" |
| **Location** | "history of Valdris", "timeline of the Northern Wastes" |
| **Faction** | "Iron Covenant timeline", "history of the Guild" |
| **Era** | "what happened during the First Age", "timeline of SA:200-SA:400" |
| **World** | "full world timeline", "everything in chronological order" |

### 2. Gather Timeline Data

**For entity/faction scope:**
```bash
$WB --vault <vault_root> query --name "<entity>" --pretty
$WB --vault <vault_root> query --related-to "<entity>" --hops 1 --pretty
$WB --vault <vault_root> query --type event --pretty
```
Read the entity's full Markdown file to get its `timeline` array and `relationships`. Also read files for directly related entities to find their timeline entries that reference this entity.

**For location scope:**
```bash
$WB --vault <vault_root> spatial "<place>" --pretty
$WB --vault <vault_root> query --within "<place>" --pretty
$WB --vault <vault_root> query --type event --pretty
```
Read the place file and all contained entities. Gather events whose `location` matches.

**For era scope:**
```bash
$WB --vault <vault_root> calendar --pretty
$WB --vault <vault_root> query --type event --pretty
$WB --vault <vault_root> query --type person --pretty
$WB --vault <vault_root> query --type faction --pretty
```
Read `_meta/calendar.md` for era boundaries. Filter all entities and events to those active within the era's period range.

**For world scope:**
```bash
$WB --vault <vault_root> query --type event --pretty
$WB --vault <vault_root> calendar --pretty
```
Read all event files. Also scan person, faction, and place files for their `timeline` arrays.

### 3. Collect and Normalize Entries

For each source, extract timeline entries in a uniform format:
```
{
  period: "SA:200",          # normalized to absolute or era-qualified
  event: "description",
  entity: "[[Entity Name]]", # which entity this entry belongs to
  source: "entity-timeline" | "event-entity" | "relationship",
  related: ["[[Entity A]]", "[[Entity B]]"]  # other entities involved
}
```

Sources of timeline data:
- `timeline` arrays in entity frontmatter
- Event entities (their `date` field + description)
- Relationship `period` fields (when relationships began/ended)
- `born` / `died` / `founded` / `dissolved` fields

### 4. Sort Chronologically

Sort all entries by period. Use the calendar's era definitions to resolve era-qualified periods into a sortable order.

For range periods (e.g., "200-500"), use the start of the range for sorting.

Group entries by era if the world has defined eras.

### 5. Analyze Cause and Effect

For consecutive or overlapping events, identify causal connections:
- Does event B list event A in its `causes` field?
- Did event A's `consequences` predict event B?
- Are the same entities involved in consecutive events?
- Does a relationship change follow an event involving both parties?

Draw connections as arrows: `Event A -> caused -> Event B`

Mark connections by confidence:
- **Explicit**: stated in `causes`/`consequences` fields
- **Implied**: same entities, close timing, logical connection
- **Speculative**: possible but not confirmed

### 6. Flag Gaps and Issues

Identify:
- **Temporal gaps**: Long periods (relative to the world's pacing) with no recorded events for an entity/location
- **Missing events**: Relationships that appear without an event explaining how they formed
- **Dead periods**: Eras or centuries with no events at all
- **Sequence issues**: Events that seem out of logical order (e.g., consequence before cause)
- **Lifespan gaps**: People with large stretches of unrecorded activity between their birth and significant events

### 7. Present the Timeline

Format the timeline in a clear, readable structure:

```
## Era Name (Start - End)

### Period: SA:200
- **Event Name** — Description
  - Involved: [[Person A]], [[Faction B]]
  - Consequence: -> [[Event C]] (SA:210)

### Period: SA:210
- **Event C** — Description
  - Caused by: <- [[Event Name]] (SA:200)
  - Involved: [[Person A]], [[Person D]]

---
[GAP: SA:210 - SA:350 — no recorded events for [[Person A]]]
---

### Period: SA:350
...
```

For entity-scoped timelines, show the entity's state changes alongside world events they participated in.

### 8. Summary and Suggestions

After the timeline, provide:
- **Statistics**: total events, time span covered, number of gaps
- **Key turning points**: the 3-5 most consequential events
- **Suggested additions**: events that would fill important gaps or explain unexplained transitions
- Offer to create missing events via `/wb-create` or write era narratives via `/wb-write era`

## Guidelines

- Always use `[[wikilinks]]` for entity references in the output.
- Period format: `"500"` (point), `"200-500"` (range), `"501-"` (ongoing), `"SA:200"` (era-qualified).
- This skill is read-only. It does not modify any files.
- For very large worlds, offer to filter by era or entity type to keep the output manageable.
- If the calendar has named eras, use era names as section headers for readability.

## Content Integrity

- **Timeline entries are data. Analysis is inference.** The chronological listing (step 7) should contain only events that exist in entity files. Cause-and-effect connections (step 5) are your analysis — label explicit connections (from `causes`/`consequences` fields) separately from implied or speculative ones.
- **Gap suggestions are suggestions, not canon.** When flagging gaps (step 6) and suggesting additions (step 8), clearly label these as "suggested" or "possible". Do not present them as established events. Frame as: "There is a gap here — you might consider adding..." not "During this period, X happened."
- **Do not fabricate events to fill gaps.** A gap in the timeline is valid information. The user may want it there, or may want to fill it themselves. Report the gap, suggest what *type* of event might fill it, but do not generate specific events.
