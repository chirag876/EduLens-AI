<div align="center">

<img src="https://img.shields.io/badge/EduLens-AI-4A90D9?style=for-the-badge&logoColor=white" alt="EduLens-AI" width="300"/>

# EduLens-AI

**A production-grade Retrieval-Augmented Generation (RAG) platform for curriculum-grounded question answering.**

EduLens-AI ingests educational content from PDFs and videos, builds a semantic knowledge base, and answers student questions strictly from the ingested curriculum with page-level citations, grade-level personalization, and built-in safety moderation.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35?style=flat-square)](https://trychroma.com)
[![Groq](https://img.shields.io/badge/Groq-LLM_API-F54D27?style=flat-square)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What is EduLens-AI?

EduLens-AI is a backend RAG system built for educational platforms. It allows institutions to ingest their own curriculum content textbooks, lecture slides, recorded sessions and expose a question-answering API that responds only from that content. The system never hallucinates beyond the provided material, always cites its sources with exact page numbers, and adapts its language based on the student's grade level.

---

## System Architecture

```
                          INGESTION PIPELINE
 ┌─────────────┐
 │  PDF / Video │
 │     URL      │
 └──────┬───────┘
        │
        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    INGESTION LAYER                          │
 │                                                             │
 │   PDF Flow                        Video Flow               │
 │   ─────────────────               ──────────────────────   │
 │   Fetch PDF (HTTPX)               Download Audio (yt-dlp)  │
 │        │                               │                   │
 │   Extract Text (PyMuPDF)          Transcribe (Whisper)     │
 │        │                               │                   │
 │   Clean Text                      Clean Transcript         │
 │        │                               │                   │
 │   Chunk per Page                  Chunk Text               │
 │        │                               │                   │
 │        └──────────┬────────────────────┘                   │
 │                   │                                        │
 │          Generate Embeddings                               │
 │       (Sentence Transformers)                              │
 │                   │                                        │
 │          Store in ChromaDB                                 │
 │       (PDF Collection / Video Collection)                  │
 └─────────────────────────────────────────────────────────────┘

                          QUERY PIPELINE
 ┌─────────────────┐
 │ Student Question │
 └────────┬─────────┘
          │
          ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                     QUERY LAYER                             │
 │                                                             │
 │   Embed Question                                            │
 │   (Sentence Transformers)                                   │
 │          │                                                  │
 │          ▼                                                  │
 │   Semantic Search                                           │
 │   ChromaDB — PDF + Video Collections (TOP-K)               │
 │          │                                                  │
 │          ▼                                                  │
 │   Generate Answer                                           │
 │   (Groq LLM — curriculum-grounded prompt)                  │
 │          │                                                  │
 │          ▼                                                  │
 │   Safety Moderation                                         │
 │   (Length / Harmful Content / Off-Curriculum / Relevance)  │
 │          │                                                  │
 │          ▼                                                  │
 │   Grade-Level Personalization                               │
 │   (Primary / Middle / High School / College)               │
 │          │                                                  │
 │          ▼                                                  │
 │   Final Response                                            │
 │   Answer + Sources + Pages Cited + Chunk Indices           │
 └─────────────────────────────────────────────────────────────┘
```

---

## Features

### Ingestion
- **PDF Ingestion** — Fetches PDFs directly from URL (including Google Drive), extracts text page-by-page using PyMuPDF, cleans, chunks, and stores with page-level metadata
- **Video Ingestion** — Downloads audio via yt-dlp, transcribes using Faster-Whisper locally, cleans transcript and stores as searchable chunks
- **Duplicate Detection** — Skips re-ingestion if the same source title already exists in the vector store
- **In-Memory Processing** — PDFs are never written to disk; processed entirely in memory

### Retrieval
- **Semantic Search** — Embeds the student question and retrieves top-K most relevant chunks from both PDF and video collections
- **Multi-Source Retrieval** — Searches across PDF and video collections simultaneously and merges by relevance distance
- **Source Filtering** — Optionally restrict retrieval to PDF-only or Video-only sources

### Answer Generation
- **Curriculum-Grounded** — LLM is strictly prompted to answer only from retrieved context; refuses to fabricate
- **Page-Level Citations** — Response includes exact page numbers and chunk indices from which the answer was derived
- **Grade-Level Adaptation** — Adjusts language complexity for Primary, Middle School, High School, and College levels

### Safety & Moderation
- **Minimum Length Check** — Rejects answers too short to be meaningful
- **Harmful Content Filter** — Keyword-based detection for unsafe content
- **Off-Curriculum Detection** — Catches responses where the LLM broke character or referenced external AI systems
- **Relevance Check** — Word-overlap heuristic ensures the answer is grounded in retrieved content

---

## API Reference

### Ingestion Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest/pdf` | Ingest a PDF from URL |
| `POST` | `/api/v1/ingest/video` | Ingest a video from URL |
| `DELETE` | `/api/v1/ingest/pdf` | Remove an ingested PDF by title |
| `DELETE` | `/api/v1/ingest/video` | Remove an ingested video by title |

### Query Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Ask a question against the curriculum |

### Sample Request — Ingest PDF

```json
POST /api/v1/ingest/pdf
{
  "url": "https://example.com/textbook.pdf",
  "title": "Biology Chapter 5"
}
```

### Sample Request — Query

```json
POST /api/v1/query
{
  "question": "What is photosynthesis?",
  "grade_level": "high",
  "source_type": "pdf"
}
```

### Sample Response — Query

```json
{
  "answer": "Photosynthesis is the process by which green plants convert sunlight into chemical energy...",
  "grade_level": "High School",
  "sources": [
    {
      "title": "Biology Chapter 5",
      "type": "PDF",
      "url": "https://example.com/textbook.pdf",
      "pages_cited": [33, 35, 61],
      "chunk_indices": [93, 100, 221]
    }
  ],
  "total_sources": 1
}
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI | REST API, async request handling |
| Vector Database | ChromaDB | Semantic chunk storage and retrieval |
| Embedding Model | all-MiniLM-L6-v2 (Sentence Transformers) | Text-to-vector conversion |
| LLM | Groq (configurable model) | Answer generation |
| PDF Processing | PyMuPDF (fitz) | In-memory page-level text extraction |
| HTTP Client | HTTPX | Async PDF fetching |
| Audio Download | yt-dlp | Video audio extraction |
| Transcription | Faster-Whisper | Local CPU-based audio transcription |
| Text Chunking | LangChain Text Splitters | Recursive character-based chunking |
| Validation | Pydantic v2 | Request/response schema validation |
| Containerization | Docker | Deployment and environment isolation |

---

## Project Structure

```
EduLens-AI/
├── app/
│   ├── main.py
│   └── server/
│       ├── config/          # Environment configuration
│       ├── database/        # ChromaDB client and core data operations
│       ├── embeddings/      # Sentence Transformer singleton + batch embedding
│       ├── ingestion/       # PDF and video ingestion pipelines
│       ├── llm/             # Groq answer generation and prompt construction
│       ├── models/          # Pydantic request/response schemas
│       ├── personalization/ # Grade-level response formatting
│       ├── processing/      # Text cleaning and chunking
│       ├── retrieval/       # Semantic search across collections
│       ├── routes/          # FastAPI route definitions
│       ├── safety/          # Answer moderation layer
│       ├── static/          # Enums, constants, error identifiers
│       └── utils/           # Shared utility functions
├── docs/                    # Architecture diagrams and documentation
├── temp_videos/             # Temporary audio files (auto-deleted post-ingestion)
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- FFmpeg (required for yt-dlp audio conversion)
- Groq API Key

### Installation

```bash
git clone https://github.com/chirag876/EduLens-AI.git
cd EduLens-AI
python -m venv myenv
source myenv/bin/activate  # Windows: myenv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
GROQ_MODEL_NAME=llama3-8b-8192
VIDEO_DOWNLOAD_PATH=./temp_videos
```

### Run the Server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs available at: `http://127.0.0.1:8000/docs`

---

## Upcoming Features

- **Background Job Processing** — Celery + Redis based async ingestion so users are not blocked during large document processing
- **Global Structured Logging** — Cloud-agnostic logging system with per-step ingestion timing for performance monitoring
- **Groq Whisper API Integration** — Replace local Whisper with Groq's hosted Whisper for significantly faster video transcription
- **Multi-language Support** — Configurable response language per institution
- **Admin Dashboard** — Ingestion status tracking, chunk inspection, and query analytics
- **Webhook Notifications** — Notify clients when background ingestion jobs complete
- **Authentication Layer** — JWT/API key based access control per tenant

---

## Known Limitations

- Embedding generation on CPU is the primary bottleneck for large PDFs (400+ pages takes approximately 2 minutes)
- Video transcription using local Whisper on CPU adds significant processing time for longer videos
- Page number citations reflect PDF page indices, which may differ from printed book page numbers

---

<div align="center">

Built by [Chirag Gupta](https://linkedin.com/in/chiraggupta1706)

</div>