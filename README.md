# Agentic Wiki

A small multi-agent system that builds and maintains a markdown knowledge base instead of relying on vector retrieval. Six agents collaborate to classify what the user is asking, look at what's already written, and decide whether to create, patch, merge, or skip. The wiki grows across sessions, and each note carries derived metadata (confidence, coverage, links) computed from the file itself rather than guessed by the model.

## Why it isn't just a pipeline

The usual multi-agent layout is linear (research -> summarize -> write). Here the MasterAgent picks one of four intents first, and the workflow branches on the intent. A CuratorAgent then emits a JSON plan of file operations and a non-LLM WriterAgent applies it. Keeping the "decide" step separate from the "do" step means you can log or rollback what the model wanted to change, rather than finding out after the fact.

## Architecture

```
          +-------------------------------+
  query ->|          MasterAgent          |-> intent + topic
          +-------------------------------+
                         |
                 +-------+--------+
                 v                v
        +--------------+  +--------------+
        |  Retrieval   |->|   Research   |
        +--------------+  +--------------+
                          |
                          v
                 +--------------+
                 |   Curator    |  -> FileOperationPlan
                 +--------------+
                          v
                 +--------------+
                 |    Writer    |  -> knowledge_base/*.md
                 +--------------+
                          v
                 +--------------+
                 |    Linker    |  -> [[wikilinks]] + backlinks
                 +--------------+
                          v
                 +--------------+
                 |  Validator   |  -> gate, one retry on failure
                 +--------------+
```

### Intents

| Intent | Trigger | Curator behaviour |
|---|---|---|
| `NEW_TOPIC` | Nothing in the wiki covers it | Create one note |
| `EXTEND_TOPIC` | A stub/partial note already exists | Patch the matching section, no duplicate file |
| `COMPARE` | Phrases like "vs", "difference between" | Create a comparison note, cross-link the sources |
| `DEEP_DIVE` | Broad, multi-faceted request | Parent note plus 2-4 child notes |

### Agents

| Agent | Role | Model |
|---|---|---|
| Master | Intent classifier and router | `llama-3.3-70b-versatile` |
| Retrieval | Pulls relevant note bodies (no LLM) | - |
| Research | Gap-aware findings | `llama-3.1-8b-instant` |
| Curator | Decides create / patch / merge / skip | `llama-3.3-70b-versatile` |
| Writer | Applies the plan (no LLM) | - |
| Linker | Adds wikilinks + mirrors backlinks | rules + `llama-3.1-8b-instant` fallback |
| Validator | Structural + hallucination check, one retry | `llama-3.1-8b-instant` |

Models run on [Groq](https://groq.com) via their OpenAI-compatible endpoint. Swapping back to Anthropic, OpenAI, or another provider is a one-file change in [backend/agents/base.py](backend/agents/base.py).

## Layout

```
agentic_wiki/
  backend/
    main.py            FastAPI app + SSE endpoint
    orchestrator.py    runs the agent DAG and emits trace events
    schemas.py         Pydantic contracts shared by all agents
    agents/            master, retrieval, research, curator, writer, linker, validator
    tools/
      notes.py         frontmatter, section patching, derived metadata
      graph.py         wikilink parsing, adjacency + backlink map
  frontend/
    index.html         three-panel UI (query+trace | note viewer | graph+list)
  knowledge_base/      seeded with four canonical notes
  scripts/seed.py
  requirements.txt
  run.sh
```

## Run

Python 3.11+.

```
./run.sh
```

Open http://localhost:8000.

If you don't have a key, you can still exercise the UI, SSE trace and file writes:

```
MOCK_MODE=1 ./run.sh
```

With a real key, drop it in `.env`:

```
GROQ_API_KEY=gsk_...
MOCK_MODE=0
```

A free Groq key works — grab one at https://console.groq.com/keys.

## Try it

Preloaded wiki: Transformers, Attention Mechanism, RLHF, Tokenization.

- `Explain PPO` -> intent `EXTEND_TOPIC`, curator patches the existing RLHF note instead of creating a duplicate.
- `Compare BPE vs WordPiece` -> intent `COMPARE`, new comparison note with cross-links.
- `What is KV cache?` -> intent `NEW_TOPIC`, fresh note auto-linked to Attention Mechanism.

The agent trace panel streams start/end events for each agent live over SSE while the run is happening.

## Derived metadata

Every note's frontmatter includes fields computed from the file itself, not invented by the model:

```
title: PPO
created: 2026-04-17
updated: 2026-04-17
revision: 2
tags: [alignment, rl]
parent: rlhf
summary: ...
validator_passed: true
```

Confidence is weighted from source count, validator result, coverage tier (stub / partial / comprehensive) and incoming links:

```
confidence = 0.35 * sources + 0.30 * validator + 0.25 * coverage + 0.10 * links_in
```

## Notes on scope

- No vector DB, no embeddings. The brief specifically asks for file-based knowledge rather than RAG, and the notes index (slug, title, tags, summary) fits easily in a cached system prompt at this size.
- No auth, no database. One directory of markdown files.
- SSE carries agent-level events, not token streams. The signal people care about is which agent is running, not the tokens.
- Frontend is a single HTML file with Tailwind and vis-network over CDN. No build step.
