"""
APScheduler glue (docs/next.md §2.4)
--------------------------------------
Runs live-sync jobs on a cadence inside the API process (or standalone later).

Cadence:
    MyScheme          every 6–12 h   (catalog data — changes weekly at most)
    Karnataka SSP     every 2–4 h    (deadlines are time-critical)

All intervals are configurable via .env (``MYSCHEME_POLL_INTERVAL_MIN``,
``SSP_POLL_INTERVAL_MIN``) and the scheduler is **disabled by default** in dev
— opt in with ``LIVE_SYNC_ENABLED=true``.
"""

import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Source -> default poll interval in minutes.
DEFAULT_INTERVALS = {
    "myscheme": 360,
    "karnataka_ssp": 240,
}


def live_sync_enabled() -> bool:
    return os.getenv("LIVE_SYNC_ENABLED", "false").strip().lower() == "true"


def _interval_minutes(source: str) -> int:
    env_name = f"{source.upper()}_POLL_INTERVAL_MIN"
    try:
        return max(1, int(os.getenv(env_name, DEFAULT_INTERVALS.get(source, 360))))
    except (TypeError, ValueError):
        return DEFAULT_INTERVALS.get(source, 360)


class SyncScheduler:
    """BackgroundScheduler wrapper that runs live-sync jobs in-process."""

    def __init__(self):
        self._scheduler = BackgroundScheduler(daemon=True)
        self._started = False

    def start(self) -> bool:
        """Register and start the sync jobs. No-op unless LIVE_SYNC_ENABLED=true."""
        if self._started:
            return False
        if not live_sync_enabled():
            logger.info(
                "LIVE_SYNC_ENABLED is not true — live-sync scheduler not started"
            )
            return False

        from ingestion.pipelines.live_sync_pipeline import LiveSyncPipeline

        pipeline = LiveSyncPipeline()

        for source in DEFAULT_INTERVALS:
            self._scheduler.add_job(
                pipeline.run,
                trigger=IntervalTrigger(minutes=_interval_minutes(source)),
                kwargs={"sources": [source]},
                id=f"live-sync:{source}",
                name=f"Live sync: {source}",
                replace_existing=True,
                coalesce=True,
                max_instances=1,
            )

        self._scheduler.start()
        self._started = True
        logger.info(
            "Live-sync scheduler started with jobs: %s", list(DEFAULT_INTERVALS)
        )
        return True

    def stop(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False


# Module-level singleton the API lifespan can start/stop.
scheduler = SyncScheduler()
