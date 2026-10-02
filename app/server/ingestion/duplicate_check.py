# =============================================================================
# Duplicate Check
# =============================================================================
#
# Single place that decides whether a source is already ingested.
# Used by the route (fast 409 before queueing) and by the ingestion handlers
# (safety net, in case two identical requests were queued together).
#
# Rule (per collection, i.e. per source type):
#   - same title  -> duplicate
#   - same url    -> duplicate (same file ingested again under a different title)
# The same title in a different source type (pdf vs video) is allowed.

from typing import Any, Optional

from app.server.database import core_data as db


def find_duplicate(collection_name: str, title: str, url: str) -> Optional[dict[str, Any]]:
    """
    Returns None if the source is new, otherwise a dict describing the clash:
    {'reason': 'title' | 'url', 'title': ..., 'url': ..., 'doc_id': ...}
    """
    matches = db.get_metadatas_by_filter(
        collection_name=collection_name,
        where={'$or': [{'title': title}, {'url': url}]},
        limit=1,
    )
    if not matches:
        return None

    existing = matches[0]
    return {
        'reason': 'title' if existing.get('title') == title else 'url',
        'title': existing.get('title'),
        'url': existing.get('url'),
        'doc_id': existing.get('doc_id'),
    }