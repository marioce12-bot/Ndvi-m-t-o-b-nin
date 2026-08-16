"""Native Render cron entry point for automatic pentade generation."""

from __future__ import annotations

import logging
import time
from datetime import date

from . import db
from .config import get_settings
from .main import GenerateRequest, _run_pipeline
from .pentades import list_available, pentade_for_date, pentade_label

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run() -> int:
    settings = get_settings()
    target = pentade_for_date(date.today(), settings.cron_safety_delay_days)
    if target is None:
        logger.info("Aucune pentade eligible aujourd'hui")
        return 0
    year = date.today().year
    pentade_id = f"{year}-P{target:02d}"
    label = pentade_label(year, target)
    available = next((item for item in list_available(settings.cron_product) if item["id"] == pentade_id), None)
    if not available:
        raise RuntimeError(f"COG/ZIP absent pour {pentade_id}")
    failures = 0
    for owner_id, email in db.list_users():
        request = GenerateRequest(jobId=f"auto-{settings.cron_product}-{pentade_id}-{owner_id}", pentadeId=pentade_id, product=settings.cron_product, email=email, ownerId=owner_id, force=True)
        last_error = "Echec inconnu"
        for attempt in range(1, max(1, settings.cron_retry_attempts) + 1):
            try:
                db.create_pending(request.jobId, request.product, request.pentadeId, label, request.email, request.ownerId)
                if _run_pipeline(request, label, str(available["url"]), notify_failure=attempt == settings.cron_retry_attempts):
                    break
            except Exception as error:
                last_error = str(error)
                logger.warning("Utilisateur %s, tentative %s/%s echouee: %s", owner_id, attempt, settings.cron_retry_attempts, error)
            if attempt < settings.cron_retry_attempts:
                time.sleep(max(1, settings.cron_retry_delay_hours) * 3600)
        else:
            failures += 1
            logger.error("Echec final pour %s: %s", email, last_error)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
