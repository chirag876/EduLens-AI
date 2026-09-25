import os
from celery import Celery

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    'edulens',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'app.server.services.tasks.ingestion_task'
    ]
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_track_started=True,
)