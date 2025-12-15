# Implementation Plan: Integrated RAG Chatbot

**Branch**: `001-rag-chatbot` | **Date**: 2025-12-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rag-chatbot/spec.md`

## Summary

Build a RAG chatbot embedded in the existing Docusaurus AI textbook with two strictly separated modes:
1. **Full-book RAG mode**: Retrieve relevant chunks from Qdrant vector store, generate answers with Gemini
2. **Selected-text mode**: Answer based only on user-highlighted text (no retrieval)

**Technical Approach**: FastAPI backend with OpenAI Agents SDK for agent logic, ChatKit.js frontend injected via Docusaurus Root component swizzle, Cohere for embeddings (via OpenAI-compatible API), Gemini for generation (via OpenAI-compatible API), Qdrant Cloud for vector storage, Neon PostgreSQL for metadata.

## Technical Context

**Language/Version**: Python 3.11+, JavaScript/TypeScript (Docusaurus)
**Primary Dependencies**: FastAPI, OpenAI Agents SDK, qdrant-client, asyncpg, ChatKit.js
**Storage**: Qdrant Cloud (vectors), Neon PostgreSQL (metadata)
**Testing**: pytest, manual E2E testing
**Target Platform**: Local development (Windows/Linux/macOS)
**Project Type**: Web application (Python backend + JavaScript frontend embedded in existing Docusaurus)
**Performance Goals**: <10s response time, streaming begins <2s, 10 concurrent users
**Constraints**: Local development only, no deployment; ChatKit.js mandatory; Context7 compliance required
**Scale/Scope**: ~12 documents, ~100 chunks, single developer use

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Respect existing project structure | PASS | All Python files at project root, ai-textbook/ untouched except swizzle |
| II. Correct technical initialization | PASS | Plan starts with `uv init`, follows with `uv add` |
| III. Context7 compliance | PASS | All technology patterns researched via Context7 MCP |
| IV. Zero hallucination | PASS | Agent instructions explicitly ground answers in retrieved/selected text |
| V. Strict mode separation | PASS | Mode determined by presence of `selected_text` in request |
| VI. Minimal modifications | PASS | Only Root component swizzle, easily reversible |

**Technology Stack Compliance**:
| Component | Required | Planned | Status |
|-----------|----------|---------|--------|
| Package Manager | uv | uv | PASS |
| Web Framework | FastAPI | FastAPI | PASS |
| Agent Framework | OpenAI Agents SDK | OpenAI Agents SDK | PASS |
| Embeddings | Cohere (OpenAI-compatible) | Cohere via AsyncOpenAI | PASS |
| Generation | Gemini (OpenAI-compatible) | Gemini via AsyncOpenAI | PASS |
| Vector Store | Qdrant Cloud | AsyncQdrantClient | PASS |
| Metadata Store | Neon PostgreSQL | asyncpg | PASS |
| Chat UI | ChatKit.js | @openai/chatkit | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-rag-chatbot/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Technology research
├── data-model.md        # Phase 1: Data model design
├── quickstart.md        # Phase 1: Setup guide
├── contracts/           # Phase 1: API contracts
│   ├── api.yaml         # OpenAPI specification
│   └── frontend-backend.md # Protocol documentation
└── tasks.md             # Phase 2: Implementation tasks (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
project-root/
├── .env                     # Environment variables (credentials)
├── pyproject.toml           # Python project config (uv init)
├── main.py                  # FastAPI application entry point
├── ingest.py                # Book content ingestion script
├── rag_tools.py             # RAG agent tools (@function_tool)
├── db.py                    # Database connection and queries
├── config.py                # Configuration loading from .env
│
├── ai-textbook/             # EXISTING Docusaurus site (DO NOT RECREATE)
│   ├── docs/                # Book content (.md, .mdx files) - source for RAG
│   ├── src/
│   │   └── theme/
│   │       └── Root.js      # Swizzled component with ChatKit injection
│   ├── docusaurus.config.js # May need minor config for ChatKit CSS
│   └── package.json         # Add @openai/chatkit dependency
│
├── specs/                   # Feature specifications
├── history/                 # PHR and ADR records
└── .specify/                # SpecKit Plus templates
```

