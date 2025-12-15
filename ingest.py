"""Book content ingestion script for RAG Chatbot.

Discovers all .md and .mdx files from ai-textbook/docs/, chunks them,
generates embeddings via Cohere, and stores in Qdrant + PostgreSQL.
"""

import asyncio
import hashlib
import re
import uuid
from pathlib import Path
from typing import AsyncIterator

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from config import (
    BOOK_DOCS_PATH,
    CHUNK_SIZE_TARGET,
    CHUNK_OVERLAP,
    MAX_CHUNK_SIZE,
    MIN_CHUNK_SIZE,
    COHERE_API_KEY,
    COHERE_BASE_URL,
    COHERE_EMBED_MODEL,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
)
import db


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_title(content: str, filepath: Path) -> str:
    """Extract title from first H1 heading or use filename."""
    # Look for first H1 heading
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Fallback to filename without extension
    return filepath.stem.replace("-", " ").replace("_", " ").title()


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return len(text) // 4


def chunk_document(content: str) -> list[dict]:
    """
    Chunk document into segments suitable for embedding.

    Returns list of dicts with: content, chunk_index, start_char, end_char, token_count
    """
    chunks = []

    # Split by double newlines (paragraphs) first
    paragraphs = re.split(r"\n\n+", content)

    current_chunk = ""
    current_start = 0
    chunk_index = 0
    char_pos = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            char_pos += 2  # Account for newlines
            continue

        para_tokens = estimate_tokens(para)
        current_tokens = estimate_tokens(current_chunk)

        # If adding this paragraph exceeds max, save current chunk
        if current_chunk and (current_tokens + para_tokens > MAX_CHUNK_SIZE):
            if current_tokens >= MIN_CHUNK_SIZE:
                chunks.append({
                    "content": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "start_char": current_start,
                    "end_char": char_pos,
                    "token_count": current_tokens,
                })
                chunk_index += 1

                # Start new chunk with overlap
                overlap_text = current_chunk[-CHUNK_OVERLAP * 4:] if len(current_chunk) > CHUNK_OVERLAP * 4 else ""
                current_chunk = overlap_text + "\n\n" + para
                current_start = char_pos - len(overlap_text)
            else:
                current_chunk += "\n\n" + para
        else:
            if not current_chunk:
                current_start = char_pos
            current_chunk += ("\n\n" if current_chunk else "") + para

        char_pos += len(para) + 2  # paragraph + newlines

    # Save final chunk
    if current_chunk.strip():
        final_tokens = estimate_tokens(current_chunk)
        if final_tokens >= MIN_CHUNK_SIZE or chunk_index == 0:
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "start_char": current_start,
                "end_char": char_pos,
                "token_count": final_tokens,
            })

    return chunks


async def discover_documents() -> AsyncIterator[Path]:
    """Discover all .md and .mdx files in the book docs directory."""
    docs_path = Path(BOOK_DOCS_PATH)
    if not docs_path.exists():
        print(f"Warning: {BOOK_DOCS_PATH} does not exist")
        return

    for pattern in ["**/*.md", "**/*.mdx"]:
        for filepath in docs_path.glob(pattern):
            yield filepath


async def generate_embeddings(texts: list[str], cohere_client: AsyncOpenAI) -> list[list[float]]:
    """Generate embeddings for a list of texts using Cohere."""
    if not texts:
        return []

    response = await cohere_client.embeddings.create(
        input=texts,
        model=COHERE_EMBED_MODEL,
        encoding_format="float",
    )
    return [item.embedding for item in response.data]


async def ingest_document(
    filepath: Path,
    cohere_client: AsyncOpenAI,
    qdrant_client: AsyncQdrantClient,
) -> tuple[int, bool]:
    """
    Ingest a single document.

    Returns (chunk_count, was_updated).
    """
    # Read file content
    content = filepath.read_text(encoding="utf-8")
    content_hash = compute_content_hash(content)
    relative_path = str(filepath.relative_to(Path(BOOK_DOCS_PATH).parent))

    # Check if document exists and hash matches
    existing_doc = await db.get_document_by_path(relative_path)
    if existing_doc and existing_doc["content_hash"] == content_hash:
        # No changes, skip
        return 0, False

    # Extract title
    title = extract_title(content, filepath)

    # Upsert document record
    doc_id = await db.upsert_document(relative_path, title, content_hash)

    # Delete old chunks if document existed
    if existing_doc:
        await db.delete_chunks_for_document(existing_doc["id"])
        # Delete old vectors from Qdrant
        old_chunks = await db.get_chunks_for_document(existing_doc["id"])
        if old_chunks:
            await qdrant_client.delete(
                collection_name=QDRANT_COLLECTION,
                points_selector=[str(c["id"]) for c in old_chunks],
            )

    # Chunk the document
    chunks = chunk_document(content)

    if not chunks:
        return 0, True

    # Generate embeddings for all chunks
    chunk_texts = [c["content"] for c in chunks]
    embeddings = await generate_embeddings(chunk_texts, cohere_client)

    # Store chunks and embeddings
    points = []
    for chunk, embedding in zip(chunks, embeddings):
        # Insert chunk into PostgreSQL
        chunk_id = await db.insert_chunk(
            document_id=doc_id,
            content=chunk["content"],
            chunk_index=chunk["chunk_index"],
            start_char=chunk["start_char"],
            end_char=chunk["end_char"],
            token_count=chunk["token_count"],
        )

        # Prepare Qdrant point
        points.append(
            PointStruct(
                id=str(chunk_id),
                vector=embedding,
                payload={
                    "document_id": str(doc_id),
                    "document_path": relative_path,
                    "document_title": title,
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                },
            )
        )

    # Upsert to Qdrant
    if points:
        await qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points,
        )

    return len(chunks), True


async def main():
    """Main ingestion entry point."""
    print(f"Discovering documents in {BOOK_DOCS_PATH}...")

    # Initialize clients
    cohere_client = AsyncOpenAI(
        base_url=COHERE_BASE_URL,
        api_key=COHERE_API_KEY,
    )
    qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Track stats
    total_docs = 0
    updated_docs = 0
    total_chunks = 0

    # Process documents
    async for filepath in discover_documents():
        total_docs += 1
        print(f"Processing: {filepath}")

        try:
            chunk_count, was_updated = await ingest_document(
                filepath, cohere_client, qdrant_client
            )

            if was_updated:
                updated_docs += 1
                total_chunks += chunk_count
                print(f"  Created {chunk_count} chunks")
            else:
                print(f"  Skipped (unchanged)")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Cleanup
    await qdrant_client.close()
    await db.close_pool()

    # Summary
    print(f"\n{'='*50}")
    print(f"Ingestion complete!")
    print(f"  Documents found: {total_docs}")
    print(f"  Documents updated: {updated_docs}")
    print(f"  Total chunks created: {total_chunks}")


if __name__ == "__main__":
    asyncio.run(main())
