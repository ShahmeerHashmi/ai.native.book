"""Configuration loading and validation for RAG Chatbot."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_required_env(key: str) -> str:
    """Get a required environment variable or raise an error."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


# Gemini API (generation)
GEMINI_API_KEY = get_required_env("GEMINI_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODEL = "gemini-2.5-flash"  # Latest flash model

# Cohere API (embeddings)
COHERE_API_KEY = get_required_env("COHERE_API_KEY")
COHERE_BASE_URL = "https://api.cohere.ai/compatibility/v1"
COHERE_EMBED_MODEL = "embed-v4.0"
EMBEDDING_DIMENSIONS = 1536  # embed-v4.0 uses 1536 dimensions

# Qdrant Cloud (vector database)
QDRANT_URL = get_required_env("QDRANT_URL")
QDRANT_API_KEY = get_required_env("QDRANT_API_KEY")
QDRANT_COLLECTION = "book_chunks"

# Neon PostgreSQL (metadata database)
NEON_DB_URL = get_required_env("NEON_DB_URL")

# Book content location
BOOK_DOCS_PATH = "ai-textbook/docs"

# Chunking settings
CHUNK_SIZE_TARGET = 750  # Target tokens per chunk
CHUNK_OVERLAP = 100  # Overlap tokens between chunks
MAX_CHUNK_SIZE = 1000  # Maximum tokens per chunk
MIN_CHUNK_SIZE = 100  # Minimum tokens per chunk

# Search settings
TOP_K_RESULTS = 5  # Number of chunks to retrieve

# Validation settings
MAX_SELECTED_TEXT_LENGTH = 10000  # Maximum characters for selected text mode
