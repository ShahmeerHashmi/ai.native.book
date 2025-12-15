# Feature Specification: Integrated RAG Chatbot

**Feature Branch**: `001-rag-chatbot`
**Created**: 2025-12-15
**Status**: Draft
**Input**: User description: "Integrated RAG Chatbot Embedded in Existing Docusaurus Book (ai-textbook Folder)"

## Overview

Build a fully functional, embedded Retrieval-Augmented Generation (RAG) chatbot directly into the existing Docusaurus book located in the "ai-textbook" subfolder. The chatbot supports two strictly separated answer modes:
- **General questions**: Answered using relevant chunks retrieved from the entire book via vector search
- **Selected-text questions**: Answered exclusively from user-highlighted text on the page (no retrieval)

**Target Audience**: Readers of the AI textbook (technical and non-technical), hackathon judges, and future maintainers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask General Questions About the Book (Priority: P1)

A reader navigating the AI textbook wants to ask questions about concepts covered anywhere in the book without manually searching through chapters. They open the chat panel, type their question, and receive an accurate answer grounded in the book's actual content.

**Why this priority**: This is the core RAG functionality - the primary value proposition of having an intelligent assistant embedded in the documentation.

**Independent Test**: Can be fully tested by typing a question in the chat panel and verifying the response contains accurate information from the book with relevant context.

**Acceptance Scenarios**:

1. **Given** the chatbot is visible on any page, **When** user types "What is ROS2?" and submits, **Then** the chatbot returns an answer citing content from the book's ROS2 section
2. **Given** the user asks a question about a topic covered in the book, **When** the response is generated, **Then** the answer streams progressively and completes within reasonable time
3. **Given** the user asks about a topic NOT in the book, **When** the response is generated, **Then** the chatbot indicates it cannot find relevant information rather than hallucinating

---

### User Story 2 - Ask Questions About Highlighted Text (Priority: P1)

A reader highlights a specific passage on the current page and wants to ask a question specifically about that selected text. The chatbot answers based ONLY on the highlighted content, without searching the broader book.

**Why this priority**: This is the second core mode - equally critical as it enables focused, context-specific learning that differentiates this from a simple search.

**Independent Test**: Can be tested by highlighting text on a page, clicking the "Ask about selection" button, asking a question, and verifying the answer is strictly derived from the selected text.

**Acceptance Scenarios**:

1. **Given** user highlights text "Gazebo is a robotics simulator", **When** user asks "What is this used for?", **Then** the chatbot answers based only on the highlighted text
2. **Given** user has highlighted text and asks a question, **When** the response is generated, **Then** the system does NOT retrieve additional chunks from the vector database
3. **Given** user highlights a short phrase, **When** user asks an unrelated question, **Then** the chatbot explains it can only answer based on the selected text

---

### User Story 3 - Access Chatbot From Any Page (Priority: P2)

A reader browsing any page of the Docusaurus book sees a consistent, non-intrusive chat panel (bottom-right corner) that can be opened, used, and minimized without disrupting their reading experience.

**Why this priority**: Accessibility and UX are essential for adoption, but the core functionality must work first.

**Independent Test**: Navigate to 5 different pages and verify the chat panel appears consistently and functions correctly on each.

**Acceptance Scenarios**:

1. **Given** user navigates to any documentation page, **When** the page loads, **Then** the chat panel is visible in the bottom-right corner
2. **Given** the chat panel is open, **When** user navigates to another page, **Then** the chat panel remains accessible
3. **Given** user is reading content, **When** chat panel is minimized, **Then** it does not obstruct page content

---

### User Story 4 - Ingest Book Content (Priority: P2)

A developer or maintainer runs a single command to process all book content and prepare it for RAG queries. This is a one-time setup step that indexes all documentation.

**Why this priority**: Required for the system to function, but is a one-time developer action rather than ongoing user interaction.

**Independent Test**: Run the ingestion command and verify embeddings are stored and retrievable.

**Acceptance Scenarios**:

