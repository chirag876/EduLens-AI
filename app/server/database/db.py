import chromadb
from app.server.config import config

chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)