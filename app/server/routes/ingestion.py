from typing import Any

from fastapi import APIRouter
from app.server.database import core_data as db
from app.server.ingestion.pdf_ingestion import ingest_pdf
from app.server.ingestion.video_ingestion import ingest_video
from app.server.models.ingestion_model import IngestionResponse, PDFIngestionRequest, VideoIngestionRequest
from app.server.static.collections import Collections
router = APIRouter()


@router.post('/ingest/pdf', summary='Ingest a PDF document into the curriculum', response_model=IngestionResponse)
async def ingest_pdf_route(params: PDFIngestionRequest) -> dict[str, Any]:
    data = await ingest_pdf(url=str(params.url), title=params.title)
    return data


@router.post('/ingest/video', summary='Ingest a video into the curriculum', response_model=IngestionResponse)
async def ingest_video_route(params: VideoIngestionRequest) -> dict[str, Any]:
    data = await ingest_video(url=str(params.url), title=params.title)
    return data


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
