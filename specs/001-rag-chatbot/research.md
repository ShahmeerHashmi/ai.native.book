# Research: Integrated RAG Chatbot

**Feature Branch**: `001-rag-chatbot`
**Date**: 2025-12-15

## Technology Research Summary

### 1. FastAPI Application Structure

**Decision**: Use standard FastAPI application with StreamingResponse for SSE

**Rationale**:
- FastAPI provides native `StreamingResponse` class for streaming large files or continuous data
- SSE (Server-Sent Events) supported via `media_type="text/event-stream"`
- Async generators work seamlessly with FastAPI's async/await pattern
- ChatKit Python SDK provides ready-made integration patterns

**Key Patterns** (from Context7):
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def generate_stream():
    for i in range(10):
        yield f"data: Item {i}\n\n"
        await asyncio.sleep(0.5)

@app.get("/stream")
async def stream_data():
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

**Alternatives Considered**:
- WebSockets: More complex, overkill for one-way streaming
- Long polling: Less efficient than SSE

---

### 2. OpenAI Agents SDK

**Decision**: Use `@function_tool` decorator with `Runner.run_streamed()` for streaming agent responses

**Rationale**:
- Native streaming support via `Runner.run_streamed()` and `stream_events()`
- `@function_tool` decorator converts Python functions to callable agent tools
- Supports async functions naturally
- Built-in event types for tool calls, message outputs, and raw response deltas

**Key Patterns** (from Context7):
```python
from agents import Agent, Runner, function_tool
from openai.types.responses import ResponseTextDeltaEvent

@function_tool
def search_book(query: str) -> str:
    """Search the book for relevant content."""
    # Implementation
    return "relevant content"

agent = Agent(
    name="RAG Assistant",
    instructions="Answer questions using the search_book tool.",
    tools=[search_book],
)

# Streaming execution
result = Runner.run_streamed(agent, input="What is ROS2?")
async for event in result.stream_events():
    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="", flush=True)
```

**Alternatives Considered**:
- LangChain: Heavier, not required by constitution
- Direct OpenAI API: Less structured agent patterns

---

### 3. Qdrant Vector Database

**Decision**: Use `AsyncQdrantClient` for non-blocking vector operations

**Rationale**:
- Native async client for FastAPI compatibility
- Simple upsert and search operations
- Supports payload filtering for metadata queries
- Cloud-hosted free tier available

**Key Patterns** (from Context7):
```python
from qdrant_client import AsyncQdrantClient, models

client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Create collection
await client.create_collection(
    collection_name="book_chunks",
    vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
)

# Upsert vectors
await client.upsert(
    collection_name="book_chunks",
    points=[
        models.PointStruct(
            id=idx,
            vector=embedding,
            payload={"source": "docs/intro.md", "chunk_index": 0}
        )
    ],
)

# Search
results = await client.search(
    collection_name="book_chunks",
    query_vector=query_embedding,
    limit=5,
)
```

**Alternatives Considered**:
- Pinecone: Not specified in constitution
- ChromaDB: Local-only, less cloud-ready

---

### 4. Cohere Embeddings via OpenAI Compatibility API

**Decision**: Use OpenAI SDK with Cohere's compatibility endpoint

**Rationale**:
- Constitution mandates Cohere only for embeddings
- OpenAI-compatible API allows using familiar `openai` SDK patterns
- Model: `embed-v4.0` (or `embed-english-v3.0`)
- Supports `encoding_format="float"` for vector output

**Key Patterns** (from Context7):
```python
from openai import AsyncOpenAI

cohere_client = AsyncOpenAI(
    base_url="https://api.cohere.ai/compatibility/v1",
    api_key=COHERE_API_KEY,
)

response = await cohere_client.embeddings.create(
    input=["text to embed"],
    model="embed-v4.0",
    encoding_format="float",
)
embedding = response.data[0].embedding
```

**Vector Dimensions**: 1024 (for embed-english-v3.0 / embed-v4.0)

**Alternatives Considered**:
- Native Cohere SDK: Constitution requires OpenAI-compatible clients only

---

### 5. Google Gemini via OpenAI-Compatible Endpoint

**Decision**: Use AsyncOpenAI with Gemini's compatibility endpoint

**Rationale**:
- Constitution mandates Gemini only for generation
- OpenAI-compatible endpoint allows seamless integration
- Model: `gemini-1.5-flash` (or latest stable)

**Key Patterns** (from constitution):
```python
from openai import AsyncOpenAI

gemini_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Use with OpenAI Agents SDK
from agents import OpenAIChatCompletionsModel

model = OpenAIChatCompletionsModel(
    model="gemini-1.5-flash",
    openai_client=gemini_client,
)
```

**Alternatives Considered**:
- Native Google AI SDK: Constitution requires OpenAI-compatible clients only

---

### 6. ChatKit.js Frontend Integration

**Decision**: Use vanilla JS custom element with CDN import in swizzled Docusaurus component

