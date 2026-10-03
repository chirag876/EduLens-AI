"""
One-time script: give doc_id to chunks that were ingested BEFORE doc_id existed.

Chunks of the same (title, url) inside one collection get the same new doc_id.
ingested_at is NOT invented — old documents keep it empty (we truly don't know it).
Safe to run more than once: chunks that already have a doc_id are skipped.

Run from the project root:
    python -m scripts.backfill_doc_ids
"""
import uuid

from app.server.config.source_config import SOURCE_CONFIG
from app.server.database import core_data as db

READ_BATCH = 1000
WRITE_BATCH = 5000


def backfill() -> None:
    for source_type, config in SOURCE_CONFIG.items():
        collection = db.get_collection(config.collection)

        records = []
        offset = 0
        while True:
            res = collection.get(include=['metadatas'], limit=READ_BATCH, offset=offset)
            if not res['ids']:
                break
            records.extend(zip(res['ids'], res['metadatas']))
            offset += len(res['ids'])
            if len(res['ids']) < READ_BATCH:
                break

        doc_ids: dict[tuple, str] = {}
        update_ids, update_metas = [], []
        for chunk_id, meta in records:
            if meta.get('doc_id'):
                continue
            key = (meta.get('title'), meta.get('url'))
            doc_id = doc_ids.setdefault(key, str(uuid.uuid4()))
            update_ids.append(chunk_id)
            update_metas.append({**meta, 'doc_id': doc_id})  # full metadata, nothing lost

        for start in range(0, len(update_ids), WRITE_BATCH):
            collection.update(
                ids=update_ids[start:start + WRITE_BATCH],
                metadatas=update_metas[start:start + WRITE_BATCH],
            )

        print(f'[{source_type.value}] {len(doc_ids)} documents, {len(update_ids)} chunks updated')


if __name__ == '__main__':
    backfill()