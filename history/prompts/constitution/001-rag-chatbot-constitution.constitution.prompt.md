---
id: 001
title: RAG Chatbot Constitution Creation
stage: constitution
date: 2025-12-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: master
user: system
command: /sp.constitution
labels: ["constitution", "rag", "chatbot", "docusaurus", "fastapi"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - history/prompts/constitution/001-rag-chatbot-constitution.constitution.prompt.md
tests:
  - null
---

## Prompt

Project: Integrated RAG Chatbot Embedded in Existing Docusaurus Book (Fresh Setup in ai-textbook Folder)

Core principles:
- Absolute respect for existing project structure: The Docusaurus book already exists inside the current folder named "ai-textbook" — never create another Docusaurus site, never duplicate folders, never suggest moving or renaming the existing book
- Start every technical step correctly: Before writing any code involving FastAPI, always first run `uv init` in the project root if not already done, then initialize a standard FastAPI application
- Context 7 rule: Whenever using or explaining any technology (FastAPI, OpenAI Agents SDK, Qdrant, Cohere, Gemini, ChatKit, Docusaurus plugins, etc.), always reference and follow the official Context 7 guidelines/standard practices for that technology
- Zero hallucination on book content: All answers must come only from the book's actual text
- Strict mode separation: Full-book RAG vs. selected-text-only mode must never cross-contaminate
- Minimal, reversible modifications: Changes to the existing Docusaurus site must be clean and easy to undo

Key standards:
- Project root = current folder containing the existing "ai-textbook" subfolder (which holds the full Docusaurus site with docs/, src/, docusaurus.config.js, etc.)
- Backend initialization:
  1. First command: `uv init` (only if not already initialized)
  2. Then create a standard FastAPI application following Context 7 best practices
- Book content source: Automatically discover and read all .md and .mdx files from ai-textbook/docs/
- Ingestion: One-time upfront Cohere embeddings (via OpenAI-compatible API) stored in Qdrant Cloud Free Tier
- Metadata storage: Neon Serverless Postgres
- Generation: Google Gemini only (OpenAI-compatible endpoint)
- Embeddings: Cohere only (base_url="https://api.cohere.ai/compatibility/v1", model preferably "embed-english-v3.0" or latest)
- Agent framework: OpenAI Agents SDK with proper tool calling
- Backend: Standard FastAPI app (initialized via uv) enhanced with OpenAI ChatKit server
- Frontend: Exclusively OpenAI ChatKit.js embedded into the existing Docusaurus site
- Selected-text workflow: Browser text highlight → send to chatbot → answer strictly from that text only

Constraints:
- Never create a new Docusaurus site or additional nested book folders
- All new Python files (ingest.py, rag_tools.py, main FastAPI file, etc.) must be placed in the project root (same level as the "ai-textbook" folder)
- Docusaurus modifications limited to: swizzling components, custom plugin in ai-textbook/plugins/, or config injection — always minimal and Context 7 compliant
- Use exact provided credentials (add to .env in root)
- Local development only — run Docusaurus with `npm start` inside ai-textbook/ and FastAPI with `uvicorn`

Success criteria:
- `uv init` successfully run and standard FastAPI app created/initialized
- `python ingest.py` embeds the entire existing book (from ai-textbook/docs/) into Qdrant + Neon
- Local FastAPI server provides fully working ChatKit endpoint with streaming Gemini responses
- Existing Docusaurus site (npm start) displays functional ChatKit panel on every page
- General questions → accurate full-book RAG answers
- Highlighted text questions → answers based exclusively on selected text (no retrieval tool used)
- Entire system runs end-to-end locally without errors
- All code and setup steps strictly follow Context 7 for every technology used

## Response snapshot

Created comprehensive constitution document at `.specify/memory/constitution.md` with:

1. **Six Core Principles:**
   - I. Absolute Respect for Existing Project Structure
   - II. Correct Technical Initialization (uv init → FastAPI)
   - III. Context7 Compliance (NON-NEGOTIABLE)
   - IV. Zero Hallucination on Book Content
   - V. Strict Mode Separation (full-book RAG vs selected-text)
   - VI. Minimal, Reversible Modifications

2. **Technology Stack Tables:**
   - Backend: uv, FastAPI, OpenAI Agents SDK, ChatKit server
   - AI Services: Cohere embeddings, Gemini generation, Qdrant, Neon
   - Frontend: ChatKit.js exclusively, existing Docusaurus site

3. **Constraints:**
   - Forbidden actions (never recreate Docusaurus, never use alternative providers)
   - Required patterns (credentials in .env, local development commands)

4. **Project Structure Diagram:**
   - Clear file placement rules
   - Separation of concerns between root and ai-textbook/

5. **Success Criteria Checklist:**
   - Initialization, Ingestion, Backend, Frontend, RAG Functionality, End-to-End

6. **Governance Rules:**
   - Amendment process and version tracking

## Outcome

- ✅ Impact: High - Established foundational rules for entire RAG chatbot implementation
- 🧪 Tests: N/A - Constitution document, no code tests
- 📁 Files: Created .specify/memory/constitution.md, history/prompts/ directories
- 🔁 Next prompts: /sp.specify for feature spec, then /sp.plan for architecture
- 🧠 Reflection: Constitution captures all user requirements including Context7 mandate and strict technology choices

## Evaluation notes (flywheel)

- Failure modes observed: None - straightforward constitution creation
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Standard constitution creation
- Next experiment (smallest change to try): Validate constitution completeness during /sp.specify
