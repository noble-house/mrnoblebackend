from celery import Celery
from .config import settings
from .services.logger import get_logger

logger = get_logger("celery")

# Create Celery instance
celery_app = Celery(
    "mrnoble",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.ai_tasks.*": {"queue": "ai"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
    },
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "email": {
            "exchange": "email",
            "routing_key": "email",
        },
        "ai": {
            "exchange": "ai",
            "routing_key": "ai",
        },
        "analytics": {
            "exchange": "analytics",
            "routing_key": "analytics",
        },
    }
)

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"
