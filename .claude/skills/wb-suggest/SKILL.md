---
name: wb-suggest
description: AI suggestions for your world — character concepts, faction responses, plot ideas, "who would do this?", "what would happen if?". Pure creative ideation.
---

# wb-suggest

Generate AI-powered suggestions for your world. Two primary modes: entity/character suggestions and faction/entity response analysis.

## Setup

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

Detect the vault root (the directory containing `_meta/`).

## Modes

Determine the mode from `$ARGUMENTS` or user intent:

### Mode 1: Entity/Character Suggestions

Trigger phrases: "suggest a character", "who could fill this role", "I need a villain", "suggest a faction", "what kind of creature", etc.

#### Steps

1. **Gather constraints** from the user:
   - Role or function needed ("a spy in the court", "a rival faction leader")
   - Time period ("during the First Age", "present day")
   - Location ("in the Northern Wastes")
   - Relationships ("connected to the Iron Covenant")
   - Tone ("tragic", "ambitious", "comic relief")

2. **Load world context**:
   ```bash
   $WB --vault <vault_root> query --type person --pretty    # existing characters
   $WB --vault <vault_root> query --type faction --pretty   # factions for affiliation
   $WB --vault <vault_root> query --type place --pretty     # places for origin/location
   $WB --vault <vault_root> calendar --pretty               # era info
   ```
   Read specific entity files with the Read tool if the user mentions them or if they are central to the constraints.

3. **Generate 2-3 distinct concepts**, each with:
   - **Name** and **aliases**
   - **Type** (person, faction, creature, etc.)
   - **Core concept** (1-2 sentence pitch)
   - **Backstory** sketch (3-5 sentences)
   - **Key relationships** to existing entities (with relationship types)
   - **Potential plot hooks** (2-3 story possibilities this entity enables)
   - **Why this fits** (how it fills the stated need and connects to existing world)

4. **Present all concepts** with clear differentiation. Explain the trade-offs between them.

5. **If user picks one**, offer to create it via the `/wb-create` workflow. Pass the chosen concept details so `/wb-create` can use them directly instead of regenerating.

### Mode 2: Faction/Entity Response Analysis

Trigger phrases: "how would X respond to Y", "what would X do if", "faction response", etc.

#### Steps

1. **Identify the entity and the stimulus**:
   - Entity: the faction, person, or group responding
   - Stimulus: the event, action, or change they are responding to

2. **Load deep context**:
   ```bash
   $WB --vault <vault_root> query --name "<entity>" --pretty
   $WB --vault <vault_root> query --related-to "<entity>" --hops 2 --pretty
   ```
   Read the entity's full Markdown file for goals, personality, history, and relationships. If the stimulus is an existing event, read that file too.

3. **Analyze response across dimensions**:
   - **Immediate reaction**: First public or private response (hours/days)
   - **Political**: Alliances formed or broken, diplomatic moves
   - **Military**: Troop movements, defensive postures, aggression
   - **Economic**: Trade sanctions, resource hoarding, investment shifts
   - **Social/Cultural**: Public opinion shifts, propaganda, morale effects
   - **Religious/Ideological**: How does this fit or conflict with their beliefs?
   - **Long-term strategy**: How does this change their 5-year plan?

4. **Rate confidence** for each dimension:
   - **High**: Directly follows from stated goals/personality
   - **Medium**: Reasonable inference from context
   - **Low**: Speculative but interesting

5. **Present the analysis** organized by dimension with confidence ratings.

6. **Offer follow-ups**:
   - Create an event entity for the response
   - Propagate consequences via `/wb-consequences`
   - Analyze how other factions react to THIS response (chain reaction)

## Guidelines

- Suggestions must be grounded in existing world lore. Reference specific entities, events, and locations.
- Avoid contradicting established canon. If a suggestion would conflict, flag it explicitly.
- Diversity of concepts: make the 2-3 options genuinely different in tone, background, and narrative function.
- For faction responses, consider the entity's established personality traits, not just rational strategy.
- This skill is read-only unless the user explicitly asks to create something. Do not write files.

## Content Integrity

- **Suggestions are proposals, not canon.** Always frame output as "here are options for your consideration" — never as established fact. Nothing is real until the user approves it and it's written to a file.
- **Respect the user's creative vision.** Suggestions should serve the user's stated need, not steer the world in a direction the AI finds interesting. If the user asks for "a simple merchant", don't suggest a secret dragon in disguise unless they asked for twists.
- **Confidence ratings are required.** For faction response analysis (Mode 2), always include the High/Medium/Low confidence ratings. Do not present speculative responses with the same authority as ones directly supported by entity data.
