---
name: Vaeloris Map Style Guide
description: Visual style and AI generation instructions for all Vaeloris maps, standardized on the Mike Schley aesthetic. City-agnostic — covers all biomes, settlement types, material levels, and industries.
tags: [meta, maps, art-guide]
created: 2026-04-08
modified: 2026-04-08
---
# Vaeloris Map Style Guide

All maps use the **Mike Schley** aesthetic — the defining visual language of professional hand-drawn TTRPG cartography. Consistent use across all campaign and world maps ensures every location feels like it belongs to the same world.

This guide is **settlement-agnostic**. It defines the visual language. Each specific settlement gets its own map definition file (see `Campaign/Maps/` for per-city prompts).

---

## The Mike Schley Aesthetic

### Core Visual Qualities

- **Hand-drawn linework** — not vector-clean. Lines have natural weight variation, slight wobbles, and hand-inked character. Contour lines show elevation change.
- **Parchment or aged-paper background** — warm cream to amber tones, subtle staining, slight edge-darkening as if the map has been handled.
- **Painterly fills** — regions and terrain filled with soft watercolor-style washes, never flat fills. Multiple translucent layers of color build depth.
- **Topographic hatching** — hills and mountain ridges shown with consistent line hatching (parallel or fan-radial lines running down the slope), not shaded blocks.
- **Layered depth** — foreground elements (trees, buildings) sit in front of terrain; distance indicated by lightening line weight.
- **Serif fonts** — clean, traditional serif for all labels. Settlement names slightly larger than district names; region names in ALL CAPS SPACED. Italic for bodies of water.
- **Ornamental compass rose** — detailed, with cardinal and inter-cardinal points. Often with an outer decorative ring.
- **Scale bar and legend** — always present on city maps and larger. Scale bar shows two or three segment lengths. Legend uses the same icons as the map.
- **Numbered/lettered key** — points of interest numbered in the map, described in a separate key block on the map or alongside it.

---

## Base Color Palette

These are the universal Vaeloris palette defaults. Specific biome and settlement sections below describe how to shift from this base.

| Element | Color |
|---------|-------|
| Parchment background | Warm tan — `#D4B483` to `#E8CFA0` |
| Water bodies | Desaturated steel blue — `#7CA5B8` |
| Forest / vegetation | Muted sage green — `#7A9E7E` to `#5C7A60` |
| Desert / arid terrain | Sandy ochre — `#C8A96A` to `#B89050` |
| Mountains / rock | Warm grey-brown — `#8C7B6B` |
| Settlement (buildings) | Light buff — `#D4C4A0` |
| Roads | Warm tan, slightly darker than parchment — `#A0895C` |
| Text and linework | Deep sepia — `#3D2B1F` |
| Accent / highlight | Amber-gold — `#C8922A` |
| Cave / underground | Deep umber shadow — `#5C3D28` |
| Magical / arcane | Faint iridescent blue-violet wash (used sparingly) |
| Snow / ice | Pale blue-white — `#D6E4EC` |
| Swamp / marsh | Olive-brown — `#7A7A50` with blue-grey water patches |
| Volcanic / scorched | Charcoal — `#3A3028` with orange-red ember accents `#C44518` |
| Grassland / plains | Warm yellow-green — `#A3B86C` |

---

## Icon Conventions

| Feature | Symbol |
|---------|--------|
| Inn / Tavern | Hanging sign or tankard motif on building |
| Temple / Shrine | Building with circular or arched window, often cross or star element |
| Market / Trade | Scales or open-awning stall silhouette |
| Military / Guard post | Tower with crenellations |
| Mage / Arcane | Flame or crystal shard motif |
| Well / Water source | Circle with bucket and crossbar |
| Cave entrance | Arch shape with radiating hatching inward |
| Ruin | Crumbled wall outline with grass pushing through |
| Forest | Stylized deciduous tree cluster (3–5 trees, varied heights) |
| Conifer forest | Narrow triangular tree cluster |
| Jungle / tropical | Dense canopy clusters, broad fronds, vines |
| Desert | Dune wave lines with occasional cactus or scrub |
| Cliff face | Cliff edge line with short hatching perpendicular to the drop |
| Docks / wharf | Rectangular planking extending into water |
| Bridge | Double parallel lines with cross-hatching |
| Wall / fortification | Thick double line with periodic tower bumps |
| Gate / entrance | Gap in wall with flanking towers |
| Mine entrance | Pick-and-hammer motif or downward-arrow arch |
| Farm / field | Parallel furrow lines in a bounded area |
| Graveyard / burial | Cluster of small cross or headstone shapes |
| Lighthouse / beacon | Tall narrow tower with radiating lines at top |
| Shipwreck | Broken hull outline, tilted |
| Geothermal vent | Wavy rising-steam lines from a crack or pool |

