import asyncio

from celery_app import celery_app

from app.server.ingestion.pdf_ingestion import ingest_pdf
from app.server.ingestion.video_ingestion import ingest_video
from app.server.static.enums import SourceType


INGESTION_HANDLERS = {
    SourceType.PDF: ingest_pdf,
    SourceType.VIDEO: ingest_video,
}


@celery_app.task(bind=True, name="tasks.ingest")
def ingest_task(
    self,
    source_type: SourceType,
    url: str,
    title: str,
) -> dict:

    try:
        source_type = SourceType(source_type)

        handler = INGESTION_HANDLERS.get(source_type)

        if not handler:
            raise ValueError(
                f"Unsupported source type: {source_type}"
            )

        self.update_state(
            state="STARTED",
            meta={
                "status": f"{source_type.value.capitalize()} ingestion started"
            },
        )

        result = asyncio.run(
            handler(
                url=url,
                title=title,
            )
        )

        return result

    except Exception:
        raise