1. **Given** the book exists in ai-textbook/docs/, **When** running `python ingest.py`, **Then** all .md and .mdx files are discovered and processed
2. **Given** ingestion completes, **When** checking the vector store, **Then** embeddings exist for each document chunk
3. **Given** ingestion completes, **When** checking the metadata store, **Then** document metadata (title, path, chunk info) is recorded

---

### Edge Cases

- What happens when user highlights text and then clears selection before asking?
  - System should detect no selection and default to full-book RAG mode
- What happens when the vector database is empty or unreachable?
  - System should display a user-friendly error message
- What happens when user asks in a language different from the book content?
  - System should attempt to answer but may indicate reduced accuracy
- What happens when highlighted text is extremely long (>5000 chars)?
  - System should truncate with notification or handle gracefully
- What happens when the streaming response is interrupted?
  - Partial response should be displayed, user can retry

## Requirements *(mandatory)*

### Functional Requirements

**Ingestion**
- **FR-001**: System MUST automatically discover all .md and .mdx files from ai-textbook/docs/ without hardcoded paths
- **FR-002**: System MUST chunk documents appropriately for embedding (reasonable chunk size with overlap)
- **FR-003**: System MUST generate embeddings for each chunk and store them in the vector database
- **FR-004**: System MUST store document metadata (source file path, title, chunk position) in the relational database

**Chat Interface**
- **FR-005**: System MUST display a chat panel on every page of the Docusaurus site
- **FR-006**: Chat panel MUST be positioned in the bottom-right corner and be non-intrusive
- **FR-007**: System MUST support text input for user questions
- **FR-008**: System MUST stream responses progressively as they are generated

**Full-Book RAG Mode**
- **FR-009**: System MUST retrieve relevant chunks from the vector database when answering general questions
- **FR-010**: System MUST use semantic similarity search to find relevant content
- **FR-011**: System MUST provide grounded answers based only on retrieved content (no hallucination)

**Selected-Text Mode**
- **FR-012**: System MUST detect when user has highlighted text on the page
- **FR-013**: System MUST provide a mechanism to ask questions about selected text (button or automatic detection)
- **FR-014**: System MUST answer ONLY based on the selected text when in selected-text mode
- **FR-015**: System MUST NOT call the retrieval function when answering selected-text questions

**Mode Separation**
- **FR-016**: System MUST maintain strict separation between full-book and selected-text modes
- **FR-017**: System MUST clearly indicate which mode is active to the user

### Key Entities

- **Document**: Represents a single .md/.mdx file from the book (path, title, content)
- **Chunk**: A segment of a document suitable for embedding (content, position, parent document reference)
- **Embedding**: Vector representation of a chunk (vector, chunk reference)
- **ChatMessage**: A single message in a conversation (role: user/assistant, content, timestamp)
- **SelectedText**: User-highlighted text from the page (content, source page URL)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can ask a general question and receive a relevant answer within 10 seconds
- **SC-002**: Users can highlight text and ask a question about it within 3 clicks/interactions
- **SC-003**: Chat panel is visible and functional on 100% of documentation pages
- **SC-004**: Ingestion script processes all book files without errors in a single run
- **SC-005**: 90% of answers to questions about topics in the book cite accurate information from the book
- **SC-006**: 100% of selected-text mode answers derive exclusively from the highlighted text
- **SC-007**: System handles 10 concurrent users without degradation
- **SC-008**: Streaming responses begin appearing within 2 seconds of query submission

## Assumptions

- The existing Docusaurus site in ai-textbook/ is functional and can be started with `npm start`
- All book content is in English
- Document chunks of ~500-1000 tokens with ~100 token overlap are appropriate for this content type
- Users have modern browsers supporting text selection APIs
- Local development only - no deployment or production scaling requirements
- Credentials provided in .env are valid and have appropriate permissions

## Out of Scope

- User authentication or persistent chat history
- Multimodal inputs (images, audio, video)
- Analytics, logging, or monitoring of queries
- Deployment to production environments
- Custom chat UI (must use ChatKit.js only)
- Standalone chat application or separate page
- Support for languages other than English
- Mobile-specific optimizations
