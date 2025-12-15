# Tasks: Integrated RAG Chatbot

**Input**: Design documents from `/specs/001-rag-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - spec does not explicitly require TDD, so tests are listed but can be skipped.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions (per plan.md)

- **Python files**: Project root (`main.py`, `ingest.py`, `rag_tools.py`, `db.py`, `config.py`)
- **Frontend**: `ai-textbook/src/theme/Root.js` (swizzled component)
- **Specs**: `specs/001-rag-chatbot/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and environment configuration

- [x] T001 Initialize Python project with `uv init` at project root
- [x] T002 Add Python dependencies with `uv add fastapi uvicorn openai qdrant-client asyncpg python-dotenv openai-agents`
- [x] T003 [P] Create `.env` file with all API credentials (GEMINI_API_KEY, COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY, NEON_DB_URL)
- [x] T004 [P] Create `config.py` for environment variable loading and validation

**Checkpoint**: Python environment ready, credentials configured

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create `db.py` with asyncpg connection pool and query helpers
- [x] T006 Execute DDL schema in Neon PostgreSQL (documents table, chunks table, indexes)
- [x] T007 [P] Create Qdrant collection `book_chunks` (1024 dimensions, Cosine distance)
- [x] T008 [P] Verify database and Qdrant connectivity with test queries

**Checkpoint**: Foundation ready - all external services connected and verified

---

## Phase 3: User Story 4 - Ingest Book Content (Priority: P2) - FOUNDATIONAL

**Goal**: Process all book content and prepare it for RAG queries (required before US1 can work)

**Why P2 but first**: Although marked P2 (developer action), US1 and US2 cannot function without ingested data

**Independent Test**: Run `python ingest.py` and verify embeddings appear in Qdrant and metadata in PostgreSQL

### Implementation for User Story 4

- [x] T009 [US4] Create `ingest.py` with document discovery (glob `ai-textbook/docs/**/*.md` and `**/*.mdx`)
- [x] T010 [US4] Implement content hash computation (SHA-256) for change detection
- [x] T011 [US4] Implement document chunking logic (500-1000 tokens, 100 token overlap)
- [x] T012 [US4] Implement Cohere embedding generation via OpenAI-compatible API
- [x] T013 [US4] Implement Qdrant upsert with payload (document_id, path, title, chunk_index, content)
- [x] T014 [US4] Implement PostgreSQL upsert for documents and chunks tables
- [x] T015 [US4] Add progress reporting and summary output (X documents, Y chunks processed)
- [x] T016 [US4] Run full ingestion on ai-textbook/docs/ and verify data in both stores

**Acceptance Criteria**:
- FR-001: All .md/.mdx files discovered automatically
- FR-002: Documents chunked appropriately
- FR-003: Embeddings stored in Qdrant
- FR-004: Metadata stored in PostgreSQL

**Checkpoint**: Book content ingested - RAG queries can now function

---

## Phase 4: User Story 1 - Ask General Questions About the Book (Priority: P1)

**Goal**: Users can ask questions and receive answers grounded in book content via RAG

**Independent Test**: Start backend, send POST to /chatkit with a question, verify streaming response with relevant book content

### Implementation for User Story 1

- [x] T017 [US1] Create `rag_tools.py` with `@function_tool search_book(query: str)` decorator
- [x] T018 [US1] Implement query embedding via Cohere in search_book tool
- [x] T019 [US1] Implement Qdrant semantic search (top-5 chunks) in search_book tool
- [x] T020 [US1] Create `main.py` with FastAPI app structure and CORS middleware
- [x] T021 [US1] Configure Gemini client via AsyncOpenAI with OpenAI-compatible endpoint
- [x] T022 [US1] Define RAG agent with instructions to use search_book and cite sources
- [x] T023 [US1] Implement `/chatkit` POST endpoint with mode detection logic
- [x] T024 [US1] Implement SSE streaming response using `Runner.run_streamed()` and `StreamingResponse`
- [x] T025 [US1] Implement `/health` GET endpoint with service connectivity checks
- [x] T026 [US1] Test full RAG flow: question → embedding → search → generation → streaming response

**Acceptance Criteria**:
- FR-009: Retrieves relevant chunks from vector database
- FR-010: Uses semantic similarity search
- FR-011: Answers grounded in retrieved content (no hallucination)
- SC-001: Response within 10 seconds
- SC-008: Streaming begins within 2 seconds

**Checkpoint**: Full-book RAG mode operational

---

## Phase 5: User Story 2 - Ask Questions About Highlighted Text (Priority: P1)

**Goal**: Users can ask questions about selected text, answered ONLY from that text (no retrieval)

**Independent Test**: Send POST to /chatkit with `context.selected_text`, verify response uses only that text

### Implementation for User Story 2

