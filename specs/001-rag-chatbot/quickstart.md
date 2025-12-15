# Quickstart: Integrated RAG Chatbot

**Feature Branch**: `001-rag-chatbot`

## Prerequisites

- Python 3.11+ with `uv` package manager
- Node.js 18+ with npm
- Git

## Setup Steps

### 1. Initialize Python Environment

```bash
# From project root (same level as ai-textbook/)
uv init
uv add fastapi uvicorn openai qdrant-client asyncpg python-dotenv openai-agents
```

### 2. Create Environment File

Create `.env` in project root:

```env
GEMINI_API_KEY=AIzaSyCeLRHFFF3jCJ3Kj44L1FN5TFKa33A-wTY
COHERE_API_KEY=l7crZ3p00qchoiashvHwAnTUodQcAgJxJGLRnsAk
QDRANT_URL=https://deab3260-bee6-4228-89e2-f488cef70ca6.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.0qHJm-dUOPk4hnoaTaj-eYotMv4Mt69ONSB6ZUsm-34
NEON_DB_URL=postgresql://neondb_owner:npg_qs82TExSNPhX@ep-divine-voice-a47vuwe4-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### 3. Ingest Book Content

```bash
# From project root
python ingest.py
```

Expected output:
```
Discovering documents in ai-textbook/docs/...
Found 12 documents
Processing: docs/intro.md
  Created 5 chunks
Processing: docs/ros2.md
  Created 8 chunks
...
Ingestion complete: 12 documents, 87 chunks
```

### 4. Backend Server

The backend is deployed on Vercel at:
```
https://ai-native-book-sand.vercel.app/
```

For local development:
```bash
# From project root
uvicorn main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 5. Install ChatKit in Docusaurus

```bash
# From ai-textbook/
cd ai-textbook
npm install @openai/chatkit
```

### 6. Swizzle Root Component

```bash
# From ai-textbook/
npm run swizzle @docusaurus/theme-classic Root -- --wrap
```

Edit `ai-textbook/src/theme/Root.js` to inject ChatKit.

### 7. Start Docusaurus

```bash
# From ai-textbook/
npm start
```

Open http://localhost:3000 in your browser.

## Verification Checklist

- [ ] Backend health check: `curl https://ai-native-book-sand.vercel.app/health`
- [ ] Chat panel visible on Docusaurus pages
- [ ] General question returns answer with book context
- [ ] Highlighted text + question returns context-specific answer
- [ ] Streaming responses appear progressively

## Project Structure (After Setup)

```
project-root/
├── .env                    # API credentials
├── pyproject.toml          # Python dependencies
├── main.py                 # FastAPI application
├── ingest.py               # Book ingestion script
├── rag_tools.py            # RAG agent tools
├── ai-textbook/            # Existing Docusaurus site
│   ├── src/
│   │   └── theme/
│   │       └── Root.js     # Swizzled component with ChatKit
│   ├── docs/               # Book content (source for RAG)
│   └── package.json        # Now includes @openai/chatkit
└── specs/
    └── 001-rag-chatbot/
        ├── spec.md
        ├── plan.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md
        └── contracts/
```

## Common Issues

### "Cannot connect to Qdrant"
- Check `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
- Verify network connectivity to Qdrant Cloud

### "Chat panel not showing"
- Ensure `@openai/chatkit` is installed in ai-textbook
- Verify Root.js swizzle is correct
- Check browser console for JavaScript errors

### "No results returned"
- Run `python ingest.py` to populate vector store
- Verify ingestion completed successfully
- Check Qdrant Cloud dashboard for collection data
