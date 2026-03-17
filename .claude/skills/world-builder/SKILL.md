---
name: world-builder
description: World Builder reference and status. Use /wb-create, /wb-query, /wb-write, etc. for specific tasks. Run this to check system health.
---
<!-- WB_STATE: ready -->

# World Builder

Setup complete. Available commands:

| Command | Purpose |
|---------|---------|
| `/wb-create` | Create entities (person, place, event, faction, etc.) with AI assistance |
| `/wb-query` | Natural language world queries, temporal state, semantic search |
| `/wb-ingest` | Parse unstructured text into structured entities |
| `/wb-suggest` | AI suggestions — characters, faction responses, plot ideas |
| `/wb-consequences` | Analyze ripple effects of changes, propagate across entities |
| `/wb-consistency` | Audit for contradictions, gaps, broken links |
| `/wb-write` | Generate narrative content (chapters, era histories, lore, vignettes) |
| `/wb-timeline` | Compile chronological timeline summaries |

## Health Check

When this skill is invoked, run a health check:

1. Check Python venv exists: `_meta/.wb-venv/`
2. Check stores exist: `_meta/wb.db`, `_meta/wb-graph.json`, `_meta/chroma/`
3. Run sync status:
   ```bash
   _meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py sync --status
   ```
4. Report any issues to the user.

## Troubleshooting

- **Re-sync stores**: `_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py sync --full`
- **Verify store consistency**: `_meta/.wb-venv/Scripts/python .claude/skills/world-builder/_lib/wb.py sync --verify`
- **Re-install deps**: `_meta/.wb-venv/Scripts/pip install -r .claude/skills/world-builder/_lib/requirements.txt`
