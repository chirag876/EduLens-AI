from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.server.ingestion.pdf_ingestion import ingest_pdf
from app.server.ingestion.video_ingestion import ingest_video
from app.server.static.collections import Collections
from app.server.static.enums import SourceType


@dataclass(frozen=True)
class SourceConfig:
    handler: Callable[..., Awaitable[dict[str, Any]]]
    collection: str


SOURCE_CONFIG: dict[SourceType, SourceConfig] = {
    SourceType.PDF: SourceConfig(handler=ingest_pdf, collection=Collections.PDF_CHUNKS),
    SourceType.VIDEO: SourceConfig(handler=ingest_video, collection=Collections.VIDEO_CHUNKS),
}

# Startup check: If you forget the configuration after adding value to the enum the app throws an error as soon it starts
assert set(SourceType) == set(SOURCE_CONFIG), (
    f'SOURCE_CONFIG missing: {set(SourceType) - set(SOURCE_CONFIG)}'
)