# Data Model: Integrated RAG Chatbot

**Feature Branch**: `001-rag-chatbot`
**Date**: 2025-12-15

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Document     │       │     Chunk       │       │   Embedding     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──1:N──│ id (PK)         │──1:1──│ chunk_id (PK/FK)│
│ path            │       │ document_id (FK)│       │ vector [1024]   │
│ title           │       │ content         │       │ created_at      │
│ content_hash    │       │ chunk_index     │       └─────────────────┘
│ created_at      │       │ start_char      │              │
│ updated_at      │       │ end_char        │              │
└─────────────────┘       │ token_count     │              │
                          │ created_at      │              │
                          └─────────────────┘              │
                                                           │
                                                    [Qdrant Cloud]
                                                    Vector Store
```

## Entities

### 1. Document (Neon PostgreSQL)

Represents a single .md/.mdx file from the book.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique document identifier |
| `path` | VARCHAR(500) | NOT NULL, UNIQUE | Relative path from ai-textbook/docs/ |
| `title` | VARCHAR(255) | NOT NULL | Extracted from first H1 or filename |
| `content_hash` | VARCHAR(64) | NOT NULL | SHA-256 hash for change detection |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | First ingestion timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last ingestion timestamp |

**Indexes**:
- PRIMARY KEY (`id`)
- UNIQUE INDEX on `path`
- INDEX on `content_hash` (for change detection)

---

### 2. Chunk (Neon PostgreSQL)

A segment of a document suitable for embedding.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique chunk identifier |
| `document_id` | UUID | FK → Document.id, NOT NULL | Parent document reference |
| `content` | TEXT | NOT NULL | Chunk text content |
| `chunk_index` | INTEGER | NOT NULL | Position in document (0-indexed) |
| `start_char` | INTEGER | NOT NULL | Start character position in source |
| `end_char` | INTEGER | NOT NULL | End character position in source |
| `token_count` | INTEGER | NOT NULL | Approximate token count |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Indexes**:
- PRIMARY KEY (`id`)
- INDEX on `document_id`
- UNIQUE INDEX on (`document_id`, `chunk_index`)

**Constraints**:
- ON DELETE CASCADE from Document

---

### 3. Embedding (Qdrant Cloud)

Vector representation of a chunk stored in Qdrant.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Same as Chunk.id (point ID in Qdrant) |
| `vector` | FLOAT[1024] | Cohere embedding vector |
| `payload.document_id` | STRING | Parent document UUID |
| `payload.document_path` | STRING | Source file path |
| `payload.document_title` | STRING | Document title |
| `payload.chunk_index` | INTEGER | Chunk position |
| `payload.content` | STRING | Chunk text (for retrieval display) |

**Collection Config**:
```json
{
  "collection_name": "book_chunks",
  "vectors_config": {
    "size": 1024,
    "distance": "Cosine"
  }
}
```

---

## Validation Rules

### Document
- `path` must be relative to ai-textbook/docs/
- `path` must end with `.md` or `.mdx`
- `title` extracted from first `# ` heading or filename without extension
- `content_hash` computed on raw file content

### Chunk
- `content` length: 500-1000 tokens (target)
- `chunk_index` starts at 0
- Chunks should overlap by ~100 tokens with adjacent chunks
- `token_count` estimated using cl100k_base tokenizer

### Embedding
- Vector dimension must be exactly 1024
- `id` must match corresponding Chunk.id
- All payload fields are required

---

## State Transitions

### Document Lifecycle

```
[File Discovered] → [Document Created] → [Chunks Generated] → [Embeddings Stored]
                           │                                          │
                           │ (file changed)                           │
                           ▼                                          │
                    [Hash Mismatch] → [Chunks Deleted] → [Re-chunk] ──┘
                           │
                           │ (file deleted)
                           ▼
                    [Document Deleted] → [Chunks Cascade Delete] → [Embeddings Deleted]
```

### Ingestion State Machine

```
IDLE → DISCOVERING → PROCESSING → EMBEDDING → STORING → COMPLETE
  ↑                      │
  └──────────────────────┘ (error → retry)
```

---

## Sample Data

### Document
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "path": "architecture/ros2.md",
  "title": "ROS2 Architecture",
  "content_hash": "a1b2c3d4e5f6...",
  "created_at": "2025-12-15T10:00:00Z",
  "updated_at": "2025-12-15T10:00:00Z"
}
```

### Chunk
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "ROS2 (Robot Operating System 2) is a flexible framework for writing robot software...",
  "chunk_index": 0,
  "start_char": 0,
  "end_char": 512,
  "token_count": 128,
  "created_at": "2025-12-15T10:00:00Z"
}
```

### Qdrant Point
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "vector": [0.012, -0.034, 0.056, ...],
  "payload": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "document_path": "architecture/ros2.md",
    "document_title": "ROS2 Architecture",
    "chunk_index": 0,
    "content": "ROS2 (Robot Operating System 2) is a flexible framework..."
  }
}
```

---

## Database Schema (PostgreSQL DDL)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    path VARCHAR(500) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_content_hash ON documents(content_hash);

-- Chunks table
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
```
