import asyncio

from celery_app import celery_app

from app.server.static.enums import SourceType
from app.server.config.source_config import SOURCE_CONFIG


@celery_app.task(bind=True, name="tasks.ingest")
def ingest_task(
    self,
    source_type: SourceType,
    url: str,
    title: str,
) -> dict:
    source_type = SourceType(source_type)
 
    config = SOURCE_CONFIG.get(source_type)
    if not config:
        raise ValueError(f"Unsupported source type: {source_type}")
 
    self.update_state(
        state="STARTED",
        meta={"status": f"{source_type.value.capitalize()} ingestion started"},
    )
 
    return asyncio.run(config.handler(url=url, title=title))