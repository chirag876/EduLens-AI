# =============================================================================
# PDF Ingestion Module
# =============================================================================
#
# This module implements the complete ingestion pipeline for PDF documents.
# It takes a PDF URL, extracts its text, processes the extracted content,
# generates embeddings, and stores the resulting chunks in ChromaDB.
#
# The PDF is processed entirely in memory. The implementation does not save
# the PDF to disk during ingestion.
#
# Processing Flow:
#
#     PDF URL
#        │
#        ▼
#     Fetch PDF Bytes
#        │
#        ▼
#     Extract Text using PyMuPDF
#        │
#        ▼
#     Clean Extracted Text
#        │
#        ▼
#     Split Text into Chunks
#        │
#        ▼
#     Generate Embeddings
#        │
#        ▼
#     Store Chunks + Embeddings + Metadata in ChromaDB
#
# Key Responsibilities:
#
# 1. In-Memory PDF Fetching
#    - Fetches the PDF content directly from the provided URL using HTTPX.
#    - The response content is kept in memory as bytes.
#    - The PDF is not written to disk during the ingestion process.
#
# 2. PDF Text Extraction
#    - Uses PyMuPDF (fitz) to open the PDF from its in-memory byte content.
#    - Extracts text from every page that contains meaningful text.
#    - Combines the extracted page content into a single text string.
#
# 3. Text Cleaning
#    - Passes the extracted raw text through the PDF-specific cleaning
#      pipeline before further processing.
#    - Removes common extraction artifacts and unnecessary text noise.
#
# 4. Text Chunking
#    - Splits the cleaned PDF text into smaller, overlapping chunks.
#    - Attaches source metadata such as source type, title, URL, and chunk index
#      to every generated chunk.
#
# 5. Embedding Generation
#    - Converts every text chunk into a numerical embedding vector using the
#      shared embedding model.
#    - These embeddings allow the document chunks to be searched later using
#      semantic similarity.
#
# 6. ChromaDB Storage
#    - Generates a unique UUID for every chunk.
#    - Stores the chunk text, generated embedding, and associated metadata in
#      the configured PDF ChromaDB collection.
#
# 7. Pipeline Validation and Error Handling
#    - Validates HTTP responses and generated chunks before continuing through
#      the pipeline.
#    - Converts ingestion, fetching, extraction, and storage failures into
#      application-level CustomHTTPException errors.
#
# =============================================================================
import uuid
from io import BytesIO

import fitz  # PyMuPDF
import httpx
from fastapi import status

from app.server.database import core_data as db
from app.server.embeddings.embedder import generate_embeddings
from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.processing.cleaner import clean_pdf_text
from app.server.processing.chunker import chunk_text
from app.server.static.collections import Collections
from app.server.static import error_identifier
from app.server.static.enums import SourceType


async def fetch_pdf_bytes(url: str) -> bytes:
    """
    Fetch PDF content from a URL into memory without downloading to disk.

    Args:
        url (str): The URL of the PDF.

    Returns:
        bytes: PDF file content as bytes.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise CustomHTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Failed to fetch PDF from URL: {url} — status {response.status_code}',
                    identifier=error_identifier.PDF_INGESTION_FAILED,
                )
            return response.content
    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error fetching PDF: {str(error)}',
            identifier=error_identifier.PDF_INGESTION_FAILED,
        ) from error


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract full text from PDF bytes using PyMuPDF (in-memory).

    Args:
        pdf_bytes (bytes): PDF content as bytes.

    Returns:
        str: Extracted raw text from all pages.
    """
    try:
        pdf_document = fitz.open(stream=BytesIO(pdf_bytes), filetype='pdf')
        full_text = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            if text.strip():
                full_text.append(text)

        pdf_document.close()
        extracted = '\n\n'.join(full_text)
        logger.debug(f'Extracted text from {len(pdf_document)} pages — {len(extracted)} chars')
        return extracted

    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to extract text from PDF: {str(error)}',
            identifier=error_identifier.PDF_INGESTION_FAILED,
        ) from error


async def ingest_pdf(url: str, title: str) -> dict:
    """
    Full ingestion pipeline for a PDF:
    Fetch → Extract → Clean → Chunk → Embed → Store in ChromaDB.

    Args:
        url (str): URL of the PDF (read-only access, no download).
        title (str): Title/name of the PDF document.

    Returns:
        dict: Summary of ingestion with chunk count and document id.
    """
    logger.debug(f'Starting PDF ingestion: {title}')

    # Step 1: Fetch PDF bytes into memory
    pdf_bytes = await fetch_pdf_bytes(url)

    # Step 2: Extract raw text
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)

    # Step 3: Clean text
    cleaned_text = clean_pdf_text(raw_text)

    # Step 4: Chunk text
    metadata = {
        'source_type': SourceType.PDF,
        'title': title,
        'url': url,
    }
    chunks = chunk_text(cleaned_text, metadata)

    if not chunks:
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'No chunks generated from PDF: {title}',
            identifier=error_identifier.PDF_INGESTION_FAILED,
        )

    # Step 5: Generate embeddings
    texts = [chunk['text'] for chunk in chunks]
    embeddings = generate_embeddings(texts)

    # Step 6: Prepare data for ChromaDB
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]

    # Step 7: Store in ChromaDB
    db.add_documents(
        collection_name=Collections.PDF_CHUNKS,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    logger.debug(f'PDF ingestion complete: {title} — {len(chunks)} chunks stored')

    return {
        'title': title,
        'url': url,
        'total_chunks': len(chunks),
        'source_type': SourceType.PDF,
    }