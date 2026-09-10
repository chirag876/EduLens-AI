# =============================================================================
# Video Ingestion Module
# =============================================================================
#
# This module implements the complete ingestion pipeline for video content.
# It downloads the audio track from a video, converts the audio into text
# using Faster-Whisper, processes the transcript, generates embeddings, and
# stores the resulting chunks in ChromaDB.
#
# The video itself is not processed as a video stream. Only its audio track
# is downloaded and temporarily stored on disk for transcription.
#
# Processing Flow:
#
#     Video URL
#        │
#        ▼
#     Download Audio using yt-dlp
#        │
#        ▼
#     Transcribe Audio using Faster-Whisper
#        │
#        ▼
#     Clean Transcript
#        │
#        ▼
#     Split Transcript into Chunks
#        │
#        ▼
#     Generate Embeddings
#        │
#        ▼
#     Store Chunks + Embeddings + Metadata in ChromaDB
#        │
#        ▼
#     Delete Temporary Audio File
#
# Key Responsibilities:
#
# 1. Audio Extraction
#    - Uses yt-dlp to download the best available audio from the provided
#      video URL.
#    - The downloaded audio is converted to MP3 using FFmpeg.
#    - A unique UUID-based filename is used to avoid filename collisions.
#
# 2. Temporary File Management
#    - Audio files are stored temporarily in the configured video download
#      directory while they are being processed.
#    - The temporary file is deleted after processing is complete.
#    - Cleanup is performed inside a finally block so that the file is removed
#      even when an error occurs during transcription, cleaning, chunking,
#      embedding, or database storage.
#
# 3. Audio Transcription
#    - Uses Faster-Whisper to convert the downloaded audio into text.
#    - The Whisper base model is configured to run on the CPU using int8
#      computation, so GPU hardware is not required.
#    - The model is loaded only once and the same instance is reused for
#      subsequent transcription requests.
#    - If the model is not already available locally, Faster-Whisper downloads
#      the required model files when the model is loaded for the first time.
#
# 4. Transcript Cleaning
#    - Passes the raw transcript through the transcript-specific cleaning
#      pipeline.
#    - Removes timestamps, speaker labels, filler words, URLs, control
#      characters, and unnecessary whitespace.
#
# 5. Transcript Chunking
#    - Splits the cleaned transcript into smaller overlapping chunks.
#    - Each chunk retains source metadata such as source type, title, URL,
#      and chunk index.
#
# 6. Embedding Generation
#    - Converts every transcript chunk into a numerical embedding vector
#      using the shared embedding model.
#    - These embeddings are later used for semantic similarity search.
#
# 7. ChromaDB Storage
#    - Generates a unique UUID for every transcript chunk.
#    - Stores the chunk text, embeddings, and metadata in the configured
#      video chunks collection.
#
# 8. Validation and Error Handling
#    - Validates the processing stages before continuing through the pipeline.
#    - Converts ingestion-related failures into application-level
#      CustomHTTPException errors.
#
# =============================================================================

import os
import uuid

import yt_dlp
from faster_whisper import WhisperModel
from fastapi import status

from app.server.config import config
from app.server.database import core_data as db
from app.server.embeddings.embedder import generate_embeddings
from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.processing.cleaner import clean_transcript_text
from app.server.processing.chunker import chunk_text
from app.server.static.collections import Collections
from app.server.static import error_identifier
from app.server.static.enums import SourceType

# Load Whisper model once — reused across all requests
_whisper_model = None


def get_whisper_model() -> WhisperModel:
    """
    Returns the Whisper model instance.
    Loads it once and reuses across all requests (singleton pattern).

    Returns:
        WhisperModel: The loaded Whisper model.
    """
    global _whisper_model
    if _whisper_model is None:
        logger.debug('Loading Whisper model: base')
        # base model — good balance of speed and accuracy for educational content
        # runs on CPU — no GPU required
        _whisper_model = WhisperModel('base', device='cpu', compute_type='int8')
        logger.debug('Whisper model loaded successfully')
    return _whisper_model


def download_audio(video_url: str) -> str:
    """
    Download audio from a video URL using yt-dlp.
    Saves audio as mp3 in the configured temp directory.

    Args:
        video_url (str): The video URL (YouTube or other supported platform).

    Returns:
        str: Path to the downloaded audio file.
    """
    os.makedirs(config.VIDEO_DOWNLOAD_PATH, exist_ok=True)

    file_id = str(uuid.uuid4())
    output_path = os.path.join(config.VIDEO_DOWNLOAD_PATH, file_id)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        audio_path = f'{output_path}.mp3'
        logger.debug(f'Audio downloaded: {audio_path}')
        return audio_path
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to download audio from video: {str(error)}',
            identifier=error_identifier.VIDEO_INGESTION_FAILED,
        ) from error


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using faster-whisper.

    Args:
        audio_path (str): Path to the audio file.

    Returns:
        str: Full transcript text.
    """
    try:
        model = get_whisper_model()
        logger.debug(f'Transcribing audio: {audio_path}')
        segments, _ = model.transcribe(audio_path, beam_size=5)
        transcript = ' '.join([segment.text.strip() for segment in segments])
        logger.debug(f'Transcription complete — {len(transcript)} chars')
        return transcript
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to transcribe audio: {str(error)}',
            identifier=error_identifier.VIDEO_INGESTION_FAILED,
        ) from error


def delete_audio_file(audio_path: str) -> None:
    """
    Delete the temporary audio file after processing.

    Args:
        audio_path (str): Path to the audio file.
    """
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.debug(f'Temp audio file deleted: {audio_path}')
    except Exception as error:
        logger.error(f'Failed to delete temp audio file: {str(error)}')


async def ingest_video(url: str, title: str) -> dict:
    """
    Full ingestion pipeline for a video:
    Download Audio → Transcribe → Clean → Chunk → Embed → Store in ChromaDB.

    Args:
        url (str): URL of the video (YouTube or other supported platform).
        title (str): Title/name of the video.

    Returns:
        dict: Summary of ingestion with chunk count.
    """
    logger.debug(f'Starting video ingestion: {title}')
    audio_path = None

    try:
        # Step 1: Download audio only
        audio_path = download_audio(url)

        # Step 2: Transcribe audio to text
        raw_transcript = transcribe_audio(audio_path)

        # Step 3: Clean transcript
        cleaned_transcript = clean_transcript_text(raw_transcript)

        # Step 4: Chunk text
        metadata = {
            'source_type': SourceType.VIDEO,
            'title': title,
            'url': url,
        }
        chunks = chunk_text(cleaned_transcript, metadata)

        if not chunks:
            raise CustomHTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'No chunks generated from video: {title}',
                identifier=error_identifier.VIDEO_INGESTION_FAILED,
            )

        # Step 5: Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = generate_embeddings(texts)

        # Step 6: Prepare data for ChromaDB
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]

        # Step 7: Store in ChromaDB
        db.add_documents(
            collection_name=Collections.VIDEO_CHUNKS,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        logger.debug(f'Video ingestion complete: {title} — {len(chunks)} chunks stored')

        return {
            'title': title,
            'url': url,
            'total_chunks': len(chunks),
            'source_type': SourceType.VIDEO,
        }

    finally:
        # Always delete temp audio file even if ingestion fails
        if audio_path:
            delete_audio_file(audio_path)