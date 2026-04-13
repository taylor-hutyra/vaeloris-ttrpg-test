"""Build a single-page GM reference PDF of Lux Aeterna events for Session 1."""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT

OUT = r"c:\Users\Taylo\writing\Vaeloris - TTRPG example\Campaign\Session-01\Lux-Aeterna-GM-OnePager.pdf"

INK = HexColor("#1a1a1a")
ACCENT = HexColor("#8B3A1A")
MUTED = HexColor("#5a5a5a")
BOX = HexColor("#f4ebd9")

doc = SimpleDocTemplate(
    OUT, pagesize=LETTER,
    leftMargin=0.4*inch, rightMargin=0.4*inch,
    topMargin=0.35*inch, bottomMargin=0.35*inch,
)

ss = getSampleStyleSheet()
H = ParagraphStyle("H", parent=ss["Title"], fontSize=13, leading=15,
                   textColor=ACCENT, alignment=TA_LEFT, spaceAfter=2)
SUB = ParagraphStyle("SUB", parent=ss["Normal"], fontSize=7.5, leading=9,
                     textColor=MUTED, spaceAfter=4, fontName="Helvetica-Oblique")
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=8.6, leading=10,
                    textColor=ACCENT, spaceBefore=3, spaceAfter=1,
                    fontName="Helvetica-Bold")
BODY = ParagraphStyle("BODY", parent=ss["Normal"], fontSize=7, leading=8.4,
                      textColor=INK, spaceAfter=1.5)
READ = ParagraphStyle("READ", parent=BODY, fontSize=6.9, leading=8.3,
                      leftIndent=6, rightIndent=4, textColor=HexColor("#3a2410"),
                      fontName="Helvetica-Oblique", spaceAfter=2)
TINY = ParagraphStyle("TINY", parent=BODY, fontSize=6.5, leading=7.8)

story = []

story.append(Paragraph("LUX AETERNA — GM ONE-PAGER (Session 1, Beats 4–7)", H))
story.append(Paragraph("<b>Arc:</b> violence &rarr; wonder &rarr; unease &rarr; awe &nbsp;|&nbsp; <b>Setting:</b> hidden mage-refuge, pop. ~340, cloaked by mirror-charms &amp; Mage-Weave &nbsp;|&nbsp; <b>Date:</b> TA 412", SUB))

# Beat 4
story.append(Paragraph("BEAT 4 — The Return (5–10 min, desert road)", H2))
story.append(Paragraph("Quiet beat. Let new PCs (Aen'valar elf, dwarf) exchange a line or two with returning PCs. Full strain recover, no wound heal. Optional prompts: ride with the silent dwarf? sit with the sleepless elf? who briefs Tajsh?", BODY))

# Arrival read-aloud
story.append(Paragraph("ARRIVAL — READ ALOUD", H2))
story.append(Paragraph("<i>\"The sun has been down an hour by the time you ride in. The lanterns are lit — tavern to barracks, the standing lantern at the well, Hask's windows. But they aren't steady. One flickers, two burn clean, one flickers, one goes almost out and flares back up. You've lived here long enough to know this isn't normal. People in the market have stopped arguing. Nobody is shouting. Someone — you can't see who — is humming. A single sustained note. It's coming from the mouth of the Warrens.\"</i>", READ))

# Tonight's Wrongness
story.append(Paragraph("TONIGHT'S WRONGNESS (lace into every scene — all simultaneous)", H2))
story.append(Paragraph("&bull; Lanterns stutter asymmetrically &nbsp; &bull; Well-water tastes metallic &nbsp; &bull; Mage-Weave stutters (Selin can feel it) &nbsp; &bull; 3 of 4 working dogs refuse to come inside &nbsp; &bull; Candles near the Vault freeze mid-flicker &nbsp; &bull; Old Cira hums one sustained note, facing the Warrens. <b>The settlement is holding its breath.</b>", BODY))

# Beat 5 Tajsh drop + vignettes table
story.append(Paragraph("BEAT 5 — THE CITY IS OFF (20–25 min)", H2))
story.append(Paragraph("<b>First stop — Tajsh's Office.</b> He takes the Band. Candle freezes mid-flicker; he moves it across the room, it still freezes. <i>\"Give me tonight with this. Come back in the morning.\"</i> On the new arrivals: <i>\"They're with you? Fine. They eat with you. They sleep where you sleep. If they're what they say, we're lucky. If they're not — you're my trap.\"</i> He does NOT mention the symbol yet.", BODY))

