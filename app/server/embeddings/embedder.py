# =============================================================================
# Embedding Module
# =============================================================================
#
# This module is responsible for converting text chunks into numerical
# embedding vectors using Sentence Transformers.

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
        embeddings = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
        logger.debug('Embeddings generated successfully')
        return embeddings.tolist()
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to generate embeddings: {str(error)}',
            identifier=error_identifier.EMBEDDING_FAILED,
        ) from error