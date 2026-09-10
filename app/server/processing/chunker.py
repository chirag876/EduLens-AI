# =============================================================================
# Text Chunking Module
# =============================================================================
#
# This module is responsible for splitting large text content into smaller,
# meaningful chunks that can be processed efficiently by downstream AI
# components such as embedding generation and vector search.
#
# The same chunking logic is used for both PDF content and video transcripts
# to maintain a consistent processing pipeline across different data sources.
#
# Key Responsibilities:
#
# 1. Text Chunking
#    - Splits large PDF text and video transcript content into smaller chunks.
#    - Smaller chunks make the content easier to embed, store, retrieve, and
#      provide as context to the LLM.
#
# 2. Configurable Chunk Size
#    - CHUNK_SIZE defines the maximum number of characters considered for
#      each chunk.
#    - The current configuration uses 500 characters per chunk.
#
# 3. Chunk Overlap
#    - CHUNK_OVERLAP keeps a portion of the previous chunk in the next chunk.
#    - The current configuration uses a 50-character overlap.
#    - This helps preserve context when important information lies near a
#      chunk boundary.
#
# 4. Recursive Smart Splitting
#    - Uses RecursiveCharacterTextSplitter from langchain-text-splitters.
#    - The splitter attempts to preserve meaningful text boundaries instead
#      of blindly cutting the text at a fixed character position.
#    - Splitting is attempted in the following order:
#        1. Paragraph breaks
#        2. Line breaks
#        3. Sentence boundaries
#        4. Word boundaries
#        5. Individual characters as a final fallback
#
# 5. Metadata Preservation
#    - Metadata received with the original text is attached to every chunk.
#    - This allows downstream components to identify where a retrieved chunk
#      originated from, such as a PDF or video transcript.
#
# 6. Chunk Indexing
#    - Each generated chunk receives a sequential chunk_index.
#    - The index helps identify the original order of chunks within the
#      source content.
#
# 7. Input Validation and Error Handling
#    - Empty or whitespace-only text is rejected before processing.
#    - Chunking failures are converted into application-level
#      CustomHTTPException errors for consistent API error handling.
#
# =============================================================================

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier
from fastapi import status

# Chunk configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Returns a configured text splitter instance.

    Returns:
        RecursiveCharacterTextSplitter: Configured splitter.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=['\n\n', '\n', '. ', ' ', ''],
    )


def chunk_text(text: str, metadata: dict) -> list[dict]:
    """
    Split a large text into smaller overlapping chunks with metadata.

    Args:
        text (str): The full text to split (from PDF or video transcript).
        metadata (dict): Metadata to attach to each chunk
                         e.g. {'source_type': 'pdf', 'title': '...', 'url': '...'}

    Returns:
        list[dict]: List of chunks, each with 'text' and 'metadata'.
    """
    if not text or not text.strip():
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='text cannot be empty for chunking',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        splitter = get_text_splitter()
        chunks = splitter.split_text(text)
        logger.debug(f'Text split into {len(chunks)} chunks')

        result = []
        for index, chunk in enumerate(chunks):
            result.append({
                'text': chunk,
                'metadata': {
                    **metadata,
                    'chunk_index': index,
                },
            })

        return result

    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to chunk text: {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error