---

## Map Tiers

### City Map (Settlement Overview)
- **Coverage:** Full settlement + immediate surroundings (0.5–2 mile radius)
- **Scale:** 1 inch ≈ 200–500 feet
- **Keys only:** Major landmarks only (3–8 numbered/lettered points)
- **Detail level:** Silhouette building blocks, no floor plans; terrain features prominent
- **Text:** Settlement name large (top), district names medium, landmark labels small

### Borough / District Map
- **Coverage:** One district or neighborhood
- **Scale:** 1 inch ≈ 50–100 feet
- **Keys:** Individual buildings, intersections, notable spots (10–25 locations)
- **Detail level:** Building footprints, some showing doorways/windows
- **Text:** District name large, building/location labels small

### Hub Map (Dense Zone)
- **Coverage:** A single street, courtyard, or dense cluster of buildings
- **Scale:** 1 inch ≈ 10–25 feet
- **Keys:** Every location numbered (20–40 locations); legend alongside
- **Detail level:** Individual rooms may appear; entrance positions shown
- **Text:** All locations numbered; legend in margin

### Region / Overland Map
- **Coverage:** A region, trade route, or multi-settlement area
- **Scale:** 1 inch ≈ 1–10 miles
- **Keys:** Settlements as named icons, terrain zones, roads, borders
- **Detail level:** Broad terrain washes, no individual buildings
- **Text:** Region name in ALL CAPS SPACED, settlement names in title case, water in italic

---

## Biome Reference

Each biome defines the **dominant color shift**, **terrain drawing conventions**, and **atmospheric tags** to include in any AI prompt for a settlement in that biome.

### Temperate Forest / Woodland

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Greens dominate: sage `#7A9E7E`, dark fern `#4A6B4A`; brown earth tones for roads | Deciduous tree clusters; clearings where settlement sits; dappled canopy edge suggested by stippling |

**Atmospheric tags:** `lush green canopy, forest clearing, dappled sunlight, moss-covered stone, leaf litter, fern underbrush, deciduous tree clusters, earthen paths`

### Arid Desert / Scrubland

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Ochre and amber dominate: `#C8A96A`, `#B89050`; rock is warm brown; vegetation sparse yellow-green | Dune wave lines, mesa silhouettes, scattered scrub dots, rock outcrop hatching; strong shadows on south-facing cliff faces |

**Atmospheric tags:** `sandy ochre terrain, desert foothills, mesa and canyon walls, scrub brush, arid wind-carved rock, warm amber light, heat shimmer, sparse vegetation`

### Coastal / Maritime

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Steel blue water `#7CA5B8`; seafoam `#A8C5C0` at shore; sandy tan beaches; grey-green coastal vegetation | Shoreline with wave-line border; docks and wharves extending into water; cliff edges where coast is rocky; lighthouse symbols on headlands |

**Atmospheric tags:** `coastal shoreline, harbor docks, wave-line water border, cliff-edge coast, sandy beach, seabird silhouettes, salt-weathered buildings, fishing boats, tidal pools`

### Mountain / Alpine

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Grey-brown rock `#8C7B6B` dominates; snow-white `#D6E4EC` at peaks; dark green conifer `#3D5C3D` on lower slopes | Heavy topographic hatching; fan-radial lines on peaks; conifer tree lines on slopes; switchback road markings; avalanche chute hatching |

**Atmospheric tags:** `mountain peaks, alpine terrain, snow-capped ridges, conifer treeline, switchback mountain paths, steep cliff hatching, avalanche chutes, high altitude thin air`

### Subterranean / Underground

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Deep umber `#5C3D28` dominates; amber `#C8922A` for torchlight zones; pale blue `#8AAAC0` for underground water | Cross-section view where helpful; heavy wall hatching; stalactite symbols on ceiling; glowing crystal accents where magical; water pools with depth shading |

**Atmospheric tags:** `underground cavern, cave chamber cross-section, stalactite ceiling, torch-lit corridors, mineral-vein walls, underground river, glowing crystal accents, deep shadow`

### Swamp / Wetland

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Olive-brown `#7A7A50`; murky blue-grey water `#7A8A8C`; dark green moss `#4A5A3A`; rotting wood brown `#6A5040` | Irregular water patches between land; dead tree silhouettes; reed clusters at water edges; raised wooden walkways; fog suggested by lighter wash at edges |

**Atmospheric tags:** `murky swamp water, dead tree silhouettes, reed clusters, raised wooden walkways, fog wash, moss-covered ruins, stagnant pools, dense underbrush`

### Tundra / Arctic

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Pale blue-white `#D6E4EC` dominates; grey rock `#8C8C8C` where exposed; dark blue-black `#2A3A4A` for deep water or shadow | Snow drift lines; exposed rock ridges; ice-crack patterns on frozen water; sparse windswept shrub; aurora hint at sky edge (very faint green-violet wash) |

