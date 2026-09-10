import os

# App
PROXY_API_PREFIX = ""
APP_TITLE = os.environ.get("APP_TITLE", "EduLens AI")
ENV_NAME = os.environ.get("ENV_NAME", "dev")

# Swagger Docs Auth
DOC_USERNAME = os.environ.get("DOC_USERNAME", "Dev")
DOC_PASSWORD = os.environ.get("DOC_PASSWORD", "Dev")

# Groq LLM
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL_NAME = os.environ.get("GROQ_MODEL_NAME", "llama3-8b-8192")

# ChromaDB
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")

# Embedding Model
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Video Download
VIDEO_DOWNLOAD_PATH = os.environ.get("VIDEO_DOWNLOAD_PATH", "./temp_videos")

# Logging
LOG_FILE_NAME = os.environ.get("LOG_FILE_NAME", "app")