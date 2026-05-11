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
        "nightly-pipeline": {
            "task": "celery_tasks.tasks.run_scheduled_pipeline",
            "schedule": crontab(hour=0, minute=0),  # midnight UTC
        },
    },
)


@celery_app.task(name="celery_tasks.tasks.run_scheduled_pipeline", bind=True, max_retries=2)
def run_scheduled_pipeline(self):
    """
    Nightly scheduled run — triggers the pipeline by POSTing to the internal API.

    This avoids the asyncio.run() + Celery anti-pattern:
      - Celery workers run in a sync context
      - The pipeline uses async SQLAlchemy and async LLM clients
      - asyncio.run() inside Celery creates a new event loop per task, leaking DB connections
      - Posting to the API instead delegates async execution to the correct event loop
    """
    import io
    import csv
    import random
    from datetime import datetime, timedelta

    # Build a synthetic 90-day dataset
    rows = [["date", "description", "amount", "category"]]
    base = datetime.utcnow()
    random.seed(42)

    for i in range(90):
        day = (base - timedelta(days=i)).strftime("%Y-%m-%d")
        rows.append([day, "Monthly SaaS Revenue", round(random.uniform(8000, 12000), 2), "revenue"])
        rows.append([day, "AWS Infrastructure", round(-random.uniform(800, 1500), 2), "expense"])
        rows.append([day, "Staff Salaries", -8500.00, "expense"])
        if i % 7 == 0:
            rows.append([day, "Consulting Invoice", round(random.uniform(2000, 5000), 2), "revenue"])

    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    csv_bytes = buffer.getvalue().encode()

    try:
        response = requests.post(
            f"{API_BASE}/api/v1/run",
            files={"file": ("scheduled_run.csv", csv_bytes, "text/csv")},
            data={"file_type": "csv", "triggered_by": "schedule"},
            timeout=30,
        )
        response.raise_for_status()
        run_id = response.json().get("run_id", "unknown")
        logger.info("[CeleryBeat] Nightly pipeline triggered — run_id=%s", run_id)
        return {"status": "accepted", "run_id": run_id}

    except requests.RequestException as exc:
        logger.error("[CeleryBeat] Failed to trigger nightly pipeline: %s", exc)
        raise self.retry(exc=exc, countdown=300)  # retry after 5 min
