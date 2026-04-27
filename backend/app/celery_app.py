from __future__ import annotations

from celery import Celery

from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CELERY_TASK_ALWAYS_EAGER

celery_app = Celery('wisdom_tooth_ai', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.update(
    task_ignore_result=True,
    task_always_eager=CELERY_TASK_ALWAYS_EAGER,
    broker_connection_retry_on_startup=True,
)
celery_app.autodiscover_tasks(['app'])
