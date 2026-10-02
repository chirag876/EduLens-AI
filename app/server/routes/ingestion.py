from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate

from app.server.config.source_config import SOURCE_CONFIG
from app.server.ingestion.duplicate_check import find_duplicate
from app.server.models.ingestion_model import IngestedDocument, IngestionRequest
from app.server.services import document_service
from app.server.services.tasks.ingestion_task import ingest_task
from app.server.static.enums import SourceType

router = APIRouter()


# Plain `def` (not `async def`) on the routes that call ChromaDB: Chroma is a
# blocking library, FastAPI runs `def` routes in a threadpool so the event loop stays free.
@router.post('/ingest', summary='Ingest a source into the curriculum')
def ingest_route(params: IngestionRequest) -> dict[str, Any]:
    config = SOURCE_CONFIG.get(params.source_type)
    if not config:
        raise HTTPException(
            status_code=400,
            detail=f'Unsupported source type: {params.source_type.value}',
        )

    # Same title or same url within this source type -> reject before queueing
    duplicate = find_duplicate(config.collection, params.title, str(params.url))
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A {params.source_type.value.upper()} with the same {duplicate['reason']} "
                f"is already ingested (title: '{duplicate['title']}', doc_id: {duplicate['doc_id']})"
            ),
        )

    task = ingest_task.delay(
        source_type=params.source_type,
        url=str(params.url),
        title=params.title,
    )
    return {
        'job_id': task.id,
        'status': 'queued',
        'message': f'{params.source_type.value.capitalize()} ingestion started for: {params.title}',
    }


@router.get('/ingest', summary='List ingested documents (paginated)')
def list_route(source_type: Optional[SourceType] = None) -> Page[IngestedDocument]:
    return paginate(document_service.list_documents(source_type))


@router.get('/ingest/status/{job_id}', summary='Check ingestion job status')
async def get_job_status(job_id: str) -> dict[str, Any]:
    from celery_app import celery_app
    task = celery_app.AsyncResult(job_id)

    if task.state == 'PENDING':
        return {'job_id': job_id, 'status': 'pending', 'message': 'Job is waiting in queue'}

    elif task.state == 'STARTED':
        return {'job_id': job_id, 'status': 'processing', 'message': task.info.get('status', '')}

    elif task.state == 'SUCCESS':
        return {'job_id': job_id, 'status': 'completed', 'result': task.result}

    elif task.state == 'FAILURE':
        return {'job_id': job_id, 'status': 'failed', 'error': str(task.info)}

    return {'job_id': job_id, 'status': task.state}


@router.delete('/ingest', summary='Delete an ingested document by doc_id')
def delete_route(doc_id: str) -> dict[str, Any]:
    deleted = document_service.delete_document(doc_id)
    total = sum(deleted.values())

    if total == 0:
        raise HTTPException(status_code=404, detail=f'No document found with doc_id: {doc_id}')

    return {
        'doc_id': doc_id,
        'deleted_chunks': total,
        'deleted_by_source': deleted,
        'message': 'Deleted successfully',
    }