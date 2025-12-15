"""Database connection and query helpers for RAG Chatbot."""

import asyncpg
from typing import Optional
from contextlib import asynccontextmanager

from config import NEON_DB_URL

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            NEON_DB_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
        )
    return _pool


async def close_pool():
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    """Get a database connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def execute(query: str, *args) -> str:
    """Execute a query and return the status."""
    async with get_connection() as conn:
        return await conn.execute(query, *args)


async def fetch(query: str, *args) -> list:
    """Execute a query and fetch all results."""
    async with get_connection() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args) -> Optional[asyncpg.Record]:
    """Execute a query and fetch one result."""
    async with get_connection() as conn:
        return await conn.fetchrow(query, *args)


async def fetchval(query: str, *args):
    """Execute a query and fetch a single value."""
    async with get_connection() as conn:
        return await conn.fetchval(query, *args)


# Document operations
async def upsert_document(path: str, title: str, content_hash: str) -> str:
    """Insert or update a document, returning its ID."""
    query = """
        INSERT INTO documents (path, title, content_hash)
        VALUES ($1, $2, $3)
        ON CONFLICT (path) DO UPDATE SET
            title = EXCLUDED.title,
            content_hash = EXCLUDED.content_hash,
            updated_at = NOW()
        RETURNING id
    """
    return await fetchval(query, path, title, content_hash)


async def get_document_by_path(path: str) -> Optional[asyncpg.Record]:
    """Get a document by its path."""
    query = "SELECT * FROM documents WHERE path = $1"
    return await fetchrow(query, path)


async def delete_chunks_for_document(document_id: str):
    """Delete all chunks for a document."""
    query = "DELETE FROM chunks WHERE document_id = $1"
    await execute(query, document_id)


async def insert_chunk(
    document_id: str,
    content: str,
    chunk_index: int,
    start_char: int,
    end_char: int,
    token_count: int,
) -> str:
    """Insert a chunk and return its ID."""
    query = """
        INSERT INTO chunks (document_id, content, chunk_index, start_char, end_char, token_count)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """
    return await fetchval(
        query, document_id, content, chunk_index, start_char, end_char, token_count
    )


async def get_chunks_for_document(document_id: str) -> list:
    """Get all chunks for a document."""
    query = "SELECT * FROM chunks WHERE document_id = $1 ORDER BY chunk_index"
    return await fetch(query, document_id)


async def check_connection() -> bool:
    """Check if the database connection is working."""
    try:
        result = await fetchval("SELECT 1")
        return result == 1
    except Exception:
        return False
