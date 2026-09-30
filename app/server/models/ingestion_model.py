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
    title: str
    url: str
    total_chunks: int
    source_type: str
    message: str = 'Ingestion completed successfully'
