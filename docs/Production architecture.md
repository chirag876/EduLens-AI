# EduLens AI — Production Architecture & LLM Interchangeability Guide

## 1. Server vs Client — What Runs Where

In a web-based production application, there is a clear separation between
what runs on the server and what runs on the user's device.

### User's Device (Browser Only)
- A standard web browser is all that is required
- No Python, no FFmpeg, no model installations
- The user sends HTTP requests and receives JSON responses
- The frontend (React/Next.js or any framework) handles the UI

### Server (Your Deployment — GCP/AWS/Azure)
Everything AI-related runs here:
- FastAPI application (EduLens AI backend)
- FFmpeg (installed at the OS level on the server)
- faster-whisper (Whisper model for transcription)
- sentence-transformers (embedding model)
- ChromaDB (vector database)
- Groq/OpenAI/HuggingFace API calls (LLM)

The student never sees or touches any of this.
They only see the final answer in their browser.

---

## 2. How FFmpeg Works in Production

### Local (Current Setup)
FFmpeg is installed on your Windows machine.
yt-dlp downloads the video, FFmpeg extracts audio, Whisper transcribes it.

### Production Server Setup
FFmpeg is installed on the Linux server at the OS level.
This is a one-time server configuration — done during deployment.

```bash
# On Ubuntu/Debian server (done once during setup)
sudo apt-get update
sudo apt-get install ffmpeg -y

# Verify
ffmpeg -version
```

Once installed on the server, every video ingestion request
automatically uses the server's FFmpeg. Students do not need
to install anything.

### Dockerfile Approach (Recommended)
When deploying with Docker, FFmpeg is included in the image:

```dockerfile
FROM python:3.11-slim

# Install FFmpeg at OS level
RUN apt-get update && apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This Docker image, when deployed on GCP Cloud Run or AWS ECS,
will have FFmpeg available automatically. No manual installation needed.

---

## 3. LLM Interchangeability — How to Switch Models

### Current Architecture
EduLens AI is designed so that the LLM is a pluggable component.
The only file that needs to change when switching LLMs is:

```
app/server/llm/generator.py
```

Everything else — retrieval, safety, personalization — remains unchanged.

### Option 1 — Groq (Current)
```python
# config.py
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL_NAME = os.environ.get("GROQ_MODEL_NAME", "llama3-8b-8192")

# generator.py
from groq import Groq
client = Groq(api_key=config.GROQ_API_KEY)
response = client.chat.completions.create(
    model=config.GROQ_MODEL_NAME,
    messages=[...]
)
```

Groq is ideal for POC and early production:
- Free tier available
- Extremely fast inference (fastest llama3 available)
- Paid plans are cost-effective
- No infrastructure management needed

### Option 2 — OpenAI (GPT-4o / GPT-3.5)
```python
# config.py
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

# generator.py
from openai import OpenAI
client = OpenAI(api_key=config.OPENAI_API_KEY)
response = client.chat.completions.create(
    model=config.OPENAI_MODEL_NAME,
    messages=[...]
)
```

When to use: Client wants best quality, budget is available.

### Option 3 — Google Gemini
```python
# config.py
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-flash")

# generator.py
import google.generativeai as genai
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
response = model.generate_content(prompt)
```

When to use: Client is already on GCP, easier billing integration.

### Option 4 — Hugging Face Inference API
```python
# config.py
HF_API_KEY = os.environ.get("HF_API_KEY", "")
HF_MODEL_NAME = os.environ.get("HF_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.3")

# generator.py
import requests
headers = {"Authorization": f"Bearer {config.HF_API_KEY}"}
response = requests.post(
    f"https://api-inference.huggingface.co/models/{config.HF_MODEL_NAME}",
    headers=headers,
    json={"inputs": prompt}
)
```

When to use: Open source models, cost control, specific domain models.

Note: HuggingFace Inference API is production-ready.
You do NOT need to host the model yourself.
HuggingFace runs the model on their infrastructure,
you just make API calls — same as Groq/OpenAI.

### Option 5 — Self-Hosted Model (Advanced)
If the client wants complete data privacy (no third-party API):

```python
# Using Ollama (local model server)
import requests
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3", "prompt": prompt}
)
```

When to use: Strict data privacy requirements, no internet access allowed,
large budget for GPU servers.
Infrastructure cost: High (GPU servers needed)

---

## 4. Making LLM Truly Interchangeable — Recommended Pattern

Instead of hardcoding one provider, use a factory pattern:

```python
# config.py
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")  # groq/openai/gemini/huggingface

