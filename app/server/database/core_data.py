from typing import Any, Optional

from fastapi import status

from app.server.database.db import chroma_client
from app.server.handler.error_handler import CustomHTTPException
from app.server.static import error_identifier


def get_collection(collection_name: str):
    """
    Get or create a ChromaDB collection by name.

    Args:
        collection_name (str): The name of the collection.

    Returns:
        chromadb.Collection: The ChromaDB collection object.
    """
    return chroma_client.get_or_create_collection(name=collection_name)


def add_documents(
    collection_name: str,
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
    ids: list[str],
) -> dict[str, Any]:
    """
    Add documents with embeddings to a ChromaDB collection.

    Args:
        collection_name (str): The name of the collection.
        documents (list[str]): The list of document texts.
        embeddings (list[list[float]]): The list of embeddings for each document.
        metadatas (list[dict[str, Any]]): The list of metadata for each document.
        ids (list[str]): The list of unique IDs for each document.

    Returns:
        dict[str, Any]: A dictionary with the count of added documents.
    """
    if not documents or not embeddings or not ids:
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'{collection_name}: documents, embeddings and ids cannot be empty',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        collection = get_collection(collection_name)
        BATCH_SIZE = 5000
 
        total = len(ids)
        
        if total <= BATCH_SIZE:
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
        else:
            # Split into batches
            for start in range(0, total, BATCH_SIZE):
                end = min(start + BATCH_SIZE, total)
                collection.add(
                    documents=documents[start:end],
                    embeddings=embeddings[start:end],
                    metadatas=metadatas[start:end],
                    ids=ids[start:end],
                )
 
        return {'added_count': total}
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{collection_name}: Failed to add documents — {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error


def query_documents(
    collection_name: str,
    query_embeddings: list[list[float]],
    n_results: int = 5,
    where: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Query a ChromaDB collection using embeddings (semantic search).

    Args:
        collection_name (str): The name of the collection.
        query_embeddings (list[list[float]]): The query embeddings.
        n_results (int): Number of results to return. Defaults to 5.
        where (dict, optional): Metadata filter. Defaults to None.

    Returns:
        dict[str, Any]: The query results containing documents, metadatas, and distances.
    """
    if not query_embeddings:
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'{collection_name}: query_embeddings cannot be empty',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        collection = get_collection(collection_name)
        kwargs = {'query_embeddings': query_embeddings, 'n_results': n_results}
        if where:
            kwargs['where'] = where
        results = collection.query(**kwargs)
        return results
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{collection_name}: Failed to query documents — {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error

def get_metadatas_by_filter(
    collection_name: str,
    where: Optional[dict[str, Any]] = None,
    limit: Optional[int] = None,
    batch_size: int = 1000,
) -> list[dict[str, Any]]:
    """
    Fetch only the metadata (no documents, no embeddings) of chunks in a collection.
    Reads in batches so a big collection does not hit the SQLite variable limit.

    Args:
        collection_name (str): The name of the collection.
        where (dict, optional): Metadata filter. None means the whole collection.
        limit (int, optional): Stop after this many records. None means everything.
        batch_size (int): Records fetched per round trip.

    Returns:
        list[dict[str, Any]]: One metadata dict per chunk.
    """
    try:
        collection = get_collection(collection_name)
        metadatas: list[dict[str, Any]] = []
        offset = 0

        while True:
            batch_limit = batch_size if limit is None else min(batch_size, limit - len(metadatas))
            if batch_limit <= 0:
                break

            kwargs: dict[str, Any] = {'include': ['metadatas'], 'limit': batch_limit, 'offset': offset}
            if where:
                kwargs['where'] = where

            batch = collection.get(**kwargs)['metadatas'] or []
            if not batch:
                break

            metadatas.extend(batch)
            if len(batch) < batch_limit:
                break
            offset += len(batch)

        return metadatas
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{collection_name}: Failed to read metadata — {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error


def delete_documents_by_filter(collection_name: str, where: dict) -> dict[str, Any]:
    """
    Delete documents from ChromaDB by metadata filter.
    """
    try:
        collection = get_collection(collection_name)

        results = collection.get(where=where, include=[])
        ids = results['ids']
        if not ids:
            return {'deleted_count': 0}

        collection.delete(ids=ids)
        return {'deleted_count': len(ids)}
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{collection_name}: Failed to delete by filter — {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error