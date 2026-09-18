# =============================================================================
# Text Cleaning Module
# =============================================================================
#
# This module is responsible for cleaning raw text extracted from different
# content sources before it enters the downstream processing pipeline.
#
# Raw extracted content can contain unnecessary formatting, technical
# artifacts, or conversational noise. Cleaning this content before chunking
# and embedding helps produce cleaner and more meaningful AI representations.

import re

from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier
from fastapi import status


def clean_pdf_text(text: str) -> str:
    """
    Clean raw text extracted from a PDF.
    Removes extra whitespace, page numbers, repeated headers/footers patterns.

    Args:
        text (str): Raw text extracted from PDF.

    Returns:
        str: Cleaned text.
    """
    if not text or not text.strip():
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='PDF text cannot be empty for cleaning',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        # Remove non-printable/control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)

        # Remove page number patterns e.g. "Page 1 of 10", "- 1 -", "1 |"
        text = re.sub(r'(page\s*\d+\s*(of\s*\d+)?)|(-\s*\d+\s*-)|(^\d+\s*\|)', '', text, flags=re.IGNORECASE | re.MULTILINE)

        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Replace multiple spaces/tabs with single space
        text = re.sub(r'[ \t]+', ' ', text)

        # Strip each line
        lines = [line.strip() for line in text.splitlines()]

        # Remove empty lines at start/end, keep single empty lines in between
        text = '\n'.join(lines).strip()

        logger.debug(f'PDF text cleaned — final length: {len(text)} chars')
        return text

    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to clean PDF text: {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error


def clean_transcript_text(text: str) -> str:
    """
    Clean raw transcript text extracted from a video.
    Removes timestamps, speaker labels, filler words, and extra whitespace.

    Args:
        text (str): Raw transcript text.

    Returns:
        str: Cleaned transcript text.
    """
    if not text or not text.strip():
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Transcript text cannot be empty for cleaning',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        # Remove timestamps like [00:01:23] or (00:01:23) or 00:01:23 -->
        text = re.sub(r'[\[\(]?\d{1,2}:\d{2}(:\d{2})?[\]\)]?(\s*-->.*)?', '', text)

        # Remove speaker labels like "Speaker 1:" or "SPEAKER:"
        text = re.sub(r'^[A-Z][A-Z\s]+:\s*', '', text, flags=re.MULTILINE)

        # Remove filler words
        filler_words = r'\b(um|uh|hmm|erm|like|you know|i mean|basically|literally|actually|so yeah)\b'
        text = re.sub(filler_words, '', text, flags=re.IGNORECASE)

        # Remove non-printable/control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)

        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Replace multiple spaces/tabs with single space
        text = re.sub(r'[ \t]+', ' ', text)

        # Strip each line
        lines = [line.strip() for line in text.splitlines()]
        text = '\n'.join(lines).strip()

        logger.debug(f'Transcript text cleaned — final length: {len(text)} chars')
        return text

    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to clean transcript text: {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error