vdata = [
    ["LOCATION", "NPC", "THE WRONGNESS / HOOK"],
    ["The Dusty Lantern", "Marta Dustborn (human, 40s, burn-scars)", "Lanterns out of rhythm. Half-empty. \"They've been doing that for an hour. I'm not going to be the one who asks why.\" Serves the elf without asking where he came from."],
    ["Hask's Workshop", "Hask (Orkin alchemist, 30s)", "Potion simmers 1 hr — neither boils nor cools. Hands cup of warm something: \"Whatever you brought back — it's in the walls now.\" To elf: \"You've been somewhere my people used to go. Before.\""],
    ["Ladder in canyon", "Selin Voss (gnome, 50s)", "Patching Mage-Weave. Grabs a sleeve: \"Does this look right? Tell me if it looks wrong.\" Ambient mana is unpredictable. If she dies, the cover fails in weeks."],
    ["The Well", "Oris Hallow + crowd + Petra (10)", "METALLIC WATER. Oris (sick wife) publicly accuses Petra of poisoning it via sparks. Run this one. Charm/Negotiation ◆◆, Coercion ◆◆◆, or Arcana ◆◆ to explain the Band. Do nothing → Sabel arrives in 2 min, crowd disperses, tension remains. Petra remembers."],
    ["Vault entrance", "Old Cira (Lothari seer)", "Humming one note, facing the Warrens. If the ELF passes: stops humming. \"Two of you are walking. Only one came back.\" Returns to humming. No clarification. DO NOT EXPLAIN."],
    ["Perimeter / outlook", "Warden Sabel (human, 40s)", "Checking crossbows for the 3rd time — this is how he sits still. \"Everything is exactly what it is. I'm checking the bows.\" He saw the candle freeze. He is counting the wrongnesses."],
]
vt = Table(vdata, colWidths=[0.95*inch, 1.6*inch, 5.0*inch])
vt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), ACCENT),
    ("TEXTCOLOR", (0,0), (-1,0), HexColor("#ffffff")),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 6.5),
    ("LEADING", (0,0), (-1,-1), 7.8),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.25, MUTED),
    ("BACKGROUND", (0,1), (-1,-1), BOX),
    ("LEFTPADDING", (0,0), (-1,-1), 3),
    ("RIGHTPADDING", (0,0), (-1,-1), 3),
    ("TOPPADDING", (0,0), (-1,-1), 2),
    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
]))
story.append(vt)
story.append(Paragraph("Run 2–3 vignettes (not all). <b>Always run the Well.</b> Cut to morning when done.", TINY))

# Beat 6
story.append(Paragraph("BEAT 6 — TAJSH'S REVELATION (10–15 min, Tajsh's Office, morning)", H2))
story.append(Paragraph("Gray morning. Lanterns stabilized. Tajsh has read the journal, hasn't slept. Band wrapped in dark wool on desk. Kettle whistling, ignored. Two chairs for five.", BODY))
story.append(Paragraph("<b>THE MONOLOGUE (read slowly, don't paraphrase):</b> <i>\"I've seen that symbol twice in my life. Once when I was twenty-two. Shadewalker archive. Sealed crate — three rings interlocked burned into the lid. I tried to draw it later. I couldn't. Neither could Torvin. Second time — seventeen years ago. Ruin in the Barren Hills. I was paid a great deal of money to forget I'd been there. My employer paid me to carve the room shut and walk away. I did. Both times, everyone in the room treated it like a cobra. Nobody wanted to reach for it... I need that book from the pedestal. Go back. Bring it to me. The kind of people who use that symbol don't leave things in mines by accident. They leave them for someone to find. I'd like to know who — before whoever gets here first.\"</i>", READ))
story.append(Paragraph("<b>Ledger beat:</b> asks new PCs their names, writes them down, asks for next-of-kin. Not because he wants to know — because someone has to write it.", BODY))
story.append(Paragraph("<b>THE FLICKER (interruption as they leave):</b> <i>EVERY lantern in the canyon goes OUT at once. One heartbeat. Then back on, brighter, and settles. The mirror-charms dropped. Lux Aeterna was visible from the sky for one heartbeat.</i> Tajsh: <i>\"That was bad. That was very bad. Stay here.\"</i> Sabel is already running toward the outlook. Cira's hum is climbing in pitch. She finds the party at the Warrens' mouth: <i>\"I cannot follow you where this goes. Listen carefully. Doubt generously. Come back.\"</i>", BODY))

