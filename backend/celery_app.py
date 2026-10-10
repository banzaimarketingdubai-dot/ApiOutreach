from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "revo_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.scraping_tasks",
        "app.workers.enrichment_tasks",
        "app.workers.outreach_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=2,
    worker_max_tasks_per_child=50
)

# Celery Beat Schedule
from celery.schedules import crontab
celery_app.conf.beat_schedule = {
    'process-outreach-queue-every-5-minutes': {
        'task': 'app.workers.outreach_tasks.process_outreach_queue',
        'schedule': crontab(minute='*/5'),
    },
}
