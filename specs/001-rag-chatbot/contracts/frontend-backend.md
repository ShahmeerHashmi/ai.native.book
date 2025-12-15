# Frontend-Backend Contract: RAG Chatbot

## Communication Protocol

### ChatKit Protocol (Primary)

The frontend ChatKit.js component communicates with the backend using the standard ChatKit protocol over HTTP POST with SSE streaming responses.

```
Frontend (ChatKit.js)                    Backend (FastAPI)
       │                                        │
       │ POST /chatkit                          │
       │ Content-Type: application/json         │
       │ ───────────────────────────────────>   │
       │                                        │
       │ 200 OK                                 │
       │ Content-Type: text/event-stream        │
       │ <───────────────────────────────────   │
       │                                        │
       │ event: message                         │
       │ data: {"delta": "ROS2 is..."}          │
       │ <───────────────────────────────────   │
       │                                        │
       │ event: done                            │
       │ data: {}                               │
       │ <───────────────────────────────────   │
```

### Request Format

#### Standard Message (Full-Book RAG Mode)
```json
{
  "type": "send_message",
  "thread_id": "uuid-or-null",
  "message": {
    "content": "What is ROS2?"
  }
}
```

#### Selected-Text Mode
```json
{
  "type": "send_message",
  "thread_id": "uuid-or-null",
  "message": {
    "content": "Explain this concept"
  },
  "context": {
    "selected_text": "Gazebo is a robotics simulator that integrates..."
  }
}
```

### Response Format (SSE Stream)

#### Message Chunk Event
```
event: message
data: {"type": "text_delta", "delta": "ROS2 (Robot Operating System 2) "}
```

#### Source Citation Event (RAG mode only)
```
event: source
data: {"document_path": "ros2.md", "title": "ROS2 Architecture", "excerpt": "..."}
```

#### Completion Event
```
event: done
data: {"mode": "rag", "sources_count": 3}
```

#### Error Event
```
event: error
data: {"error": "Failed to retrieve context", "code": "RETRIEVAL_ERROR"}
```

---

## Mode Detection Logic

### Backend Decision Tree

```python
def determine_mode(request):
    if request.context and request.context.get("selected_text"):
        return "selected_text"
    else:
        return "rag"
```

### Frontend Context Passing

The frontend must detect text selection and include it in the request context:

```javascript
// On chat submit
const selectedText = window.getSelection()?.toString().trim();

chatkit.setOptions({
  api: {
    url: 'http://localhost:8000/chatkit',
    domainKey: 'local-dev',
  },
  // Pass selected text as context
  onBeforeSend: (message) => ({
    ...message,
    context: selectedText ? { selected_text: selectedText } : undefined,
  }),
});
```

---

## Error Handling Contract

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request body |
| `MESSAGE_TOO_LONG` | 400 | Message exceeds 5000 chars |
| `SELECTED_TEXT_TOO_LONG` | 400 | Selected text exceeds 10000 chars |
| `RETRIEVAL_ERROR` | 500 | Failed to query Qdrant |
| `GENERATION_ERROR` | 500 | Failed to generate response from Gemini |
| `DATABASE_ERROR` | 500 | Failed to connect to Neon PostgreSQL |

---

## CORS Configuration

The backend must allow CORS from the Docusaurus dev server:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Docusaurus dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

---

## Health Check Contract

### Request
```
GET /health
```

### Response (200 OK)
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "qdrant": "connected",
    "gemini": "available",
    "cohere": "available"
  }
}
```

### Response (503 Service Unavailable)
```json
{
  "status": "unhealthy",
  "services": {
    "database": "connected",
    "qdrant": "disconnected",
    "gemini": "available",
    "cohere": "available"
  }
}
```
