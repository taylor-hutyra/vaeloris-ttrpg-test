---
name: wb-query
description: Query the world using natural language. Find entities, resolve temporal states, explore relationships, and search semantically.
---

# wb-query

Query the world using natural language. Translates user questions into wb.py commands and presents results clearly.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## Query Types

Analyze the user's question (from `$ARGUMENTS` or conversation) and determine which query type to use:

### 1. Structured Query (SQLite)

For questions about entity types, names, tags, or text content.

| User asks | Command |
|-----------|---------|
| "List all factions" | `$WB query --type faction` |
| "Find people tagged noble" | `$WB query --type person --tags noble` |
| "Who is Kael?" | `$WB query --name Kael` |
| "Places in the Northern Wastes" | `$WB query --type place --within "Northern Wastes"` |
| "Anything about dragons" | `$WB query --text dragons` |

### 2. Temporal Query (Resolve)

For questions about state at a specific time.

| User asks | Command |
|-----------|---------|
| "Who ruled Valdris in SA:200?" | `$WB resolve "Valdris" --at "SA:200"` |
| "What was the Iron Covenant doing in year 500?" | `$WB resolve "Iron Covenant" --at "500"` |
| "Show the timeline of Kael" | `$WB resolve "Kael" --at "<current_era_end>"` (gets full timeline) |

Can also combine with structured query: `$WB query --type person --at "SA:200"` resolves temporal state for all results.

### 3. Graph Query (Relationships)

For questions about connections between entities.

| User asks | Command |
|-----------|---------|
| "Who is related to Kael?" | `$WB query --related-to "Kael"` |
| "Show the extended network of the Iron Covenant" | `$WB query --related-to "Iron Covenant" --hops 2` |
| "What connects A to B?" | Run `--related-to A --hops 3`, look for B in results |

### 4. Spatial Query

For questions about geographic containment and hierarchy.

| User asks | Command |
|-----------|---------|
| "What's inside the Northern Wastes?" | `$WB spatial "Northern Wastes"` |
| "Where is Valdris located?" | `$WB spatial "Valdris"` (check containment_chain) |

### 5. Semantic Query (Vector)

For fuzzy/conceptual questions where exact terms are unknown.

| User asks | Command |
|-----------|---------|
| "Who would betray their allies?" | `$WB query --semantic "betrayal treachery ambitious"` |
| "Places with dark magic" | `$WB query --semantic "dark magic corruption" --type place` |

## Steps

### 1. Parse the Question

Read `$ARGUMENTS` or the user's natural language question. Identify:
- What type of information they want (entities, relationships, state-at-time, spatial)
- Any filters (type, tags, name, time, location)
- Whether this needs one query or multiple combined queries

### 2. Execute Queries

Run the appropriate `$WB` commands via Bash. Always use `--vault <vault_root>` and `--pretty` for readability.

For complex questions, chain multiple queries:
- "Who in the Iron Covenant was alive during the Great War?" -> query faction members, then resolve each at the war's time period.

### 3. Enrich Results

For each result, consider reading the full entity file with the Read tool if the user needs detail beyond what the query returns (which is metadata only).

### 4. Format and Present

Present results in a clear, readable format:
- For entity lists: table or bullet list with name, type, key attributes
- For temporal queries: timeline format with periods and events
- For graph queries: relationship map showing connections
- For spatial queries: hierarchy tree

### 5. Suggest Follow-ups

After presenting results, suggest 2-3 follow-up queries the user might find useful. Examples:
- "You could explore [Entity]'s relationships with `/wb-query related to [Entity]`"
- "To see how this changes over time, try `/wb-query [Entity] at SA:300`"
- "For a deeper network view, try `/wb-query connections of [Entity] within 3 hops`"

## Tips

- If a query returns no results, try broader terms or semantic search as fallback.
- Combine query types for complex questions (structured to find candidates, then resolve for temporal detail).
- The `--text` flag does full-text search across all content, useful when you are not sure which field contains the answer.

## Content Integrity

- **Report only what exists.** If a query returns no results, say so clearly. Never fill gaps with plausible-sounding lore or "educated guesses" about what the world might contain.
- **Distinguish data from inference.** When presenting results, the entity data is canon. Any commentary you add (e.g., "this suggests X might be related to Y") must be clearly framed as your inference, not established fact.
- **This skill is read-only.** Do not create, update, or delete entities. If the user's question reveals a gap in the world, suggest using `/wb-create` or `/wb-suggest` — do not fill the gap yourself.
