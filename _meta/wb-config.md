---
wb-type: config
models:
  default: claude
  creative: gemini
  available:
    claude:
      cli: claude
      strengths:
        - analysis
        - structure
        - consistency
    gemini:
      cli: gemini
      prompt-via: stdin
      strengths:
        - creative-writing
        - prose
        - dialogue
    ollama:
      cli: "ollama run llama3"
      prompt-via: stdin
      strengths:
        - offline
        - free
        - fast-iteration
model-routing:
  suggest-character: default
  write-chapter: creative
  consequences: default
  write-lore: creative
  write-era: creative
  write-vignette: creative
  faction-response: default
  consistency: default
  ingest: default
mode: ask
embeddings:
  provider: openai
  model: text-embedding-3-large
  configs:
    gemini:
      model: text-embedding-004
      dimensions: 768
      api: rest
    openai:
      model: text-embedding-3-small
      dimensions: 1536
      api: rest
    ollama:
      model: nomic-embed-text
      dimensions: 768
      api: rest
      endpoint: "http://localhost:11434"
    custom:
      model: null
      dimensions: null
      api: rest
      endpoint: null
---

# World Builder Configuration

## Models

Configure which AI models handle different tasks. Each model needs a CLI command that accepts prompts.

- **default**: Used for structural/analytical tasks (character suggestions, consequences, consistency checks)
- **creative**: Used for prose generation (chapters, lore, vignettes)

### Available Models

| Model | CLI Command | Strengths |
|-------|------------|-----------|
| claude | `claude` | analysis, structure, consistency |
| gemini | `gemini` (via stdin) | creative-writing, prose, dialogue |
| ollama | `ollama run llama3` (via stdin) | offline, free, fast-iteration |

## Model Routing

Each task type is routed to either the `default` or `creative` model:

- **default**: suggest-character, consequences, faction-response, consistency, ingest
- **creative**: write-chapter, write-lore, write-era, write-vignette

## Mode

- `ask`: AI proposes changes and waits for approval (default)
- `autonomous`: AI applies changes directly, logs everything for review/rollback

## Embeddings

Semantic search uses vector embeddings for finding related entities. Configure the provider and model here.

- **gemini**: `text-embedding-004` (768 dimensions) — default, good balance of quality and cost
- **openai**: `text-embedding-3-small` (1536 dimensions) — high quality, requires API key
- **ollama**: `nomic-embed-text` (768 dimensions) — local/offline, no API key needed
- **custom**: Bring your own embedding endpoint