# generator.py
def get_llm_client():
    if config.LLM_PROVIDER == "groq":
        from groq import Groq
        return Groq(api_key=config.GROQ_API_KEY)
    elif config.LLM_PROVIDER == "openai":
        from openai import OpenAI
        return OpenAI(api_key=config.OPENAI_API_KEY)
    elif config.LLM_PROVIDER == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        return genai
```

To switch providers: Change LLM_PROVIDER in .env — no code change needed.

---

## 5. Embedding Model in Production

### Current Setup
sentence-transformers (all-MiniLM-L6-v2) runs locally on the server.
Model is downloaded once (~90MB) and cached.
All embedding generation happens on your server — no external API calls.

### Production Consideration
This model runs on CPU — fine for moderate load.
For high load (thousands of concurrent users):

Option A: Keep local model, scale horizontally
(multiple server instances, each with the model loaded)

Option B: Switch to embedding API
```python
# OpenAI embeddings
from openai import OpenAI
client = OpenAI(api_key=config.OPENAI_API_KEY)
response = client.embeddings.create(
    input=texts,
    model="text-embedding-3-small"  # cheap and fast
)
embeddings = [item.embedding for item in response.data]
```

Recommendation for client: Start with local model (free, fast enough for POC
and early users). Switch to API-based embeddings only when load justifies it.

---

## 6. Vector Database in Production

### Current Setup
ChromaDB local (SQLite-based) — perfect for POC and development.

### Production Options

| Option | Best For | Cost |
|--------|----------|------|
| ChromaDB Server Mode | Small-medium scale | Free/Self-hosted |
| Pinecone | Scalable, managed | Paid (free tier available) |
| Weaviate Cloud | Enterprise | Paid |
| pgvector (PostgreSQL) | Already using Postgres | Free |

For client's first production version:
ChromaDB in server mode on the same GCP/AWS instance is sufficient.
Migrate to Pinecone when data exceeds 1M+ vectors.

---

## 7. Recommended Production Stack for Client

### Phase 1 — Early Production (0 to 1000 users)
```
Platform:     GCP Cloud Run (serverless, auto-scaling)
LLM:          Groq API (fast, cost-effective)
Embeddings:   Local sentence-transformers (free)
Vector DB:    ChromaDB server mode
Video:        FFmpeg on server via Docker
Cost:         ~$50-100/month
```

### Phase 2 — Growth (1000 to 10,000 users)
```
Platform:     GCP Cloud Run + Cloud SQL
LLM:          Groq or OpenAI based on quality needs
Embeddings:   OpenAI text-embedding-3-small API
Vector DB:    Pinecone starter plan
Cost:         ~$200-500/month
```

### Phase 3 — Scale (10,000+ users)
```
Platform:     GCP GKE (Kubernetes)
LLM:          Fine-tuned model on Vertex AI
Embeddings:   Vertex AI embeddings
Vector DB:    Pinecone or Weaviate enterprise
Cost:         Custom pricing
```

---

## 8. Summary — What Changes for Production

| Component | Development | Production | Change Required |
|-----------|-------------|------------|-----------------|
| FFmpeg | Local install | Server Docker image | Dockerfile only |
| Whisper | Local model | Server Docker image | No code change |
| Embeddings | Local model | Local or API | config.py only |
| LLM | Groq API | Any provider | generator.py only |
| Vector DB | ChromaDB local | ChromaDB/Pinecone | db.py only |
| App Server | uvicorn local | Cloud Run/ECS | Dockerfile + CI/CD |

The core AI pipeline code does not change for production.
Only infrastructure configuration changes.