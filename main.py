"""FastAPI application for RAG Chatbot.

Provides the /chatkit endpoint for ChatKit.js integration with streaming responses.
Supports two modes: Full-book RAG and Selected-text.
"""

import json
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_api
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents.run import RunResultStreaming

from config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
    MAX_SELECTED_TEXT_LENGTH,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
)
from rag_tools import search_book, close_clients
import db


# Use chat_completions API for non-OpenAI providers
set_default_openai_api("chat_completions")

# Groq client (OpenAI-compatible)
groq_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)

# Groq model wrapper
groq_model = OpenAIChatCompletionsModel(
    model=GROQ_MODEL,
    openai_client=groq_client,
)


def create_selection_agent(selected_text: str) -> Agent:
    """Create an agent for selected-text mode (no tools)."""
    return Agent(
        name="Selection Assistant",
        instructions=f"""You are a helpful assistant that answers questions based ONLY on the following selected text.

SELECTED TEXT:
---
{selected_text}
---

Guidelines:
1. Answer questions based ONLY on the selected text above.
2. Do NOT use any external knowledge or make assumptions.
3. If the answer is not in the selected text, say "I can only answer based on the selected text, and it doesn't contain information about that."
4. Be helpful and accurate within the constraints of the selected text.""",
        model=groq_model,
        tools=[],  # NO tools in selected-text mode
    )


async def stream_agent_response(result: RunResultStreaming) -> AsyncIterator[str]:
    """Stream SSE events from agent response."""
    try:
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                data = event.data
                # Check for text delta
                if hasattr(data, "delta") and data.delta:
                    yield f"event: message\ndata: {json.dumps({'delta': data.delta})}\n\n"
                elif hasattr(data, "type") and data.type == "response.output_text.delta":
                    if hasattr(data, "delta"):
                        yield f"event: message\ndata: {json.dumps({'delta': data.delta})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    yield f"event: done\ndata: {{}}\n\n"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown
    await close_clients()
    await db.close_pool()


app = FastAPI(
    title="RAG Chatbot API",
    description="RAG chatbot for AI Robotics textbook",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Docusaurus frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-native-docusaurus.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def format_history_for_context(history: list, max_messages: int = 6) -> str:
    """Format conversation history into a compact string for context.

    Limits to last max_messages to save tokens.
    Truncates long messages to 150 chars.
    """
    if not history:
        return ""

    # Take only last N messages
    recent = history[-max_messages:]

    lines = []
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # Truncate long messages
        if len(content) > 150:
            content = content[:150] + "..."
        prefix = "Q" if role == "user" else "A"
        lines.append(f"{prefix}: {content}")

    return "\n".join(lines)


def create_rag_agent_with_history(history_context: str) -> Agent:
    """Create RAG agent with conversation history in instructions."""
    history_section = ""
    if history_context:
        history_section = f"""

Recent conversation for context (use this to understand follow-up questions):
{history_context}
"""

    return Agent(
        name="Book Assistant",
        instructions=f"""You are a helpful assistant for the AI Robotics textbook.

Your job is to answer questions about robotics, AI, ROS2, simulation, and related topics
based on the content in the textbook.
{history_section}
Guidelines:
1. ALWAYS use the search_book tool first to find relevant content before answering.
2. Base your answers ONLY on the content retrieved from the book.
3. If the search results don't contain relevant information, say so honestly.
4. Cite your sources by mentioning which chapter/document the information comes from.
5. Be helpful, clear, and accurate in your responses.
6. If asked about something not covered in the book, explain that it's not in the textbook.
7. For follow-up questions, use the conversation context above to understand what the user is referring to.""",
        model=groq_model,
        tools=[search_book],
    )


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """
    ChatKit protocol endpoint.

    Handles both RAG mode (no selected_text) and selected-text mode.
    Returns SSE streaming response.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON in request body", "code": "INVALID_REQUEST"},
        )

    # Extract message content
    message = body.get("message", {})
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = str(message)

    if not content:
        return JSONResponse(
            status_code=400,
            content={"error": "Message content is required", "code": "INVALID_REQUEST"},
        )

    # Check for selected text in context
    context = body.get("context", {})
    selected_text = context.get("selected_text") if isinstance(context, dict) else None

    # Get conversation history (for context window)
    history = body.get("history", [])
    history_context = format_history_for_context(history)

    # Validate selected text length
    if selected_text and len(selected_text) > MAX_SELECTED_TEXT_LENGTH:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Selected text exceeds maximum length of {MAX_SELECTED_TEXT_LENGTH} characters",
                "code": "SELECTED_TEXT_TOO_LONG",
            },
        )

    # Choose agent based on mode
    if selected_text:
        # Selected-text mode: no retrieval, answer from selection only
        agent = create_selection_agent(selected_text)
    else:
        # Full-book RAG mode: create agent with history context in instructions
        agent = create_rag_agent_with_history(history_context)

    # Run agent with streaming (send only current question as input)
    result = Runner.run_streamed(
        agent,
        input=content,
    )

    return StreamingResponse(
        stream_agent_response(result),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Verifies connectivity to all external services.
    """
    from qdrant_client import AsyncQdrantClient

    services = {
        "database": "unknown",
        "qdrant": "unknown",
        "groq": "available",  # Assume available if configured
        "cohere": "available",  # Assume available if configured
    }

    # Check PostgreSQL
    try:
        if await db.check_connection():
            services["database"] = "connected"
        else:
            services["database"] = "disconnected"
    except Exception:
        services["database"] = "disconnected"

    # Check Qdrant
    try:
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        await client.get_collection(QDRANT_COLLECTION)
        await client.close()
        services["qdrant"] = "connected"
    except Exception:
        services["qdrant"] = "disconnected"

    # Determine overall status
    all_connected = all(
        v in ("connected", "available") for v in services.values()
    )

    return JSONResponse(
        status_code=200 if all_connected else 503,
        content={
            "status": "healthy" if all_connected else "unhealthy",
            "services": services,
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/chatkit": "POST - Chat endpoint (SSE streaming)",
            "/health": "GET - Health check",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
