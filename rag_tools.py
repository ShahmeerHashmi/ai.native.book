"""RAG agent tools for the chatbot.

Provides the search_book tool for retrieving relevant content from the vector database.
"""

from agents import function_tool
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from config import (
    COHERE_API_KEY,
    COHERE_BASE_URL,
    COHERE_EMBED_MODEL,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    TOP_K_RESULTS,
)


# Lazy-initialized clients
_cohere_client: AsyncOpenAI | None = None
_qdrant_client: AsyncQdrantClient | None = None


def get_cohere_client() -> AsyncOpenAI:
    """Get or create the Cohere client."""
    global _cohere_client
    if _cohere_client is None:
        _cohere_client = AsyncOpenAI(
            base_url=COHERE_BASE_URL,
            api_key=COHERE_API_KEY,
        )
    return _cohere_client


def get_qdrant_client() -> AsyncQdrantClient:
    """Get or create the Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
    return _qdrant_client


async def embed_query(query: str) -> list[float]:
    """Generate embedding for a query using Cohere."""
    client = get_cohere_client()
    response = await client.embeddings.create(
        input=[query],
        model=COHERE_EMBED_MODEL,
        encoding_format="float",
    )
    return response.data[0].embedding


async def search_qdrant(query_vector: list[float], top_k: int = TOP_K_RESULTS) -> list[dict]:
    """Search Qdrant for similar chunks."""
    client = get_qdrant_client()
    results = await client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
    )
    return [
        {
            "content": point.payload.get("content", ""),
            "document_path": point.payload.get("document_path", ""),
            "document_title": point.payload.get("document_title", ""),
            "chunk_index": point.payload.get("chunk_index", 0),
            "score": point.score,
        }
        for point in results.points
    ]


@function_tool
async def search_book(query: str) -> str:
    """
    Search the AI Robotics textbook for relevant content.

    Use this tool to find information from the book that can help answer the user's question.
    The tool searches across all chapters and returns the most relevant passages.

    Args:
        query: The search query to find relevant content in the book.

    Returns:
        A formatted string with the most relevant passages from the book,
        including source information for citations.
    """
    try:
        # Generate embedding for the query
        query_vector = await embed_query(query)

        # Search for similar chunks
        results = await search_qdrant(query_vector)

        if not results:
            return "No relevant content found in the book for this query."

        # Format results for the agent
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"[Source {i}: {result['document_title']} ({result['document_path']})]\n"
                f"{result['content']}\n"
            )

        return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"Error searching the book: {str(e)}. Please try again."


async def close_clients():
    """Close all clients gracefully."""
    global _cohere_client, _qdrant_client
    if _qdrant_client is not None:
        await _qdrant_client.close()
        _qdrant_client = None
    _cohere_client = None
