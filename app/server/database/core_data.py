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
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        return {'added_count': len(ids)}
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


def delete_documents(
    collection_name: str,
    ids: list[str],
) -> dict[str, Any]:
    """
    Delete documents from a ChromaDB collection by IDs.

    Args:
        collection_name (str): The name of the collection.
        ids (list[str]): The list of document IDs to delete.

    Returns:
        dict[str, Any]: A dictionary with the count of deleted documents.
    """
    if not ids:
        raise CustomHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'{collection_name}: ids cannot be empty',
            identifier=error_identifier.UNPROCESS_ENTITY,
        )

    try:
        collection = get_collection(collection_name)
        collection.delete(ids=ids)
        return {'deleted_count': len(ids)}
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{collection_name}: Failed to delete documents — {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error


def count_documents(collection_name: str) -> dict[str, Any]:
    """
    Count the number of documents in a ChromaDB collection.

    Args:
        collection_name (str): The name of the collection.

    Returns:
        dict[str, Any]: A dictionary with the document count.
    """
    try:
        collection = get_collection(collection_name)
        return {'count': collection.count()}
    except Exception as error:
        raise CustomHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{collection_name}: Failed to count documents — {str(error)}',
            identifier=error_identifier.INTERNAL_SERVER_ERROR,
        ) from error