**Atmospheric tags:** `frozen tundra, snow drifts, exposed rock ridges, ice-crack patterns, windswept terrain, sparse arctic shrubs, frost crystals, pale blue-white light`

### Volcanic / Scorched

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Charcoal `#3A3028`; ember orange-red `#C44518`; ash grey `#6A6A6A`; molten gold `#D4922A` for lava flows | Jagged rock edges; lava flow channels (bright orange with dark crust); ash-cloud stippling; dead tree stumps; cinder cone silhouettes |

**Atmospheric tags:** `volcanic terrain, lava flow channels, jagged obsidian rock, ash-cloud stippling, cinder cones, ember glow, scorched earth, sulfurous vents`

### Jungle / Tropical

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Deep emerald `#2A6B3A`; bright canopy green `#5A9A4A`; brown-red soil `#8A5A3A`; vibrant flower accents (used sparingly) | Dense overlapping canopy; broad frond shapes; hanging vine lines; river channels through vegetation; ruins half-swallowed by growth |

**Atmospheric tags:** `dense jungle canopy, broad tropical fronds, hanging vines, overgrown ruins, humid atmosphere, river channels through vegetation, colorful bird accents, massive tree trunks`

### Grassland / Plains / Steppe

| Palette Shift | Drawing Notes |
|---------------|---------------|
| Warm yellow-green `#A3B86C`; golden wheat `#C8B060`; distant blue-grey horizon `#A0A8B0` | Rolling terrain with long gentle hatching; grass tuft clusters; wide open spaces; distant settlement silhouettes small on the horizon; road visible from far away |

**Atmospheric tags:** `open grassland, rolling hills, wheat-golden fields, wide horizon, scattered farmsteads, long road stretching to distance, wind-bent grass, open sky`

---

## Settlement Construction Styles

The material and architectural vocabulary of a settlement tells the story of who built it, when, and with what. Match these to the settlement's culture, wealth, and age.

### Material Level

| Level | Materials | Drawing Treatment | Typical Cultures |
|-------|-----------|-------------------|------------------|
| **Hide / Textile** | Animal skins, woven cloth, canvas, enchanted silk | Tent shapes: peaked, rounded, or draped. Fabric texture suggested by gentle curves. Support poles visible. | Nomadic tribes, refugee camps, early frontier |
| **Thatch / Wattle** | Straw, wattle-and-daub, mud brick, reeds | Rounded roof lines, thick irregular walls, organic shapes. Texture: cross-hatching for thatch, stippling for mud. | Hamlets, fishing villages, rural communities |
| **Timber / Log** | Hewn logs, wooden planking, shingle roofs | Rectangular buildings with visible beam lines. Roof hatching for shingle texture. Timber frame visible on larger structures. | Forest settlements, frontier towns, Waldkyn |
| **Stone / Masonry** | Cut stone, mortared walls, slate roofs | Rectangular or angular buildings with clean edges. Block pattern suggested on walls. Towers and multi-story structures. | Established cities, Varnathi settlements, Dwarven surface structures |
| **Dwarven / Deep-Cut** | Mountain-hewn stone, metal reinforcement, carved facades | Geometric precision. Arch doorways. Facade detail suggesting carved relief. Internal chambers shown in cross-section where relevant. | Kharnzarak, Dwarven holdfasts, mountain fortifications |
| **Crystal / Arcane** | Enchanted crystal, mana-infused materials, light-woven structures | Faceted geometric shapes. Faint glow wash around structures. Translucent or semi-transparent fill. | Magical academies, Aen'valar structures, arcane sanctuaries |
| **Technomantic / Hybrid** | Metal plating, steam pipes, crystal-and-gear mechanisms | Industrial silhouettes: chimneys, gear motifs, pipe runs between buildings. Steam plume wisps. Mixed stone-and-metal textures. | Gearhaven, Elm-korin settlements, experimental sites |
| **Living / Grown** | Living wood, shaped stone, mycelial architecture, coral | Organic flowing lines. No sharp corners. Building shapes that merge with surrounding vegetation. Root and branch outlines visible. | Waldkyn groves, Gnomish communities, Hollowkin |

### Defensive Posture

| Level | Features | Drawing Treatment |
|-------|----------|-------------------|
| **Undefended** | No walls, open approaches | No boundary lines. Settlement blends into terrain. |
| **Palisade** | Wooden stake fence, basic gates | Single thick line with point-top hatching |
| **Walled** | Stone walls, gated entries, watch towers | Double thick line with periodic tower bumps; gate symbols at entries |
| **Fortified** | Multiple wall rings, moat, barbican, murder holes | Concentric wall lines; moat as water channel; heavy tower symbols |
| **Concealed** | Hidden entrances, camouflage, magical concealment | Dotted boundary lines; terrain-matching fill; secret entrance symbols (dotted paths) |
| **Natural Barrier** | Cliff, river, canyon, dense forest as defense | Terrain feature drawn prominently with settlement interior shown inside the natural boundary |

