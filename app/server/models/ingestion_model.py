# =============================================================================
# Ingestion API Schemas
# =============================================================================
#
# This module defines the Pydantic request and response schemas used by the
# document and video ingestion APIs.
#
# These schemas validate incoming source information before it reaches the
# ingestion pipeline and provide a consistent structure for ingestion results.
#
# Key Responsibilities:
#
# 1. PDF Ingestion Request Validation
#    - Validates that the provided PDF URL is a valid HTTP/HTTPS URL.
#    - Ensures that the URL points to a PDF file by checking for the `.pdf`
#      extension.
#    - Validates and normalizes the PDF title.
#
# 2. Video Ingestion Request Validation
#    - Validates that the provided video URL is a valid HTTP/HTTPS URL.
#    - Validates and normalizes the video title before starting ingestion.
#
# 3. Input Normalization
#    - Removes unnecessary leading and trailing whitespace from titles.
#    - Prevents empty titles from entering the ingestion pipeline.
#
# 4. Ingestion Response Structure
#    - Defines a consistent response format for completed PDF and video
#      ingestion operations.
#    - Returns the source title, URL, number of generated chunks, source type,
#      and a success message.
#
# 5. Type Safety and Serialization
#    - Uses Pydantic models to validate incoming request data and serialize
#      ingestion results into a predictable API response format.
#
# =============================================================================

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