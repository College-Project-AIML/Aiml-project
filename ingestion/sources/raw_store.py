"""
Raw Snapshot Store
--------------------
Purpose:
- Persist immutable raw connector output to ``data/raw/{source}/{timestamp}/``
- Track a ``latest`` pointer so connectors can degrade gracefully to the
  last successful snapshot when a portal blocks or fails
- Emit a tiny ``manifest.json`` per snapshot for the audit trail

Output contract (docs/next.md §1.4):
    data/raw/{source}/{timestamp}/schemes.json
    data/raw/{source}/{timestamp}/notices.json     # SSP only
    data/raw/{source}/{timestamp}/manifest.json
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

RAW_DATA_ROOT = os.getenv("RAW_DATA_ROOT", "data/raw")


class RawStore:
    """Immutable raw-data snapshot store for a single source."""

    def __init__(self, source: str):
        self.source = source

    # ------------------------------------------------------------------ write

    def write(
        self,
        *,
        schemes: Optional[List[Dict]] = None,
        notices: Optional[List[Dict]] = None,
        status: str = "ok",
        extra: Optional[Dict] = None,
    ) -> str:
        """Write one immutable snapshot and refresh the ``latest`` pointer.

        Returns the snapshot directory path.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snapshot_dir = os.path.join(RAW_DATA_ROOT, self.source, timestamp)
        os.makedirs(snapshot_dir, exist_ok=True)

        if schemes is not None:
            self._dump(os.path.join(snapshot_dir, "schemes.json"), schemes)
        if notices is not None:
            self._dump(os.path.join(snapshot_dir, "notices.json"), notices)

        manifest = {
            "source": self.source,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "scheme_count": len(schemes) if schemes is not None else None,
            "notice_count": len(notices) if notices is not None else None,
        }
        if extra:
            manifest.update(extra)
        self._dump(os.path.join(snapshot_dir, "manifest.json"), manifest)

        with open(os.path.join(RAW_DATA_ROOT, self.source, "latest.json"), "w") as f:
            json.dump({"timestamp": timestamp, "dir": snapshot_dir}, f)

        logger.info("RawStore[%s] snapshot %s (%s)", self.source, timestamp, status)
        return snapshot_dir

    # ------------------------------------------------------------------ read

    def latest(self) -> Optional[Dict]:
        """Return the most recent snapshot payloads, or None on a cold start."""
        pointer = os.path.join(RAW_DATA_ROOT, self.source, "latest.json")
        if not os.path.exists(pointer):
            return None
        try:
            with open(pointer) as f:
                meta = json.load(f)
        except (ValueError, OSError):
            return None

        snapshot_dir = meta.get("dir")
        if not snapshot_dir or not os.path.isdir(snapshot_dir):
            return None

        payload: Dict = {}
        schemes_path = os.path.join(snapshot_dir, "schemes.json")
        if os.path.exists(schemes_path):
            payload["schemes"] = self._read(schemes_path)
        notices_path = os.path.join(snapshot_dir, "notices.json")
        if os.path.exists(notices_path):
            payload["notices"] = self._read(notices_path)
        return payload or None

    def latest_schemes(self) -> List[Dict]:
        latest = self.latest()
        return (latest or {}).get("schemes", [])

    # ---------------------------------------------------------------- helpers

    def _dump(self, path: str, data) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _read(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