**Structure Decision**: Flat Python files at project root (per constitution requirement) with swizzled React component in existing Docusaurus structure. No nested backend/ folder needed as this is a simple single-service application.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Docusaurus Site                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ai-textbook/src/theme/Root.js              │   │
│  │  ┌───────────────────────────────────────────────────────┐   │   │
│  │  │                    ChatKit.js Panel                    │   │   │
│  │  │  - Text input for questions                            │   │   │
│  │  │  - Streaming response display                          │   │   │
│  │  │  - Text selection detection                            │   │   │
│  │  └───────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /chatkit (SSE streaming)
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     main.py (ChatKit Server)                  │   │
│  │  - /chatkit endpoint (ChatKit protocol)                       │   │
│  │  - /health endpoint                                           │   │
│  │  - Mode detection (RAG vs selected-text)                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│          ┌─────────────────────────┼─────────────────────────┐      │
│          ▼                         ▼                         ▼      │
│  ┌───────────────┐     ┌───────────────────┐     ┌───────────────┐ │
│  │  rag_tools.py │     │ OpenAI Agents SDK │     │    db.py      │ │
│  │ @function_tool│     │  Agent + Runner   │     │ asyncpg       │ │
│  │ search_book() │     │  (Gemini model)   │     │ Neon Postgres │ │
│  └───────┬───────┘     └───────────────────┘     └───────────────┘ │
│          │                                                          │
└──────────┼──────────────────────────────────────────────────────────┘
           │
           │ Semantic search
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Qdrant Cloud      │     │   Cohere API        │
│   Vector Store      │     │   (Embeddings)      │
│   book_chunks       │     │   embed-v4.0        │
└─────────────────────┘     └─────────────────────┘
```

## Data Flow

### Full-Book RAG Mode

```
1. User types question in ChatKit
2. ChatKit sends POST /chatkit (no selected_text in context)
3. Backend detects RAG mode
4. Agent runs with search_book tool available
5. Agent calls search_book(query)
   a. Embed query via Cohere
   b. Search Qdrant for top-5 similar chunks
   c. Return chunks as context
6. Agent generates response using Gemini with retrieved context
7. Response streams via SSE to ChatKit
8. ChatKit displays streaming response
```

### Selected-Text Mode

```
1. User highlights text on page
2. User types question in ChatKit
3. ChatKit sends POST /chatkit (selected_text in context)
4. Backend detects selected-text mode
5. Agent runs with NO tools (selected text as context)
6. Agent generates response using Gemini with only selected text
7. Response streams via SSE to ChatKit
8. ChatKit displays streaming response
```

### Ingestion Flow

```
1. Developer runs: python ingest.py
2. Script discovers all .md/.mdx in ai-textbook/docs/
3. For each document:
   a. Extract title from first H1 or filename
   b. Compute content hash
   c. Check if document exists (by path) and hash matches
   d. If new/changed: chunk document (500-1000 tokens, 100 overlap)
   e. Generate embeddings via Cohere for each chunk
   f. Upsert to Qdrant with payload metadata
   g. Upsert document/chunk records to Neon PostgreSQL
4. Report summary
```

## Key Implementation Details

### Agent Configuration

```python
from agents import Agent, function_tool, Runner
from openai import AsyncOpenAI

# Gemini client (OpenAI-compatible)
gemini_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# RAG mode agent (with tools)
rag_agent = Agent(
    name="Book Assistant",
    instructions="""You are a helpful assistant for the AI Robotics textbook.
    Use the search_book tool to find relevant content before answering.
    Always cite your sources. If you cannot find relevant information, say so.""",
    model="gemini-1.5-flash",
    tools=[search_book],
)

# Selected-text mode agent (no tools)
def create_selection_agent(selected_text: str) -> Agent:
    return Agent(
        name="Selection Assistant",
        instructions=f"""Answer the user's question based ONLY on this text:

{selected_text}

Do not use any external knowledge. If the answer is not in the text, say so.""",
        model="gemini-1.5-flash",
        tools=[],  # NO tools in selected-text mode
    )
```

### Streaming Response Pattern

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

async def stream_response(agent, input_text):
    result = Runner.run_streamed(agent, input=input_text)
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                yield f"event: message\ndata: {json.dumps({'delta': event.data.delta})}\n\n"
    yield f"event: done\ndata: {{}}\n\n"

@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    body = await request.json()
    selected_text = body.get("context", {}).get("selected_text")
    message = body["message"]["content"]

    if selected_text:
        agent = create_selection_agent(selected_text)
    else:
        agent = rag_agent

    return StreamingResponse(
        stream_response(agent, message),
        media_type="text/event-stream"
    )
```

## Complexity Tracking

> No constitution violations requiring justification.

| Aspect | Complexity Level | Justification |
|--------|------------------|---------------|
| Agent tools | Low | Single `search_book` tool |
| Mode switching | Low | Conditional agent selection |
| Streaming | Medium | SSE via FastAPI StreamingResponse |
| Frontend integration | Low | ChatKit handles complexity |
| Data model | Low | 2 tables + 1 Qdrant collection |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Cohere API rate limits | Batch embedding during ingestion; cache query embeddings |
| Gemini streaming compatibility | Use OpenAI-compatible endpoint; fallback to non-streaming if issues |
| Qdrant Cloud connectivity | Health check endpoint; graceful error messages |
| ChatKit protocol changes | Pin ChatKit version; follow official examples |
| Token limits | Chunk size ~500-1000 tokens; limit retrieved chunks to top-5 |

## Dependencies Summary

### Python (project root)
```
fastapi>=0.109.0
uvicorn>=0.27.0
openai>=1.12.0
openai-agents>=0.1.0
qdrant-client>=1.7.0
asyncpg>=0.29.0
python-dotenv>=1.0.0
```

### JavaScript (ai-textbook/)
```
@openai/chatkit
```

## Next Steps

Run `/sp.tasks` to generate the implementation task list based on this plan.
