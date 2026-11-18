from celery import Celery

# Redis connection used by Celery.
REDIS_URL = "redis://localhost:6379/0"

# Create the Celery application.
celery_app = Celery(
    "meetiq",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.worker.tasks"],
)

# Configure how Celery handles tasks.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
celery_app.conf.beat_schedule = {
    "recover-stuck-queued-meetings": {
        "task": "meetiq.recover_queued",
        "schedule": 60.0,
    },
}
