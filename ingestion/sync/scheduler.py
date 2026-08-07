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

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Source -> default poll interval in minutes.
DEFAULT_INTERVALS = {
    "myscheme": 360,
    "karnataka_ssp": 240,
}

# Delay before a catch-up sync fires on startup (lets the API come up first).
CATCH_UP_DELAY_SECONDS = 30


def live_sync_enabled() -> bool:
    return os.getenv("LIVE_SYNC_ENABLED", "false").strip().lower() == "true"


def _interval_minutes(source: str) -> int:
    env_name = f"{source.upper()}_POLL_INTERVAL_MIN"
    try:
        return max(1, int(os.getenv(env_name, DEFAULT_INTERVALS.get(source, 360))))
    except (TypeError, ValueError):
        return DEFAULT_INTERVALS.get(source, 360)


def _last_snapshot_time(source: str):
    """UTC datetime of the last RawStore snapshot for a source, or None."""
    root = os.getenv("RAW_DATA_ROOT", "data/raw")
    pointer = os.path.join(root, source, "latest.json")
    try:
        with open(pointer) as f:
            meta = json.load(f)
        return datetime.strptime(
            meta["timestamp"], "%Y%m%dT%H%M%SZ"
        ).replace(tzinfo=timezone.utc)
    except (OSError, ValueError, KeyError):
        return None


def _needs_catch_up(source: str) -> bool:
    """True when the last snapshot is missing or older than one poll interval.

    This makes the first sync land minutes after startup on a stale DB while
    skipping the burst entirely when a dev server restarts shortly after a
    successful sync (no repeated 48-request fetches during ``--reload``).
    """
    last = _last_snapshot_time(source)
    if last is None:
        return True
    age_minutes = (datetime.now(timezone.utc) - last).total_seconds() / 60
    return age_minutes > _interval_minutes(source)


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
            # Catch-up pass so a stale DB is refreshed shortly after startup
            # instead of waiting a full poll interval.
            if _needs_catch_up(source):
                self._scheduler.add_job(
                    pipeline.run,
                    trigger=DateTrigger(
                        run_date=datetime.now()
                        + timedelta(seconds=CATCH_UP_DELAY_SECONDS)
                    ),
                    kwargs={"sources": [source]},
                    id=f"live-sync:{source}:catchup",
                    name=f"Live sync catch-up: {source}",
                    replace_existing=True,
                    coalesce=True,
                    max_instances=1,
                )
                logger.info(
                    "[%s] last snapshot is stale — scheduling catch-up sync",
                    source,
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
