"""
Karnataka SSP connector — read-only public-page client
--------------------------------------------------------
The State Scholarship Portal is login-gated and hostile to scraping. Per
docs/next.md §1.3 we keep this connector **read-only on public pages only**:

    - public landing pages only (/, /ssppre/PreHome, /ssppre/PostHome)
    - never attempt login, never answer captchas, never hammer the site
    - polite delays between page loads; one run every few hours max
    - on a block/failure, log it and degrade to the last successful snapshot
      instead of retrying aggressively

Primary transport is ``requests`` + BeautifulSoup (server-rendered ASP.NET
markup). An optional Playwright fallback kicks in only when enabled via
``SSP_USE_PLAYWRIGHT=true`` *and* the playwright package is installed.
"""

import logging
import os
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin

import requests

from ingestion.sources.karnataka_ssp.parser import parse_notices, parse_schemes
from ingestion.sources.raw_store import RawStore

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://ssp.karnataka.gov.in"
PUBLIC_PAGES = ["/", "/ssppre/PreHome", "/ssppre/PostHome"]

SAMPLE_NOTICES = [
    {
        "title": "SSP 2026-27 application window opened for renewal applications",
        "text": (
            "Renewal applications for the academic year 2026-27 are now open on the "
            "Karnataka State Scholarship Portal. Last date as per the department order."
        ),
        "link": "https://ssp.karnataka.gov.in",
        "published_at": None,
    },
    {
        "title": "Vidyasiri 2026-27 deadline extended",
        "text": (
            "The last date to apply for Vidyasiri Scholarship 2026-27 has been extended "
            "to 31-10-2026 for fresh applications."
        ),
        "link": "https://ssp.karnataka.gov.in",
        "published_at": "2026-10-31",
    },
]


class KarnatakaSSPClient:
    """Read-only, polite connector for the SSP public landing pages."""

    def __init__(
        self,
        base_url: str = "",
        delay_seconds: float = 3.0,
        timeout: int = 20,
    ):
        self.base_url = (base_url or os.getenv("SSP_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.delay = float(
            delay_seconds or os.getenv("SSP_PAGE_DELAY_SECONDS", "3")
        )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; Aiml-project-schemes-ingestion/1.0; +read-only-public-pages)",
                "Accept": "text/html,application/xhtml+xml",
            }
        )

    # ------------------------------------------------------------- public API

    def fetch(self) -> Tuple[List[Dict], List[Dict], str]:
        """Fetch public pages and return (schemes, notices, status).

        status is ok | degraded | sample.
        """
        try:
            html_pages = self._fetch_public_pages()
        except Exception as exc:  # noqa: BLE001 — degrade, never crash the pipeline
            logger.warning("SSP live fetch failed (%s); degrading gracefully", exc)
            last = RawStore("karnataka_ssp").latest()
            if last:
                RawStore("karnataka_ssp").write(
                    schemes=last.get("schemes"),
                    notices=last.get("notices"),
                    status="degraded",
                    extra={"reason": str(exc)},
                )
                return last.get("schemes", []), last.get("notices", []), "degraded"
            logger.warning("No previous SSP snapshot — using sample records")
            return [], list(SAMPLE_NOTICES), "sample"

        schemes: List[Dict] = []
        notices: List[Dict] = []
        for page_url, html in html_pages:
            schemes.extend(parse_schemes(html, base_url=self.base_url))
            notices.extend(parse_notices(html, base_url=self.base_url))

        RawStore("karnataka_ssp").write(
            schemes=schemes, notices=notices, status="ok"
        )
        return schemes, notices, "ok"

    # ------------------------------------------------------------ internals

    def _fetch_public_pages(self) -> List[Tuple[str, str]]:
        pages: List[Tuple[str, str]] = []
        for index, page in enumerate(PUBLIC_PAGES):
            if index > 0:
                time.sleep(self.delay)

            url = urljoin(self.base_url, page)
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
            except requests.RequestException as exc:
                # A single blocked page is not fatal — keep the ones we got.
                logger.warning("SSP page %s fetch failed: %s", url, exc)
                continue
            pages.append((url, response.text))

        if not pages:
            raise RuntimeError("all public SSP pages failed to load")

        if os.getenv("SSP_USE_PLAYWRIGHT", "false").strip().lower() == "true":
            return self._playwright_fallback(pages)

        return pages

    def _playwright_fallback(
        self, fallback_pages: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """Optional Playwright rendering path (only when explicitly enabled).

        Returns ``fallback_pages`` unchanged if playwright is unavailable, so the
        connector still works with the pages already fetched via requests.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning(
                "SSP_USE_PLAYWRIGHT=true but playwright is not installed; "
                "continuing with the pages already fetched via requests"
            )
            return fallback_pages

        rendered: List[Tuple[str, str]] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                for path in PUBLIC_PAGES:
                    url = urljoin(self.base_url, path)
                    try:
                        page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                        rendered.append((url, page.content()))
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("SSP playwright page %s failed: %s", url, exc)
            finally:
                browser.close()

        return rendered or fallback_pages
