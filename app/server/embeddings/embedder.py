# =============================================================================
# Embedding Module
# =============================================================================
#
# This module is responsible for converting text chunks into numerical
# embedding vectors using Sentence Transformers.
#
# Key Responsibilities:
#
# 1. Text-to-Embedding Conversion
#    - Converts text into dense numerical vectors using the configured
#      Sentence Transformer model.
#    - These vectors capture the semantic meaning of the input text and can
#      later be used for similarity search and Retrieval-Augmented Generation.
#
# 2. Shared Embedder for Multiple Data Sources
#    - The same embedding model is used for both PDF document chunks and
#      video transcript chunks.
#    - Using a single model keeps all generated embeddings within the same
#      semantic embedding space.
#
# 3. Singleton Model Instance
#    - The embedding model is loaded only once when it is first requested.
#    - The loaded instance is stored in memory and reused for all subsequent
#      requests throughout the application lifecycle.
#    - This prevents the model from being loaded repeatedly for every request,
#      reducing unnecessary startup time and memory consumption.
#
# 4. Automatic Model Download and Local Caching
#    - If the configured model is not available locally, Sentence Transformers
#      automatically downloads it when the model is loaded for the first time.
#    - After the initial download, the model is cached locally and reused for
#      future loads instead of being downloaded again.
#
# 5. Batch Embedding Generation
#    - Accepts multiple text chunks at once and generates an embedding vector
#      for each chunk.
#    - Batch processing makes the module suitable for both PDF ingestion and
#      video transcript processing pipelines.
#
# 6. Centralized Error Handling
#    - Validates the input before generating embeddings.
#    - Converts embedding-related failures into application-level
#      CustomHTTPException errors for consistent API error handling.
#
# =============================================================================

from sentence_transformers import SentenceTransformer

from app.server.config import config
from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier
from fastapi import status

# Store the embedding model instance here.
# The model is initialized only on the first call to get_embedding_model()
# and the same instance is reused for the lifetime of the application.
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """
    Returns the embedding model instance.
    Loads it once and reuses across all requests (singleton pattern).

    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.debug(f'Loading embedding model: {config.EMBEDDING_MODEL_NAME}')
        _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        logger.debug('Embedding model loaded successfully')
    return _embedding_model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts (list[str]): List of text chunks to embed.

    Returns:
        list[list[float]]: List of embedding vectors.
    """
    if not texts:
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='texts list cannot be empty for embedding generation',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        model = get_embedding_model()
        logger.debug(f'Generating embeddings for {len(texts)} chunks')
        embeddings = model.encode(texts, show_progress_bar=False)
        logger.debug('Embeddings generated successfully')
        return embeddings.tolist()
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to generate embeddings: {str(error)}',
            identifier=error_identifier.EMBEDDING_FAILED,
        ) from error