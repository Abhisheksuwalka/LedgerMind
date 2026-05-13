"""
Celery task queue — scheduled nightly pipeline execution.
Schedule: runs the full pipeline daily at midnight UTC.

Anti-pattern avoided: we do NOT use asyncio.run() inside Celery.
Instead the scheduled task posts an HTTP request to the API's /run endpoint,
which handles the async pipeline correctly via asyncio.create_task.
"""

import logging
import os

import requests
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger("celery_tasks")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
API_BASE = os.getenv("INTERNAL_API_URL", "http://backend:8000")
INTERNAL_API_SECRET = os.getenv("INTERNAL_API_SECRET", "").strip()


def _internal_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if INTERNAL_API_SECRET:
        headers["X-Internal-Secret"] = INTERNAL_API_SECRET
    return headers

celery_app = Celery(
    "ledgermind",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "nightly-delta": {
            "task": "celery_tasks.tasks.nightly_delta_check",
            "schedule": crontab(hour=0, minute=0),  # midnight UTC
        },
        "weekly-digest": {
            "task": "celery_tasks.tasks.weekly_digest",
            "schedule": crontab(day_of_week=1, hour=8, minute=0),  # Monday 8am UTC
        },
    },
)


@celery_app.task(name="celery_tasks.tasks.nightly_delta_check", bind=True, max_retries=2)
def nightly_delta_check(self):
    """
    Nightly scheduled run — triggers the nightly-delta endpoint to calculate alerts.
    """
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/internal/nightly-delta",
            headers=_internal_headers(),
            timeout=60,
        )
        response.raise_for_status()
        logger.info("[CeleryBeat] Nightly delta check triggered successfully: %s", response.json())
        return response.json()
    except requests.RequestException as exc:
        logger.error("[CeleryBeat] Failed to trigger nightly delta check: %s", exc)
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(name="celery_tasks.tasks.weekly_digest", bind=True, max_retries=2)
def weekly_digest(self):
    """
    Weekly scheduled run — triggers the weekly-digest endpoint to generate LLM summary.
    """
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/internal/weekly-digest",
            headers=_internal_headers(),
            timeout=120,
        )
        response.raise_for_status()
        logger.info("[CeleryBeat] Weekly digest triggered successfully: %s", response.json())
        return response.json()
    except requests.RequestException as exc:
        logger.error("[CeleryBeat] Failed to trigger weekly digest: %s", exc)
        raise self.retry(exc=exc, countdown=300)
