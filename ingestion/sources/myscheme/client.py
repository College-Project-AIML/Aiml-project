"""
MyScheme connector — HTTP client
----------------------------------
The MyScheme portal (myscheme.gov.in) serves its React SPA from an internal,
**undocumented** JSON API. The API endpoint and the public ``x-api-key`` are
embedded in the site's own JS bundles (they are sent by the public website on
every request), so the connector uses those by default. Both remain overridable
via ``MYSCHEME_API_URL`` / ``MYSCHEME_API_KEY`` in case the portal rotates them.

The ``x-api-key`` is a **public client key** — the site's own JS bundle sends it
for every visitor, so it is not a secret. It is hardcoded as a default for
convenience and can be overridden via ``MYSCHEME_API_KEY`` if the portal rotates it.

Discovered contract (verified 2026-08-07, 4,772 schemes):
    GET https://api.myscheme.gov.in/search/v6/schemes
        ?lang=en&q=&keyword=&sort=multiple_sort&from=0&size=100
    headers: { "x-api-key": "<public key from SPA bundle>" }
    → { status, data: { summary: { total }, hits: { items: [{id, fields}],
        page: { total, totalPages, pageNumber, from, size } }, facets } }

Behaviour (docs/next.md §1.2):
- Polite polling: modest User-Agent, per-domain rate limit
  (default 1 request / 2 s) — this is a government production site. Failures
  degrade to the last snapshot rather than retrying aggressively.
- Paginates via ``from``/``size`` while ``from < hits.page.total``, with a hard
  page cap so a misbehaving endpoint can never be hammered.
- On failure, degrades to the last successful snapshot in ``data/raw/myscheme/``,
  falling back to bundled sample records on a cold start — never hammering the portal.
"""

import logging
import os
import time
from typing import Dict, List, Tuple

import requests

from ingestion.sources.myscheme.parser import parse_schemes
from ingestion.sources.raw_store import RawStore

logger = logging.getLogger(__name__)

# Discovered from the site's own JS bundle — the public endpoint + key the
# myscheme.gov.in SPA itself uses. Override via env if the portal rotates them.
DEFAULT_API_URL = "https://api.myscheme.gov.in/search/v6/schemes"
DEFAULT_API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"

# Bundled sample records in the standard raw-record shape the normalizer consumes
# (used on a cold start when the live API is unreachable and no snapshot exists).
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
        self.api_url = api_url or os.getenv("MYSCHEME_API_URL", "").strip() or DEFAULT_API_URL
        self.api_key = api_key or os.getenv("MYSCHEME_API_KEY", "").strip() or DEFAULT_API_KEY
        self.rate_limit = float(
            rate_limit_seconds
            or os.getenv("MYSCHEME_RATE_LIMIT_SECONDS", "2")
        )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Aiml-project-schemes-ingestion/1.0 (+polite polling, contact: project)",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.myscheme.gov.in",
                "Referer": "https://www.myscheme.gov.in/",
                "x-api-key": self.api_key,
            }
        )

    # ------------------------------------------------------------- public API

    def fetch_schemes(self) -> Tuple[List[Dict], str]:
        """Return (records, status) where status is ok | degraded | sample.

        A live call that yields **zero** parseable records is treated as a
        failure, not as "the portal is empty": an empty payload would otherwise
        be written over the last good snapshot, every scheme would look
        "missing" and the change detector would emit mass false CLOSED events.
        """
        try:
            payload = self._fetch_paginated()
            records = parse_schemes(payload)
            if not records:
                raise ValueError(
                    "MyScheme API returned an empty/error payload (0 records)"
                )
            RawStore("myscheme").write(schemes=records, status="ok")
            logger.info(
                "MyScheme live fetch OK: %d raw items → %d parsed records",
                len(payload),
                len(records),
            )
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
        """GET the configured endpoint, collecting raw items across pages.

        The API is undocumented and could misbehave forever — a hard page cap
        keeps us from hammering a government production site. Default page size
        of 100 means ~48 requests for the full ~4,800-scheme catalog.
        """
        page_size = int(os.getenv("MYSCHEME_PAGE_SIZE", "100"))
        max_pages = int(os.getenv("MYSCHEME_MAX_PAGES", "200"))
        from_index = 0
        page = 0
        items: List[Dict] = []
        total = None

        while True:
            resp = self.session.get(
                self.api_url,
                params={
                    "lang": "en",
                    "q": "",
                    "keyword": "",
                    "sort": "multiple_sort",
                    "from": from_index,
                    "size": page_size,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            payload = resp.json()

            batch, meta = _extract_items_and_page(payload)
            items.extend(batch)
            if total is None:
                try:
                    total = int(meta.get("total")) if meta.get("total") is not None else None
                except (TypeError, ValueError):
                    total = None
            page += 1
            from_index = page * page_size

            if page >= max_pages:
                logger.warning(
                    "MyScheme pagination hit MAX_PAGES=%d; stopping", max_pages
                )
                break
            if total is not None:
                if from_index >= total:
                    break
                # The portal promised more pages but returned an empty one.
                # Abort rather than ship a partial catalog: a partial catalog
                # would make the remaining schemes look "missing" and trigger
                # false CLOSED events after a couple of runs.
                if not batch:
                    raise RuntimeError(
                        f"MyScheme pagination stopped early: {len(items)} items "
                        f"collected of total {total} (empty page at "
                        f"from={from_index - page_size})"
                    )
            else:
                if not batch:
                    break
            time.sleep(self.rate_limit)

        if total is not None and len(items) < total * 0.995:
            raise RuntimeError(
                f"MyScheme incomplete fetch: {len(items)} of {total} items collected"
            )

        logger.info(
            "MyScheme fetched %d raw items across %d pages (total=%s)",
            len(items), page, total,
        )
        return items


# -------------------------------------------------------------- parsing utils


def _extract_items_and_page(payload) -> Tuple[List[Dict], Dict]:
    """Pull (items, page-meta) out of the API envelope, defensively.

    Handles the discovered shape ``data.hits.{items,page}`` as well as legacy
    list/``data``/``results`` responses.
    """
    data = payload if isinstance(payload, dict) else {}
    if isinstance(payload, dict):
        data = payload.get("data", payload)
    if isinstance(data, dict):
        hits = data.get("hits", {})
        if isinstance(hits, dict) and isinstance(hits.get("items"), list):
            items = [i for i in hits["items"] if isinstance(i, dict)]
            page = hits.get("page", {})
            return items, {
                "total": page.get("total") if isinstance(page, dict) else None,
                "pageNumber": page.get("pageNumber") if isinstance(page, dict) else None,
                "totalPages": page.get("totalPages") if isinstance(page, dict) else None,
            }
        if isinstance(data.get("items"), list):
            return [i for i in data["items"] if isinstance(i, dict)], {}
        if isinstance(data.get("results"), list):
            return [i for i in data["results"] if isinstance(i, dict)], {}
    if isinstance(payload, list):
        return [i for i in payload if isinstance(i, dict)], {}
    return [], {}
