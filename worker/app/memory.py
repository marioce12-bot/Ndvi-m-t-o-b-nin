"""Small process-memory diagnostics for long-lived worker processes."""

from __future__ import annotations

import gc
import logging

import psutil

logger = logging.getLogger(__name__)
_PROCESS = psutil.Process()


def log_memory(step: str) -> None:
    """Log resident memory without retaining any pipeline objects."""
    rss_mb = _PROCESS.memory_info().rss / (1024 * 1024)
    logger.info("MEMORY step=%s rss_mb=%.1f", step, rss_mb)


def collect_memory(step: str) -> None:
    """Collect released Python objects and log the resulting RSS."""
    gc.collect()
    log_memory(step)
