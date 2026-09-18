# =============================================================================
# Retrieval Module
# =============================================================================
#
# This module is responsible for retrieving the most relevant content chunks
# from the vector database based on a student's question.
#
# The student's question is converted into an embedding and searched against
# both PDF and video transcript collections using semantic search.

from app.server.database import core_data as db
from app.server.embeddings.embedder import generate_embeddings
from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static.collections import Collections
from app.server.static import error_identifier
from app.server.static.enums import SourceType
from app.server.utils.query_utils import build_where_filter
from fastapi import status

# Number of results to retrieve from each collection
TOP_K = 5


def retrieve_relevant_chunks(question: str, source_type: str = None) -> list[dict]:
    """
    Retrieve relevant content chunks from ChromaDB using semantic search.
    Searches both PDF and Video collections and merges results.

    Args:
        question (str): The student's question.
        source_type (str, optional): Filter by 'pdf' or 'video'.
                                     If None, searches both collections.

    Returns:
        list[dict]: List of relevant chunks with text, metadata, and score.
    """
    if not question or not question.strip():
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Question cannot be empty for retrieval',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        # Step 1: Generate embedding for the question
        logger.debug(f'Generating embedding for question: {question[:80]}...')
        query_embeddings = generate_embeddings([question])

        results = []

        # Step 2: Search PDF collection
        if source_type is None or source_type == SourceType.PDF:
            pdf_results = _search_collection(
                collection_name=Collections.PDF_CHUNKS,
                query_embeddings=query_embeddings,
                where=build_where_filter(SourceType.PDF),
            )
            results.extend(pdf_results)

        # Step 3: Search Video collection
        if source_type is None or source_type == SourceType.VIDEO:
            video_results = _search_collection(
                collection_name=Collections.VIDEO_CHUNKS,
                query_embeddings=query_embeddings,
                where=build_where_filter(SourceType.VIDEO),
            )
            results.extend(video_results)

        # Step 4: Sort merged results by distance (lower = more relevant)
        results.sort(key=lambda x: x['distance'])

        logger.debug(f'Retrieved {len(results)} total chunks for question')
        return results

    except CustomHTTPException:
        raise
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to retrieve relevant chunks: {str(error)}',
            identifier=error_identifier.RETRIEVAL_FAILED,
        ) from error


def _search_collection(collection_name: str, query_embeddings: list, where: dict = None) -> list[dict]:
    """
    Search a single ChromaDB collection and format results.

    Args:
        collection_name (str): ChromaDB collection to search.
        query_embeddings (list): Query embedding vectors.
        where (dict, optional): Metadata filter.

    Returns:
        list[dict]: Formatted search results.
    """
    try:
        raw_results = db.query_documents(
            collection_name=collection_name,
            query_embeddings=query_embeddings,
            n_results=TOP_K,
            where=where,
        )

        formatted = []
        documents = raw_results.get('documents', [[]])[0]
        metadatas = raw_results.get('metadatas', [[]])[0]
        distances = raw_results.get('distances', [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            formatted.append({
                'text': doc,
                'metadata': meta,
                'distance': dist,
            })

        return formatted

    except Exception:
        # If collection is empty or doesn't exist yet, return empty list
        logger.debug(f'No results from collection: {collection_name}')
        return []