---

## Industry & Economy Visual Markers

Add these visual elements to settlement maps based on the settlement's primary economy.

| Economy Type | Map Elements |
|--------------|-------------|
| **Farming / Agricultural** | Field-furrow patterns surrounding the settlement; grain silo shapes; livestock pen outlines; irrigation channels |
| **Fishing / Maritime** | Docks extending into water; boat silhouettes at moorings; net-drying rack shapes; fish market stall canopies |
| **Mining** | Mine entrance symbols in nearby hills; ore cart track lines; slag heap stippling; surface smelter chimney |
| **Logging / Timber** | Log-pile shapes at settlement edge; sawmill building with waterwheel; cleared forest zones; lumber road |
| **Trade / Caravan** | Wide central market square; caravan staging grounds outside walls; warehouse blocks; scale symbols at market |
| **Military / Garrison** | Parade ground (open square); barracks blocks; armory (shield symbol); wall-walk patrol paths |
| **Arcane / Scholarly** | Tower with crystal or flame motif; library building (book symbol); observatory dome; ritual circle in open space |
| **Craft / Artisan** | Workshop cluster (anvil, loom, kiln symbols); guild hall with banner; chimney smoke from forge district |
| **Smuggling / Black Market** | Concealed dock or cave entrance; narrow winding alleys; dead-end streets; unmarked buildings |
| **Religious / Pilgrimage** | Central temple or cathedral dominates skyline; processional avenue; pilgrim quarters; shrine waypoints approaching the settlement |

---

## AI Generation Prompt Templates

### Base Prompt Structure

Every prompt follows this pattern. Replace bracketed sections with specifics from the settlement's map definition file.

#### City Map (Settlement Overview)

```
Fantasy cartography map in Mike Schley style, [SETTLEMENT NAME], bird's-eye view, [ASPECT RATIO if needed]. Hand-drawn linework on aged parchment background. [BIOME] terrain with [KEY GEOGRAPHICAL FEATURES]. [CONSTRUCTION STYLE] buildings, [DEFENSIVE POSTURE]. [2–4 SPECIFIC VISUAL ELEMENTS describing the settlement's unique character]. [BIOME ATMOSPHERIC TAGS]. [PALETTE — from biome section or custom]. Serif font labels, ornate compass rose, scale bar. [N] key landmarks numbered with legend.
```

#### Borough / District Map

```
Fantasy cartography district map in Mike Schley style, [DISTRICT NAME] of [SETTLEMENT NAME]. Hand-drawn linework on aged parchment. [DISTRICT PHYSICAL DESCRIPTION — shape, terrain, density]. Individual building footprints: [LIST KEYED BUILDINGS with 2–3 word descriptions]. [BIOME ATMOSPHERIC TAGS]. [PALETTE]. Numbered key for all [N] locations.
```

#### Hub Map (Dense Zone)

```
Fantasy cartography hub map in Mike Schley style, [HUB NAME] in [DISTRICT NAME], [SETTLEMENT NAME]. Hand-drawn linework on aged parchment. Tightly packed zone: [PHYSICAL LAYOUT — street, courtyard, cluster]. Every location keyed and numbered: [LIST ALL LOCATIONS]. Dense detail: doorways, windows, signage, street furniture visible. [PALETTE]. Numbered legend alongside map.
```

#### Region / Overland Map

```
Fantasy cartography regional map in Mike Schley style, [REGION NAME]. Hand-drawn linework on aged parchment background. [BIOME] terrain stretching [GEOGRAPHIC SCOPE]. Settlements marked as named icons: [LIST SETTLEMENTS]. Roads and trade routes shown as [DESCRIPTION]. [KEY TERRAIN FEATURES]. [BIOME ATMOSPHERIC TAGS]. [PALETTE]. Compass rose, scale bar, legend.
```

---

## Map Checklist

Before finalizing any map:
- [ ] Parchment background present
- [ ] Compass rose included
- [ ] Scale bar included
- [ ] All numbered/lettered points match the key
- [ ] Water labeled in italic
- [ ] Region/area names in ALL CAPS SPACED
- [ ] Settlement name prominent
- [ ] Linework feels hand-drawn, not computer-generated
- [ ] Color palette consistent with Vaeloris standard or documented biome variant
- [ ] Construction style matches the settlement's culture and material level
- [ ] Any magical or special features labeled with descriptive note
- [ ] Industry visual markers present where applicable
