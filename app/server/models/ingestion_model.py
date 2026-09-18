from pydantic import BaseModel, HttpUrl, field_validator


class PDFIngestionRequest(BaseModel):
    url: HttpUrl
    title: str

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('title cannot be empty')
        return v.strip()


class VideoIngestionRequest(BaseModel):
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