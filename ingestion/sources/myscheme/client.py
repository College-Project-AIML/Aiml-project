"""
MyScheme connector — HTTP client
----------------------------------
The MyScheme portal (myscheme.gov.in) serves its React SPA from an internal,
**undocumented** JSON API. Endpoint paths change over time, so the API URL is
configurable via the ``MYSCHEME_API_URL`` environment variable.

Behaviour (docs/next.md §1.2):
- Polite polling: modest User-Agent, retries with backoff, per-domain rate limit
  (default 1 request / 2 s) — this is a government production site.
- Paginates defensively (``page`` param) while the response signals more data.
- On failure, degrades to the last successful snapshot in ``data/raw/myscheme/``,
  falling back to bundled sample records on a cold start — never hammering the portal.

Hardcoded endpoint discovery is intentionally avoided: capture the real endpoint
from the site's DevTools network tab and set ``MYSCHEME_API_URL`` in .env.
"""

import logging
import os
import time
from typing import Dict, List, Tuple

import requests

from ingestion.sources.myscheme.parser import parse_schemes
from ingestion.sources.raw_store import RawStore

logger = logging.getLogger(__name__)

# Bundled sample records in the standard raw-record shape the normalizer consumes
# (used on a cold start when no API URL is configured and no snapshot exists yet).
SAMPLE_SCHEMES = [
    {
        "scheme_name": "PM Scholarship Scheme for Wards of Ex-Servicemen",
        "source": "myscheme.gov.in",
        "category": "scholarship",
        "ministry": "Ministry of Defence",
        "description": (
            "Scholarship for wards of ex-servicemen and ex-Coast Guard personnel "
            "pursuing professional degree courses."
        ),
        "eligibility": "Wards of ex-servicemen; minimum 60% in qualifying exam; family income criteria apply.",
        "state": "india",
        "link": "https://www.myscheme.gov.in/schemes/pm-scholarship-scheme-for-wards-of-ex-servicemen",
        "tags": ["defence", "scholarship"],
    },
    {
        "scheme_name": "National Scholarship Portal - Central Sector Scheme",
        "source": "myscheme.gov.in",
        "category": "scholarship",
        "ministry": "Ministry of Education",
        "description": (
            "Central Sector Scheme of Scholarships for college and university students "
            "with merit and means."
        ),
        "eligibility": "Students with 80%+ marks in previous exam; family income below 8 lakh per annum.",
        "state": "india",
        "link": "https://www.myscheme.gov.in/schemes/national-scholarship-portal-central-sector-scheme",
        "tags": ["merit", "scholarship", "nsp"],
    },
    {
        "scheme_name": "Vidyasiri Scholarship (Karnataka)",
        "source": "myscheme.gov.in",
        "category": "scholarship",
        "ministry": "Department of Higher Education, Karnataka",
        "description": (
            "Merit-cum-means scholarship for SC/ST/OBC students of Karnataka pursuing "
            "higher education."
        ),
        "eligibility": "Karnataka domicile; family income below 2.5 lakh per annum.",
        "state": "karnataka",
        "link": "https://www.myscheme.gov.in/schemes/vidyasiri-scholarship-karnataka",
        "tags": ["karnataka", "sc", "st", "obc", "scholarship"],
    },
]


class MySchemeClient:
    """Fetch scheme records from the MyScheme portal's internal JSON API."""

    def __init__(
        self,
        api_url: str = "",
        api_key: str = "",
        rate_limit_seconds: float = 2.0,
        timeout: int = 20,
    ):
        self.api_url = api_url or os.getenv("MYSCHEME_API_URL", "").strip()
        self.api_key = api_key or os.getenv("MYSCHEME_API_KEY", "").strip()
        self.rate_limit = float(
            rate_limit_seconds
            or os.getenv("MYSCHEME_RATE_LIMIT_SECONDS", "2")
        )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Aiml-project-schemes-ingestion/1.0 (+polite polling, contact: project)",
                "Accept": "application/json",
            }
        )
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    # ------------------------------------------------------------- public API

    def fetch_schemes(self) -> Tuple[List[Dict], str]:
        """Return (records, status) where status is ok | degraded | sample."""
        if not self.api_url:
            logger.warning(
                "MYSCHEME_API_URL not configured — returning bundled sample records"
            )
            return list(SAMPLE_SCHEMES), "sample"

        try:
            payload = self._fetch_paginated()
            records = parse_schemes(payload)
            RawStore("myscheme").write(schemes=records, status="ok")
            return records, "ok"
        except Exception as exc:  # noqa: BLE001 — degrade, never crash the pipeline
            logger.warning("MyScheme live fetch failed (%s); degrading gracefully", exc)
            last = RawStore("myscheme").latest_schemes()
            if last:
                RawStore("myscheme").write(
                    schemes=last, status="degraded", extra={"reason": str(exc)}
                )
                return last, "degraded"
            logger.warning("No previous MyScheme snapshot — using sample records")
            return list(SAMPLE_SCHEMES), "sample"

    # ------------------------------------------------------------ internals

    def _fetch_paginated(self) -> List[Dict]:
        """GET the configured endpoint, collecting schemes across pages.

        The API is undocumented and could return ``has_more`` forever — a hard
        page cap keeps us from hammering a government production site.
        """
        max_pages = int(os.getenv("MYSCHEME_MAX_PAGES", "100"))
        records: List[Dict] = []
        page = 1
        while True:
            resp = self.session.get(
                self.api_url,
                params={"page": page},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()

            batch = _extract_list(payload)
            records.extend(batch)

            if page >= max_pages:
                logger.warning(
                    "MyScheme pagination hit MAX_PAGES=%d; stopping", max_pages
                )
                break
            if not _has_more(payload, batch):
                break
            page += 1
            time.sleep(self.rate_limit)

        return records


# -------------------------------------------------------------- parsing utils


def _extract_list(payload) -> List[Dict]:
    """Defensively pull the record list out of an unknown response shape."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "schemes", "items", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = _extract_list(value)
                if nested:
                    return nested
    return []


def _has_more(payload, batch: List[Dict]) -> bool:
    """True if the response signals that more pages exist."""
    if isinstance(payload, dict):
        for key in ("has_more", "hasMore", "next"):
            if payload.get(key) in (True, "true", "True"):
                return True
        if payload.get("next"):
            return True
        if payload.get("total") and payload.get("page"):
            page_size = len(batch) or 1
            if int(payload["page"]) * page_size < int(payload["total"]):
                return True
    return False
