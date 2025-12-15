---
id: 0001
title: RAG Chatbot Feature Specification
stage: spec
date: 2025-12-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-rag-chatbot
branch: 001-rag-chatbot
user: system
command: /sp.specify
labels: ["spec", "rag", "chatbot", "docusaurus", "fastapi", "openai-agents-sdk"]
links:
  spec: specs/001-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-rag-chatbot/spec.md
  - specs/001-rag-chatbot/checklists/requirements.md
  - history/prompts/001-rag-chatbot/0001-rag-chatbot-feature-specification.spec.prompt.md
tests:
  - null
---

## Prompt

Integrated RAG Chatbot Embedded in Existing Docusaurus Book (ai-textbook Folder)

Target audience: Readers of the published AI textbook (technical and non-technical), hackathon judges, and future maintainers of the project

Focus: Build a fully functional, embedded Retrieval-Augmented Generation (RAG) chatbot directly into the existing Docusaurus book located in the "ai-textbook" subfolder. The chatbot must support two strictly separated modes:
  - General questions: Answered using relevant chunks retrieved from the entire book via Qdrant vector search
  - Selected-text questions: Answered exclusively and only from the user-highlighted text on the page (no retrieval from Qdrant allowed)

Success criteria:
- Running `python ingest.py` (from project root) successfully processes all .md/.mdx files in ai-textbook/docs/ and stores embeddings + metadata in Qdrant and Neon
- Local FastAPI server (started via uvicorn) provides a fully working ChatKit endpoint with streaming responses powered by Gemini
- Existing Docusaurus site (run via `npm start` inside ai-textbook/) displays a responsive OpenAI ChatKit.js panel visible on every page (preferably bottom-right)
- General questions return accurate, grounded answers with relevant book context retrieved from Qdrant
- When user highlights any text on a page and asks a question, the chatbot receives the selected text and answers strictly based ONLY on that text (agent must not call the full-book retrieval tool)
- Selected-text workflow is intuitive and reliable (highlight → automatic detection or button → ask)
- Entire end-to-end system runs smoothly locally with zero runtime errors
- All code follows Context 7 best practices for every technology used

Constraints:
- Project root = current folder containing the existing "ai-textbook" subfolder
- Never create a new Docusaurus site, never duplicate or move the ai-textbook folder
- Backend initialization must begin with `uv init`, followed by creation of a standard FastAPI application following Context 7 guidelines
- All new Python files must be placed directly in the project root
- Generation: Exclusively Google Gemini via official OpenAI-compatible endpoint
- Embeddings: Exclusively Cohere via OpenAI Compatibility API
- Vector storage: Qdrant Cloud Free Tier only
- Metadata storage: Neon Serverless Postgres only
- Agent logic: OpenAI Agents SDK only, with proper @function_tool decorators
- Frontend UI: Exclusively OpenAI ChatKit.js (CDN module import)
- Docusaurus modifications: Minimal and reversible only
- Local development only

Not building:
- Separate standalone chat application or external page
- Custom chat UI (must use ChatKit.js only)
- User authentication or persistent chat history
- Multimodal inputs beyond plain text
- Analytics, logging, or monitoring of queries
- Any deviation from the specified tech stack or Context 7 guidelines
- Use of native Cohere/Gemini SDKs (must use OpenAI-compatible clients only)

## Response snapshot

Created comprehensive feature specification at `specs/001-rag-chatbot/spec.md` with:

**User Stories (4 total):**
1. P1: Ask General Questions About the Book - Core RAG functionality with vector search
2. P1: Ask Questions About Highlighted Text - Selected-text mode without retrieval
3. P2: Access Chatbot From Any Page - Consistent UI across all documentation pages
4. P2: Ingest Book Content - One-time developer setup for indexing

**Functional Requirements (17 total):**
- FR-001 to FR-004: Ingestion requirements (auto-discovery, chunking, embedding, metadata)
- FR-005 to FR-008: Chat interface requirements (panel, positioning, input, streaming)
- FR-009 to FR-011: Full-book RAG mode requirements (retrieval, similarity search, grounding)
- FR-012 to FR-015: Selected-text mode requirements (detection, mechanism, exclusivity, no retrieval)
- FR-016 to FR-017: Mode separation requirements (strict separation, mode indication)

**Success Criteria (8 total):**
- SC-001: Response within 10 seconds
- SC-002: Selected-text workflow within 3 clicks
- SC-003: 100% page coverage for chat panel
- SC-004: Error-free ingestion
- SC-005: 90% accuracy for book questions
- SC-006: 100% exclusivity for selected-text answers
- SC-007: 10 concurrent user support
- SC-008: Streaming begins within 2 seconds

**Quality Validation:**
- Created requirements checklist at `specs/001-rag-chatbot/checklists/requirements.md`
- All 16 validation items passed
- Zero [NEEDS CLARIFICATION] markers needed

## Outcome

- ✅ Impact: High - Complete specification ready for architecture planning
- 🧪 Tests: N/A - Specification document, no code tests
- 📁 Files: Created spec.md, checklists/requirements.md
- 🔁 Next prompts: /sp.plan to design architecture, /sp.tasks to generate implementation tasks
- 🧠 Reflection: User provided exceptionally detailed requirements eliminating need for clarification questions

## Evaluation notes (flywheel)

- Failure modes observed: None - user input was comprehensive
- Graders run and results (PASS/FAIL): Quality checklist - 16/16 PASS
- Prompt variant (if applicable): Standard specification creation
- Next experiment (smallest change to try): Validate spec completeness during /sp.plan
