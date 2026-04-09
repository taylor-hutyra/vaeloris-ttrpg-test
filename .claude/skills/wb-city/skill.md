---
name: wb-city
description: Create richly detailed, table-ready settlements of any scale — from a tribal camp of 15 families to a sprawling metropolis with dozens of districts — using the Render Pass methodology and Theme Park philosophy. Works in both the main world vault and Campaign folders.
---

# wb-city

Create a living, table-ready settlement using the Render Pass method, Theme Park philosophy, and social-network navigation. Scales automatically from a tribal camp (15 families) to a sprawling metropolis (hundreds of thousands of people). Can target either the main world vault or a Campaign subfolder.

## Setup

Detect the vault root (the directory containing `_meta/`). All CLI commands run from there.

```
WB="_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py"
```

On non-Windows systems, use `_meta/.wb-venv/bin/python` instead.

## Path Resolution

Cities can live in two contexts — always ask the user if unclear:

| Context | Root Path | NPC Path |
|---------|-----------|----------|
| **World canon** | `World/<Region>/<City>/` | `People/` |
| **Campaign-specific** | `Campaign/World/<Region>/<City>/` | `Campaign/People/` |

Both contexts use identical wb-type frontmatter conventions. The Campaign folder mirrors the root folder structure exactly. See `Campaign/_index.md` for folder layout.

For settlements below Town scale, use a single file instead of a folder: `World/<Region>/<City Name>.md`.

---

## Scale Tiers

Scale determines file count and detail depth. Determine tier from population or from the user's description (e.g., "small trading post", "capital city").

| Tier | Population | File Structure | NPC Files | Tension Hooks |
|------|-----------|----------------|-----------|---------------|
| **Outpost / Camp** | 1–100 | Single file | 2–4 inline | 1 |
| **Hamlet** | 101–300 | Single file with sections | 3–6 (1–2 get own files) | 2 |
| **Village** | 301–800 | City file + 2–3 district files | 5–8 (2–4 get files) | 3–4 |
| **Town** | 801–3,000 | City file + 3–6 district files | 8–15 (4–6 get files) | 4–6 |
| **City** | 3,001–20,000 | City file + 5–10 district files + hub files | 15–30 NPCs (6–12 get files) | 6–10 |
| **Metropolis** | 20,000+ | City file + 8+ district files + hub files + faction/govt files | 25+ NPCs (12+ get files) | 10+ |

For a **camp, outpost, or hamlet**, the single file covers everything. No subfolders needed.

---

## Core Design Principles

These principles are baked into every file generated at every scale.

### 1. The Render Pass Method

Never detail everything at once. Layer your prep:

- **City Map Layer** — The whole settlement. Key only the most landmark-worthy locations (the ruling seat, the temple, a unique geographic feature). Leave mundane blocks blank.
- **Borough / District Layer** — When players zoom into a specific district. Several keyed locations: faction hideouts, key services, notable intersections.
- **Hub Layer** — For dense, richly packed zones where players spend a lot of time: a market street, a tavern row, a dockside mile. Key every stall.

Generate only the layers the settlement's scale requires.

### 2. The Theme Park Philosophy

Every settlement organizes its districts into four functional zones. Players should always know where to go for what:

| Zone Type | Purpose | Tension Level |
|-----------|---------|--------------|
| **Safe Zone** | Inns, taverns, temples — rest and resupply without fear | Low |
| **Faction Hub** | Centers of political and social power: guildhalls, noble estates, council chambers | Medium |
| **Danger Zone** | Slums, sewers, criminal quarters — stealth, streetwise, or combat required | High |
| **Interest Node** | Dungeons, ruins, secret libraries within the city walls | Variable |

At small scales (Camp through Village), a single location may serve multiple roles. That's fine.

### 3. Navigate via Social Networks, Not Streets

City navigation is **social, not geographic**. Players declare intents:
> "I want to find someone who knows the black market"
> "I need a contact in the dockworkers' union"

Not: "I walk down Market Street to the corner of Third and Oak."

