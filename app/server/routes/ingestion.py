from typing import Any

from fastapi import APIRouter, HTTPException
from app.server.database import core_data as db
from app.server.models.ingestion_model import IngestionRequest
from app.server.services.tasks.ingestion_task import ingest_task
from app.server.config.source_config import SOURCE_CONFIG
router = APIRouter()


@router.post('/ingest', summary='Ingest a source into the curriculum')
async def ingest_route(params: IngestionRequest) -> dict[str, Any]:
    if params.source_type not in SOURCE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f'Unsupported source type: {params.source_type.value}',
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


@router.delete('/ingest', summary='Delete an ingested source from curriculum')
async def delete_route(title: str) -> dict[str, Any]:
    deleted: dict[str, int] = {}
    for source_type, config in SOURCE_CONFIG.items():
        result = db.delete_documents_by_filter(
            collection_name=config.collection,
            where={'title': title},
        )
        deleted[source_type.value] = result['deleted_count']
 
    return {
        'title': title,
        'deleted_chunks': sum(deleted.values()),
        'deleted_by_source': deleted,
        'message': 'Deleted successfully',
    }
 