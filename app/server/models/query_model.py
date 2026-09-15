# =============================================================================
# Query API Schemas
# =============================================================================
#
# This module defines the Pydantic models used as request and response schemas
# for the student question-answering API.
#
# These schemas provide a clear contract between the API client and the
# backend by validating incoming questions and structuring the final response.
#
# Key Responsibilities:
#
# 1. Request Validation
#    - Validates the student's incoming question before it reaches the
#      retrieval and generation pipeline.
#    - Prevents empty, whitespace-only, or excessively short questions from
#      being processed.
#
# 2. Grade-Level Selection
#    - Allows the student to optionally specify a grade level.
#    - Uses the GradeLevel enum to ensure that only supported grade levels
#      are accepted.
#
# 3. Source Filtering
#    - Allows the student to optionally restrict retrieval to a specific
#      source type, such as PDF or Video.
#    - Uses the SourceType enum to validate the provided source type.
#
# 4. Source Reference Structure
#    - Defines a consistent structure for curriculum sources returned with
#      the generated answer.
#    - Each source contains its title, type, and URL.
#
# 5. Response Structure
#    - Defines the final API response returned to the student.
#    - Contains the generated answer, optional grade-level information,
#      source references, and the total number of sources.
#
# 6. Type Safety and Serialization
#    - Uses Pydantic models to validate incoming data and serialize outgoing
#      response data into a predictable API format.
#
# =============================================================================

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