The **default action in a city is Investigation**. Every district has a social network: who knows what, who owes whom, what information flows where. Map this network, not the street grid.

### 4. Procedural Tables for the Mundane

Do NOT key every generic shop. Instead, generate a d10 or d20 table of names, proprietors, and quirks for mundane establishments. Roll when players spontaneously enter one. Each entry needs only: shop name, proprietor name (one line), one weird or memorable quirk.

### 5. Establishing Shots

Every district gets one paragraph of **sensory-rich description** for when players first enter — architecture, smell, ambient sounds, the kinds of people you see. Players' imaginations fill in the rest. Never read a list of streets.

### 6. Inject Immediate Tension

Pre-key at least one **"just stab someone"** event per district: a witnessed crime, a public confrontation, a desperate plea from a stranger. These anchor players who are wandering without purpose.

### 7. Shopping Abstraction

- **Mundane gear:** Subtract gold, add item. No roleplay required.
- **Significant purchases:** Full in-character scene. Reserved for expensive magical items, custom commissions, or when the merchant is a plot hook.
- **Faction discounts:** Reputation-based, no haggling rolls. Frame these as earned trust, not transactions.

### 8. Downtime Montages

For multi-day stays: each district offers 1–3 structured downtime activities. Resolve with quick skill challenges. Spotlight individual character interests without killing pace.

---

## The 7-Phase Workflow

### Phase 1: Calibrate

Ask or infer the following. Do not ask for all of these at once — work conversationally.

1. **Name and location** — what is this place called, and where in the world?
2. **Scale** — population count, or a descriptor ("small fishing village", "sprawling trade capital")
3. **Defining conflict or tension** — the single thing that makes this settlement alive and not just a backdrop. Every interesting settlement has one.
4. **Tone** — desperate, prosperous, decadent, frontier, sacred, dangerous, melancholy, vibrant
5. **Context** — world canon or campaign-specific folder?
6. **Player function** — what do players need from this settlement? (Safe harbor, information, supplies, moral dilemma, political intrigue, dungeon access)
7. **Existing entities** — check before inventing:

```bash
$WB --vault <root> --pretty query --semantic "<name> <region>"
$WB --vault <root> --pretty query --name "<name>"
$WB --vault <root> --pretty query --within "<parent region>"
```

Read `_meta/calendar.md` for era context.

### Phase 2: Establish the Concept

Generate a one-paragraph **Settlement Concept** that defines:
- The physical setting (geography, architectural character)
- The social atmosphere (who lives here, what they fear, what they want)
- The defining tension (the core conflict that makes the settlement alive)
- The hook — why players will care

Present to user. Get approval or refinement before proceeding.

### Phase 3: Design the Render Pass Structure

Based on scale tier, propose the file structure. For each planned file, define:
- Which Render Pass layer it covers
- Its Theme Park role (Safe Zone / Faction Hub / Danger Zone / Interest Node)
- One-line defining quality — the single thing that makes this district memorable
- Key NPCs (names + one-line roles)
- Primary tension hook

Present as a structured outline. User approves, modifies, or expands.

### Phase 4: Generate Content

#### City-Level File

For Town+ scale, create `<City Name>/_index.md` with:

```
# Establishing Shot
[1 vivid paragraph — senses first, facts second]

## At a Glance
[Quick-reference table: population, governance, economy, key factions, currency, danger level, notable features]

## The Shape of [City Name]
[District list: each entry = name + 1-line description + Theme Park role + link]
[Theme Park map: which districts serve which function]

## Social Networks
[Organized by intent, not by location: "To find X, talk to Y in Z"]
[Key power brokers: 3–5 names, one sentence each, what they control]

## Tension Hooks
[3–6 pre-keyed incidents — specific enough to deploy immediately]

## Shopping
[Abstraction rules specific to this settlement]
[Any unique items or services not found elsewhere]
[Mundane Shop Table: d10 or d20 — name, proprietor, quirk]

## Downtime Montage
[2–5 structured downtime options: goal, skill challenge, outcomes]

## Rumor Table
[d10 — 3 true, 4 half-true, 3 false rumors, labeled]
```

