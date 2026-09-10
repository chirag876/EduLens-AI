def build_where_filter(source_type: str = None) -> dict | None:
    """
    Build ChromaDB where filter for metadata filtering.

    Args:
        source_type (str): 'pdf' or 'video'. If None, returns None (no filter).

    Returns:
        dict | None: ChromaDB where filter or None.
    """
    if source_type:
        return {'source_type': source_type}
    return None