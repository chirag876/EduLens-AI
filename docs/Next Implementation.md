# Next Implementation

This file contains the next implementation items for the EduLens AI RAG system.

## 1. Citation

### Goal
Return source references that identify the specific page and chunk from which retrieved content came, instead of only returning the overall document URL.

### Implementation

#### `ingestion/pdf_ingestion.py`
Add page number metadata while extracting PDF pages:

```python
for page_num in range(total_pages):
    page = pdf_document[page_num]
    text = page.get_text()

    if text.strip():
        full_text.append({
            "text": text,
            "page_number": page_num + 1,
        })
```

Carry the page number into chunk metadata:

```python
chunks_with_pages = []

for page_data in pages:
    page_chunks = chunk_text(
        page_data["text"],
        metadata={
            "source_type": SourceType.PDF,
            "title": title,
            "url": url,
            "page_number": page_data["page_number"],
        },
    )

    chunks_with_pages.extend(page_chunks)
```

#### `models/query_model.py`
Extend `SourceReference`:

```python
class SourceReference(BaseModel):
    title: str
    type: str
    url: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
```

#### `llm/generator.py`
Include page and chunk metadata in returned sources:

```python
sources.append({
    "title": chunk["metadata"].get("title", "Unknown"),
    "source_type": chunk["metadata"].get("source_type", "unknown"),
    "url": chunk["metadata"].get("url", ""),
    "page_number": chunk["metadata"].get("page_number"),
    "chunk_index": chunk["metadata"].get("chunk_index"),
})
```

**Important:** Existing ChromaDB data must be re-ingested after adding page metadata because old chunks do not contain `page_number`.

---

## 2. Confidence Score

### Goal
Calculate an internal RAG response confidence score based on retrieval relevance, answer grounding, and answer completeness.

### Planned components

| Component | Weight | Purpose |
|---|---:|---|
| Retrieval relevance | 40% | Measures how relevant the retrieved chunks are |
| Answer grounding | 40% | Measures how strongly the answer is supported by retrieved context |
| Answer completeness | 20% | Basic signal based on answer length |

### Evaluation Matrix

| Score | Meaning | Action |
|---|---|---|
| 0.8 - 1.0 | High confidence | Answer as-is |
| 0.6 - 0.8 | Medium confidence | Add disclaimer |
| 0.4 - 0.6 | Low confidence | Suggest teacher |
| 0.0 - 0.4 | Very low | Return "not found" |

### Implementation

Create:

`evaluation/evaluator.py`

```python
def calculate_confidence_score(
    question: str,
    answer: str,
    chunks: list[dict],
) -> dict:
    """Calculate an internal confidence score for a RAG response."""
```

The implementation should calculate the three components above and return:

```python
{
    "confidence_score": ...,
    "retrieval_score": ...,
    "grounding_score": ...,
    "breakdown": {
        "retrieval_relevance": ...,
        "answer_grounding": ...,
        "answer_completeness": ...,
    },
}
```

In `routes/query.py`, calculate the score after answer generation/moderation and log it internally.

**Note:** This score should initially be treated as a development/evaluation signal, not as a proven factual accuracy percentage.

---

## 3. Prompt Caching

### Current approach

The system prompt is now template-based:

`templates/system_prompt.txt`

and `build_prompt()` loads and formats the template dynamically.

For the current POC, keep the prompt template file-based rather than introducing a database lookup for every request.

### Future production approach

If prompts become database-managed:

```text
Request
  ↓
Prompt/config lookup
  ↓
Cache
  ↓
Build prompt
  ↓
LLM
```

Use an in-memory or distributed cache so the database is not queried on every request.

Example concept:

```python
_prompt_cache = {}

def get_system_prompt(prompt_key: str = "default") -> str:
    if prompt_key in _prompt_cache:
        return _prompt_cache[prompt_key]

    prompt = db.get_prompt(prompt_key)
    _prompt_cache[prompt_key] = prompt
    return prompt
```

For production, define a cache TTL/invalidation strategy when prompts are updated.

### Configuration boundary

Client-configurable values can include:

- Institution name
- Language
- Tone
- Grade level

Developer-controlled base instructions and safety rules should remain protected and should not be freely editable by the client.
