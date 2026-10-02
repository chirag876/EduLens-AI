# =============================================================================
# Ingested Document Service
# =============================================================================
#
# ChromaDB stores chunks, not documents. This module rebuilds the "document"
# view (one row per ingested PDF/video) by grouping chunk metadata, and also
# deletes a whole document by its doc_id.

from typing import Any, Optional

from app.server.config.source_config import SOURCE_CONFIG
from app.server.database import core_data as db
from app.server.static.enums import SourceType


def list_documents(source_type: Optional[SourceType] = None) -> list[dict[str, Any]]:
    """
    Group chunks into documents. Newest ingested first; documents ingested before
    doc_id/ingested_at existed (legacy) come last with those fields as None.
    """
    documents: dict[tuple, dict[str, Any]] = {}

    for current_type, config in SOURCE_CONFIG.items():
        if source_type and current_type != source_type:
            continue

        for meta in db.get_metadatas_by_filter(config.collection):
            doc_id = meta.get('doc_id')
            key = (current_type.value, doc_id) if doc_id else (current_type.value, meta.get('title'), meta.get('url'))

            doc = documents.get(key)
            if doc is None:
                doc = documents[key] = {
                    'doc_id': doc_id,
                    'source_type': current_type.value,
                    'title': meta.get('title'),
                    'url': meta.get('url'),
                    'ingested_at': meta.get('ingested_at'),
                    'total_chunks': 0,
                    '_pages': set(),
                }

            doc['total_chunks'] += 1
            if meta.get('page_number') is not None:
                doc['_pages'].add(meta['page_number'])

    result = []
    for doc in documents.values():
        pages = doc.pop('_pages')
        doc['total_embeddings'] = doc['total_chunks']  # Chroma keeps exactly 1 vector per chunk
        doc['total_pages'] = len(pages) if pages else None
        result.append(doc)

    # Two stable sorts: title A-Z first, then ingested_at newest first (None goes last)
    result.sort(key=lambda d: d['title'] or '')
    result.sort(key=lambda d: d['ingested_at'] or '', reverse=True)
    return result


def delete_document(doc_id: str) -> dict[str, int]:
    """Delete every chunk of one document. doc_id is unique, so no source_type is needed."""
    deleted: dict[str, int] = {}
    for current_type, config in SOURCE_CONFIG.items():
        result = db.delete_documents_by_filter(
            collection_name=config.collection,
            where={'doc_id': doc_id},
        )
        deleted[current_type.value] = result['deleted_count']
    return deleted