For Village and below, all of this fits in a single file without subfolders.

#### District-Level File (Borough Layer)

Required sections:

```
# Establishing Shot
[1 paragraph — sensory-rich entry description]

## Points of Interest
[Table: Location | One-sentence memorable hook | Proprietor / Controller]

## Key NPCs
[Summary paragraph per named NPC: personality, secret, what they want]
[Link to dedicated file if one exists: [[NPC Name]]]

## Social Network
[Who runs this district socially? What information flows here? Who owes whom?]

## Tension
[1–2 district-specific hooks ready to deploy immediately]

## Procedural Encounters
[d6 table: things that might happen when players linger here]
```

#### Hub-Level File (Dense Zone — City+ scale only)

For a single dense zone (a market street, a guild row, a dockside mile):

```
## What This Place Is
[1 paragraph physical description]

## The Regulars
[d6 table: types of people encountered here]

## Points of Interest (dense)
[Numbered list — every keyed location gets 2–3 sentences]

## The Big Tension
[The one conflict that shapes everything in this hub]
```

#### NPC Files

NPC files go in `People/` (world) or `Campaign/People/` (campaign). Use `wb-type: person`.

**When to give an NPC their own file:**
- Major power brokers and faction leaders
- Quest-givers the players return to repeatedly
- Any NPC with a secret that will materially affect the campaign
- Anyone the players will interact with more than twice

**When to keep an NPC inline in the district file:**
- Minor proprietors and service providers
- One-scene characters
- Background color

Augment standard `wb-type: person` frontmatter with a `campaign-notes` block:

```yaml
campaign-notes:
  role: "<one line — what function this NPC serves>"
  voice: "<speech quirk or mannerism>"
  secret: "<what they hide>"
  want: "<what they actively want>"
  fear: "<what they actively avoid>"
  quest-hooks:
    - "<hook 1>"
    - "<hook 2>"
```

### Phase 5: Generate Procedural Tables

For any settlement with commercial areas:

1. **Mundane Shop Table (d10–d20):** Names, proprietors, one memorable quirk per entry.
2. **Rumor Table (d10):** 3 true, 4 half-true, 3 false — labeled clearly for the GM.
3. **Street Encounter Table (d6):** Per district, for when players linger or wander.

### Phase 6: Execute

Write files in this order:
1. City-level file first (establishes the framework; links reference district files before they exist)
2. District files (most player-facing first)
3. NPC files (key characters first)

After all files are written:

```bash
$WB --vault <root> --pretty sync --full
$WB --vault <root> --pretty ensure-inverses --all --apply
```

### Phase 7: Report

Present:
- List of all files created with paths (clickable)
- Count: NPCs created, districts detailed, tension hooks generated, procedural tables generated
- Any lore gaps or contradictions found during creation
- Suggestion to run `/wb-consistency` if the settlement connects to significant world lore
- Reminder to check `Campaign/Maps/map-style-guide.md` for map generation prompts

---

## Content Integrity

- **Existing lore is canon.** Query before inventing. If an entity file already exists for this settlement or its parent region, read it and build on it — never contradict it.
- **Sparse over speculative.** Leave fields null rather than guessing. Mark any invented content clearly as invention.
- **Tension must be specific.** "There's political tension" is not table-ready. "The harbor master is accepting bribes from the Midnight Concordat and three dock workers know it" is table-ready.
- **NPCs need contradictions.** A character with only virtues is a prop. Every key NPC should want something that conflicts with something else they want, or hide something that would change how others see them.
- **The Mundane matters.** A settlement without the smell of bread, the sound of cart wheels, and a child in the way is a stage set. Anchor every establishing shot in sensory grounding.
- **Map notes.** At the end of every city-level file, include a `## Map Notes` section with a brief description of what a map of this place should show and a reference to `Campaign/Maps/map-style-guide.md`.