# Beat 7
story.append(Paragraph("BEAT 7 — THE ARCHITECT (25–30 min, Deep Chamber via the Warrens)", H2))
story.append(Paragraph("<b>DESCENT (read aloud):</b> <i>\"The tunnel narrows. Walls older than the rest of the settlement — because they are. Lux Aeterna was built over someone else's ruin. The air cools. The torch flame flickers slower. Slower. Then stops flickering. Still burning. Just not moving. You reach the chamber. Round, empty, stone. And then the last of you crosses the threshold.\"</i>", READ))
story.append(Paragraph("<b>TRANSITION (pause between sentences):</b> <i>\"The stone behind you is no longer there. Not dark. Not hidden. Not THERE... Rings of geometric light rotate in planes that don't intersect the way your eyes expect. Some symbols are versions of the three-ring mark. There is no door. No floor — but you are not falling. At the center: not a figure. A CENTER. A point where the geometry converges, and something is looking back.\"</i> PAUSE. Let players break silence. Then: <i>\"I have been waiting a long time to meet you.\"</i>", READ))
story.append(Paragraph("<b>Pocket-space rules:</b> 3 hrs outside = 5 min inside &nbsp;|&nbsp; No door, no exit until released &nbsp;|&nbsp; Weapons do nothing (Discipline ◆◆ to recognize) &nbsp;|&nbsp; Voices sound echoless. <b>PLAY THE ARCHITECT AS RELIEF, NOT THREAT.</b> Primary signal: being-seen.", BODY))
story.append(Paragraph("<b>PHASE 2 — THE NAMING.</b> Names each PC, says something true and specific. Elf: <i>\"Child of the long silence... that choice is why the song found you first.\"</i> Dwarf: <i>\"Son of the stone-line... you were not lost in the dark. You were CALLED. Nothing is wasted. Not even grief.\"</i>", BODY))
story.append(Paragraph("<b>PHASE 3 — THE MESSAGE (6 beats, continuous):</b> (1) The Band is a fragment of an instrument that once nearly ended the world. Two more remain. (2) \"I do not know where they are. The fragments were hidden by gods. Hidden from me too.\" (3) \"I am a servant of the Four. Left behind to watch, to wait, to speak.\" (4) A plinth of folded light rises — a palm-sized dark crystal wrapped in pale metal, humming. <b>The Resonance Compass.</b> (5) \"It sings when a fragment is near. Go NORTH. The Dragon's Tooth. The observatory at its peak — any lens trained on the sky will see the fragments' mark.\" (6) \"Gathered, they must be brought to a wound in the world and unmade there. Nowhere else.\"", BODY))
story.append(Paragraph("<b>PHASE 4 — THE QUESTIONS.</b> GM voice: <i>\"It has said what it came to say. It is waiting. You can ask it anything.\"</i> Prepared checks: Perception ◆◆ = no reflection in the symbols. Perception ◆◆◆ = anticipation (triumph: hunger) on \"unmaking.\" Arcana ◆◆◆ = divine overlay on ABYSSAL core. Lore ◆◆◆◆ = the three-ring mark is a CHORD, not a rune. Discipline ◆◆ = Naming is too tailored — targeting, not therapy. Charm/Negotiation ◆◆◆ = reveals extra: <b>Brenn Hallowveil</b> (last observatory custodian) OR a Waldkyn Song-Ward master. Coercion ◆◆◆◆◆ fails — amused.", BODY))
story.append(Paragraph("<b>EXIT:</b> <i>\"Go north. Take the Band. Take the Compass. Trust the people who love you. Do not trust me further than you have to. This is the only honest thing I will say tonight.\"</i> Geometry folds; single blink. Torch flickers again. Compass is warm in someone's hand (default: the elf).", BODY))
story.append(Paragraph("<b>CIRA'S QUESTION (session close):</b> <i>\"How long were you gone?\"</i> A PC: \"A few minutes.\" Cira: <i>\"It has been three hours. I could not see you. I was not sure you were coming back. How do you feel?\"</i> Go around the table. Each PC, in character, ONE sentence. No follow-ups. When the fifth has spoken: <b>\"That's where we leave it. Good game.\"</b> END.", BODY))

doc.build(story)
print(f"Wrote: {OUT}")
