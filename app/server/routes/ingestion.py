from typing import Any

from fastapi import APIRouter
from app.server.database import core_data as db
from app.server.models.ingestion_model import PDFIngestionRequest, VideoIngestionRequest
from app.server.static.collections import Collections
from app.server.services.tasks.ingestion_task import ingest_task
from app.server.static.enums import SourceType

router = APIRouter()


@router.post('/ingest/pdf', summary='Ingest a PDF document into the curriculum')
async def ingest_pdf_route(params: PDFIngestionRequest) -> dict[str, Any]:
    task = ingest_task.delay(
        source_type=SourceType.PDF,
        url=str(params.url),
        title=params.title
    )
    return {
        'job_id': task.id,
        'status': 'queued',
        'message': f'PDF ingestion started for: {params.title}',
    }


@router.post('/ingest/video', summary='Ingest a video into the curriculum')
async def ingest_video_route(params: VideoIngestionRequest) -> dict[str, Any]:
    task = ingest_task.delay(
        source_type=SourceType.VIDEO,
        url=str(params.url),
        title=params.title
    )
    return {
        'job_id': task.id,
        'status': 'queued',
        'message': f'Video ingestion started for: {params.title}',
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


@router.delete('/ingest/pdf', summary='Delete an ingested PDF from curriculum')
async def delete_pdf_route(title: str) -> dict[str, Any]:

    result = db.delete_documents_by_filter(
        collection_name=Collections.PDF_CHUNKS,
        where={'title': title}
    )
    return {
        'title': title,
        'deleted_chunks': result['deleted_count'],
        'message': 'Deleted successfully'
    }


@router.delete('/ingest/video', summary='Delete an ingested video from curriculum')
async def delete_video_route(title: str) -> dict[str, Any]:
    result = db.delete_documents_by_filter(
        collection_name=Collections.VIDEO_CHUNKS,
        where={'title': title}
    )
    return {
        'title': title,
        'deleted_chunks': result['deleted_count'],
        'message': 'Deleted successfully'
    }