- [x] T027 [US2] Create `create_selection_agent(selected_text)` factory function (no tools)
- [x] T028 [US2] Update `/chatkit` endpoint to detect `selected_text` in request context
- [x] T029 [US2] Implement mode branching: if selected_text → selection agent, else → RAG agent
- [x] T030 [US2] Add selected_text length validation (max 10000 chars per contract)
- [x] T031 [US2] Test selected-text mode: question with context → response from only that text

**Acceptance Criteria**:
- FR-012: Detects highlighted text in request
- FR-014: Answers ONLY from selected text
- FR-015: Does NOT call retrieval in selected-text mode
- FR-016: Strict mode separation
- SC-006: 100% of answers derive exclusively from highlighted text

**Checkpoint**: Selected-text mode operational, both modes working correctly

---

## Phase 6: User Story 3 - Access Chatbot From Any Page (Priority: P2)

**Goal**: Chat panel visible on every Docusaurus page, non-intrusive and functional

**Independent Test**: Navigate to 5+ different pages, verify chat panel appears and functions on each

### Implementation for User Story 3

- [x] T032 [US3] Install @openai/chatkit in ai-textbook/ via `npm install @openai/chatkit`
- [x] T033 [US3] Create Docusaurus Root component in `ai-textbook/src/theme/Root.js`
- [x] T034 [US3] Edit `ai-textbook/src/theme/Root.js` to import and render ChatPanel component
- [x] T035 [US3] Configure ChatPanel with backend URL (http://localhost:8000/chatkit)
- [x] T036 [US3] Implement text selection detection with `window.getSelection()` in Root.js
- [x] T037 [US3] Pass selected_text to backend via context in request body
- [x] T038 [US3] Style chat panel for bottom-right positioning (non-intrusive)
- [x] T039 [US3] Test chat visibility across multiple documentation pages
- [x] T040 [US3] Test text selection → chat flow end-to-end

**Acceptance Criteria**:
- FR-005: Chat panel on every page
- FR-006: Bottom-right, non-intrusive
- FR-007: Text input for questions
- FR-008: Streaming responses
- FR-013: Mechanism to ask about selected text
- FR-017: Mode indication to user
- SC-002: Question about selection within 3 interactions
- SC-003: Panel functional on 100% of pages

**Checkpoint**: Full frontend integration complete

---

## Phase 7: Polish & Verification

**Purpose**: Final verification and cleanup

- [x] T041 [P] Verify quickstart.md steps work end-to-end
- [x] T042 [P] Test concurrent requests (verify SC-007: 10 concurrent users)
- [x] T043 [P] Test edge cases: empty vector store, very long selected text, unclear questions
- [x] T044 [P] Verify error handling displays user-friendly messages
- [x] T045 Final integration test: both modes, streaming, multiple pages

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS all user stories)
    ↓
Phase 3: US4 Ingest (BLOCKS US1 - needs data to query)
    ↓
Phase 4: US1 RAG Mode (can proceed)
    ↓
Phase 5: US2 Selected-Text Mode (can run parallel with US1 after T023)
    ↓
Phase 6: US3 Frontend (can run parallel with US1/US2 after T020)
    ↓
Phase 7: Polish
```

### Critical Path

1. T001-T004 (Setup) → T005-T008 (Foundation) → T009-T016 (Ingestion)
2. After ingestion: T017-T026 (RAG backend) can proceed
3. Frontend tasks T032-T040 can start after T020 (main.py exists)
4. US2 tasks T027-T031 can start after T023 (/chatkit endpoint exists)

### Parallel Opportunities

**Within Phase 1**:
- T003 (.env) and T004 (config.py) can run in parallel

**Within Phase 2**:
- T007 (Qdrant collection) and T008 (connectivity test) can run in parallel with T005-T006

**After Phase 3 (Ingestion complete)**:
- US1 (Phase 4) and US3 frontend setup (T032-T033) can proceed in parallel
- US2 (Phase 5) can start once T023 is complete

**Within Phase 7**:
- All polish tasks can run in parallel

---

## Implementation Strategy

### MVP First: US4 → US1

1. Complete Setup + Foundational
2. Complete US4 (Ingest) - data must exist
3. Complete US1 (RAG Mode) - core value proposition
4. **STOP and VALIDATE**: Test RAG queries work via curl/API client
5. Can demo backend-only at this point

### Add Selected-Text Mode: US2

6. Complete US2 (Selected-Text Mode)
7. **VALIDATE**: Both modes work correctly via API

### Add Frontend: US3

8. Complete US3 (Frontend Integration)
9. **VALIDATE**: Full end-to-end flow in browser

### Final Polish

10. Complete Phase 7 verification
11. Run full quickstart.md validation

---

## Notes

- All Python files at project root (per constitution)
- Only swizzle Root component in ai-textbook/ (minimal modification)
- Use Context7 patterns from research.md for all implementations
- Streaming is critical for UX - verify early
- Mode separation is absolute - verify no tool calls in selected-text mode