**Rationale**:
- ChatKit provides `<openai-chatkit>` custom Web Component
- Can be embedded in any HTML page
- Connects to FastAPI backend via configurable API URL
- Supports streaming responses out of the box

**Key Patterns** (from Context7):
```javascript
import '@openai/chatkit';

const chatkit = document.createElement('openai-chatkit');
chatkit.setOptions({
  api: {
    url: 'http://localhost:8000/chatkit',
    domainKey: 'local-dev',
  },
});
document.getElementById('chat-root')?.append(chatkit);
```

**Alternatives Considered**:
- Custom React chat component: Constitution mandates ChatKit.js only

---

### 7. ChatKit Python Server

**Decision**: Extend `ChatKitServer` class with custom `respond` method integrating Agents SDK

**Rationale**:
- ChatKit Python SDK provides server scaffolding
- `respond` method returns `AsyncIterator[ThreadStreamEvent]`
- Built-in `stream_agent_response` helper for Agents SDK integration
- Handles SSE streaming automatically

**Key Patterns** (from Context7):
```python
from chatkit.server import ChatKitServer, ThreadStreamEvent, StreamingResult
from agents import Agent, Runner

class MyChatKitServer(ChatKitServer):
    assistant_agent = Agent(
        model="gemini-1.5-flash",
        name="RAG Assistant",
        instructions="You are a helpful assistant",
        tools=[search_book],
    )

    async def respond(self, thread, input, context):
        result = Runner.run_streamed(
            self.assistant_agent,
            input,
            context=context,
        )
        async for event in stream_agent_response(context, result):
            yield event

# FastAPI endpoint
@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    result = await server.process(await request.body(), {})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    return Response(content=result.json, media_type="application/json")
```

---

### 8. Docusaurus Component Swizzling

**Decision**: Swizzle the `Root` component to inject ChatKit globally

**Rationale**:
- Root component wraps entire React tree
- Single injection point for chat panel on all pages
- Minimal modification to existing site
- Easy to undo (just delete the swizzled file)

**Key Patterns** (from Context7):
```bash
npm run swizzle @docusaurus/theme-classic Root -- --wrap
```

Creates `src/theme/Root.js`:
```javascript
import React from 'react';

export default function Root({children}) {
  return (
    <>
      {children}
      <div id="chatkit-container" style={{position: 'fixed', bottom: 20, right: 20}} />
    </>
  );
}
```

**Alternatives Considered**:
- Custom plugin: More complex, same result
- Direct config injection: Less control over positioning

---

### 9. Text Selection Detection

**Decision**: Use browser `window.getSelection()` API with event listeners

**Rationale**:
- Standard browser API, no dependencies
- Works across all modern browsers
- Can detect selection changes in real-time

**Key Pattern**:
```javascript
document.addEventListener('mouseup', () => {
  const selection = window.getSelection();
  const selectedText = selection?.toString().trim();
  if (selectedText && selectedText.length > 0) {
    // Show "Ask about selection" button
    // Store selected text for chat context
  }
});
```

---

### 10. Mode Separation Strategy

**Decision**: Use different system prompts and conditional tool availability

**Rationale**:
- Full-book RAG mode: Agent has access to `search_book` tool
- Selected-text mode: Agent receives selected text in context, NO tools available
- Mode is determined by presence of `selected_text` in request payload
- Simple, clear separation without complex state management

**Implementation**:
```python
@function_tool
def search_book(query: str) -> str:
    """Search the entire book for relevant content."""
    # Only available in full-book mode

# In respond():
if selected_text:
    # Selected-text mode: no tools, direct context
    agent = Agent(
        name="Selection Assistant",
        instructions=f"Answer based ONLY on this text:\n\n{selected_text}",
        tools=[],  # NO tools
    )
else:
    # Full-book RAG mode
    agent = Agent(
        name="Book Assistant",
        instructions="Search the book to answer questions.",
        tools=[search_book],
    )
```

---

## Resolved Unknowns

| Unknown | Resolution |
|---------|------------|
| FastAPI streaming pattern | Use `StreamingResponse` with async generators |
| Agent tool definition | Use `@function_tool` decorator |
| Qdrant async operations | Use `AsyncQdrantClient` |
| Cohere embedding API | Use OpenAI SDK with Cohere base_url |
| Gemini generation API | Use OpenAI SDK with Gemini base_url |
| ChatKit frontend setup | Use `<openai-chatkit>` custom element |
| ChatKit server pattern | Extend `ChatKitServer` with custom `respond` |
| Docusaurus integration | Swizzle `Root` component |
| Text selection detection | Use `window.getSelection()` API |
| Mode separation | Conditional agent configuration based on request |

## Dependencies to Install

### Python (project root)
```bash
uv add fastapi uvicorn openai qdrant-client openai-agents asyncpg python-dotenv
uv add chatkit  # if available, otherwise implement protocol manually
```

### JavaScript (ai-textbook/)
```bash
npm install @openai/chatkit
```
