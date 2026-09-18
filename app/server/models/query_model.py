from typing import Optional

from pydantic import BaseModel, field_validator

from app.server.static.enums import GradeLevel, SourceType


class QueryRequest(BaseModel):
    question: str
    grade_level: Optional[GradeLevel] = None
    source_type: Optional[SourceType] = None

    @field_validator('question')
    @classmethod
    def question_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('question cannot be empty')
        if len(v.strip()) < 5:
            raise ValueError('question is too short')
        return v.strip()


class SourceReference(BaseModel):
    title: str
    type: str
    url: str
    pages_cited: list[int] = []       # page numbers from which answer was retrieved
    chunk_indices: list[int] = []     # internal chunk indices (for debugging)


class QueryResponse(BaseModel):
    answer: str
    grade_level: Optional[str] = None
    sources: list[SourceReference]
    total_sources: int