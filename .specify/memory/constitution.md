# Integrated RAG Chatbot Constitution
<!-- RAG Chatbot Embedded in Existing Docusaurus Book (ai-textbook) -->

## Core Principles

### I. Absolute Respect for Existing Project Structure
The Docusaurus book already exists inside the current folder named "ai-textbook" — never create another Docusaurus site, never duplicate folders, never suggest moving or renaming the existing book. The existing structure is sacred and must be preserved.

**Invariants:**
- Project root = current folder containing the existing "ai-textbook" subfolder
- ai-textbook/ holds the full Docusaurus site with docs/, src/, docusaurus.config.js, etc.
- All new Python files (ingest.py, rag_tools.py, main.py, etc.) must be placed in the project root (same level as "ai-textbook" folder)

### II. Correct Technical Initialization
Before writing any code involving FastAPI, always first run `uv init` in the project root if not already done, then initialize a standard FastAPI application.

**Initialization Sequence:**
1. First command: `uv init` (only if pyproject.toml doesn't exist)
2. Add dependencies via `uv add <package>`
3. Create standard FastAPI application following Context7 best practices

### III. Context7 Compliance (NON-NEGOTIABLE)
Whenever using or explaining any technology (FastAPI, OpenAI Agents SDK, Qdrant, Cohere, Gemini, ChatKit, Docusaurus plugins, etc.), always reference and follow the official Context7 guidelines/standard practices for that technology.

**Required Context7 Lookups:**
- FastAPI application structure and patterns
- OpenAI Agents SDK tool calling conventions
- Qdrant vector database operations
- Cohere embedding API usage
- Google Gemini API integration
- ChatKit.js frontend integration
- Docusaurus component swizzling and plugins

### IV. Zero Hallucination on Book Content
All RAG answers must come only from the book's actual text stored in the vector database. The system must never fabricate, infer, or hallucinate content that doesn't exist in the source documents.

**Content Source:**
- Book content: Automatically discover and read all .md and .mdx files from ai-textbook/docs/

### V. Strict Mode Separation
Full-book RAG mode vs. selected-text-only mode must never cross-contaminate.

**Mode Definitions:**
- **Full-book RAG mode**: Query the vector database for relevant chunks across the entire book
- **Selected-text mode**: Answer strictly from user-highlighted text only (no retrieval tool used)

### VI. Minimal, Reversible Modifications
Changes to the existing Docusaurus site must be clean and easy to undo.

**Allowed Modifications:**
- Swizzling components in ai-textbook/src/theme/
- Custom plugin in ai-textbook/plugins/
- Config injection in docusaurus.config.js
- All changes must be Context7 compliant

## Technology Stack

### Backend
| Component | Technology | Notes |
|-----------|------------|-------|
| Package Manager | uv | Must run `uv init` first |
| Web Framework | FastAPI | Standard app structure |
| Agent Framework | OpenAI Agents SDK | With proper tool calling |
| Chat Server | OpenAI ChatKit server | Enhanced FastAPI endpoints |

### AI Services
| Component | Technology | Configuration |
|-----------|------------|---------------|
| Embeddings | Cohere | base_url="https://api.cohere.ai/compatibility/v1", model="embed-english-v3.0" or latest |
| Generation | Google Gemini | OpenAI-compatible endpoint only |
| Vector Store | Qdrant Cloud | Free Tier |
| Metadata Store | Neon Serverless | PostgreSQL |

### Frontend
| Component | Technology | Notes |
|-----------|------------|-------|
| Chat UI | OpenAI ChatKit.js | Exclusively - no alternatives |
| Documentation | Docusaurus | Existing site in ai-textbook/ |

## Constraints

### Forbidden Actions
- Never create a new Docusaurus site
- Never create additional nested book folders
- Never place Python files inside ai-textbook/
- Never use embedding providers other than Cohere
- Never use LLM providers other than Gemini for generation
- Never use chat UI libraries other than ChatKit.js

### Required Patterns
- Use exact provided credentials via .env in root
- Local development only — Docusaurus with `npm start` inside ai-textbook/
- Backend with `uvicorn` from project root
- All API keys and secrets in .env file (never hardcoded)

## Project Structure

```
project-root/                    # Current working directory
├── .specify/                    # SpecKit Plus templates and scripts
│   └── memory/
│       └── constitution.md     # This file
├── ai-textbook/                 # EXISTING Docusaurus site (DO NOT RECREATE)
│   ├── docs/                    # Source content (.md, .mdx files)
│   ├── src/                     # React components
│   ├── plugins/                 # Custom plugins (if needed)
│   ├── docusaurus.config.js    # Site configuration
│   └── ...
├── specs/                       # Feature specifications
├── history/                     # PHR and ADR records
│   ├── prompts/
│   └── adr/
├── .env                         # Environment variables (credentials)
├── pyproject.toml              # Python project config (after uv init)
├── ingest.py                   # Book ingestion script
├── rag_tools.py                # RAG agent tools
└── main.py                     # FastAPI application
```

## Success Criteria

### Initialization
- [ ] `uv init` successfully run in project root
- [ ] Standard FastAPI app created following Context7 patterns

### Ingestion
- [ ] `python ingest.py` discovers all .md/.mdx files from ai-textbook/docs/
- [ ] All content embedded via Cohere into Qdrant
- [ ] Metadata stored in Neon PostgreSQL

### Backend
- [ ] FastAPI server provides working ChatKit endpoint
- [ ] Streaming Gemini responses functional
- [ ] OpenAI Agents SDK tool calling operational

### Frontend
- [ ] Docusaurus site (`npm start` in ai-textbook/) runs without errors
- [ ] ChatKit panel displays on every page
- [ ] Panel integrates cleanly with existing site design

### RAG Functionality
- [ ] General questions → accurate full-book RAG answers
- [ ] Highlighted text questions → answers based exclusively on selected text
- [ ] No cross-contamination between modes
- [ ] Zero hallucination (all answers from actual book content)

### End-to-End
- [ ] Entire system runs locally without errors
- [ ] All code follows Context7 best practices for each technology

## Governance

This constitution supersedes all other practices for this project. Any amendments require:
1. Documentation of the change rationale
2. Impact assessment on existing implementation
3. Update to this constitution file
4. PHR record of the amendment

**Version**: 1.0.0 | **Ratified**: 2025-12-15 | **Last Amended**: 2025-12-15
