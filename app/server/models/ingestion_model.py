from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator
from app.server.static.enums import SourceType


class IngestionRequest(BaseModel):
    source_type: SourceType
    url: HttpUrl
    title: str

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('title cannot be empty')
        return v.strip()


class IngestionResponse(BaseModel):
    doc_id: Optional[str] = None
    title: str
    url: str
    total_chunks: int
    source_type: str
    message: str = 'Ingestion completed successfully'

class IngestedDocument(BaseModel):
    doc_id: Optional[str] = None          # None only for documents ingested before doc_id existed
    source_type: str
    title: str
    url: str
    ingested_at: Optional[str] = None     # ISO timestamp (UTC); None for legacy documents
    total_chunks: int
    total_embeddings: int                 # always equal to total_chunks (1 vector per chunk in Chroma)
    total_pages: Optional[int] = None     # PDFs only