from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create the Celery app
# broker = Redis (stores the task queue)
# backend = Redis (stores task results)
celery_app = Celery(
    "security_copilot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.sync_tasks"],  # where our tasks live
)

# Celery configuration
celery_app.conf.update(
    # Serialize tasks as JSON (safe, readable)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # How often to retry a failed task
    task_max_retries=3,
    task_retry_backoff=True,  # wait longer between each retry

    # Beat schedule — runs tasks on a schedule (like cron)
    beat_schedule={
        "sync-aws-security-hub-daily": {
            "task": "app.tasks.sync_tasks.sync_all_assessments",
            "schedule": crontab(hour=0, minute=0),  # runs at midnight UTC every day
        },
    },
)