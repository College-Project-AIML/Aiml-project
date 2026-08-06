"""
Karnataka SSP parser
----------------------
Parses the **public landing pages** of the Karnataka State Scholarship Portal
(ssp.karnataka.gov.in) into two things (docs/next.md §1.3):

1. Scheme cards / links → raw records in the standard pipeline shape
   (normalizer maps department → ministry, etc.)
2. Notices / announcements (deadline changes, new openings) → lightweight
   ``notice`` records with ``published_at`` and raw text. These are the
   near-real-time signals that matter most.

The portal is an ASP.NET app whose markup can change, so parsing is deliberately
defensive and keyword-driven. When the layout changes, only this file needs
updating — raw snapshots stay immutable under ``data/raw/karnataka_ssp/``.
"""

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://ssp.karnataka.gov.in"

# Substrings that mark a link as scheme-related (ASP.NET menus are noisy).
# Includes the Kannada word for scholarship (ವಿದ್ಯಾರ್ಥಿವೇತನ) seen on the portal.
SCHEME_LINK_HINTS = (
    "scheme", "scholarship", "yojana", "freeship", "postmatric", "vidya",
    "ವಿದ್ಯಾರ್ಥಿವೇತನ",
)

# Substrings that mark a link as navigation/login/document noise.
JUNK_HINTS = (
    "login", "signin", "sign in", "log in", "auth", "password", "forgot",
    "register", "create account", "create new account", "click here",
    "apply for", "information system", "empowerment",
    "feedback", "contact", "sitemap", "policy", "terms", "screen reader",
    "download", "video", "eligibility_criteria", "skip to main",
)

FILE_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")

# CSS-ish selectors for notice/announcement blocks on government portals.
NOTICE_SELECTORS = [
    "[class*='notice' i]",
    "[id*='notice' i]",
    "[class*='announcement' i]",
    "[id*='announcement' i]",
    "marquee",
    "[class*='whatsnew' i]",
    "[id*='whatsnew' i]",
]

DATE_PATTERNS = [
    re.compile(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})"),
    re.compile(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})"),
]


def parse_schemes(html: str, base_url: str = DEFAULT_BASE_URL) -> List[Dict]:
    """Extract scheme cards/links from a public SSP landing page."""
    soup = BeautifulSoup(html, "html.parser")
    records: List[Dict] = []
    seen: set = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        text = " ".join(anchor.get_text(" ", strip=True).split())
        if not text or len(text) > 200:
            continue
        # Scheme card titles are short; long CTA/paragraph anchors are noise.
        if len(text) > 90:
            continue
        if not _is_scheme_link(href, text):
            continue

        url = urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)

        records.append(
            {
                "scheme_name": text,
                "source": "ssp.karnataka.gov.in",
                "category": "scholarship",
                "ministry": "Department of Higher Education, Karnataka",
                "description": (
                    "Scheme listed on the public landing page of the Karnataka "
                    "State Scholarship Portal."
                ),
                "eligibility": None,
                "state": "karnataka",
                "link": url,
                "tags": ["karnataka", "scholarship", "ssp"],
            }
        )

    logger.info("SSP parser: extracted %d scheme links", len(records))
    return records


def parse_notices(html: str, base_url: str = DEFAULT_BASE_URL) -> List[Dict]:
    """Extract notice/announcement blocks from a public SSP landing page."""
    soup = BeautifulSoup(html, "html.parser")
    notices: List[Dict] = []
    seen_text: set = set()

    for element in soup.select(",".join(NOTICE_SELECTORS)):
        for snippet in _split_notice_snippets(element):
            text = " ".join(snippet.split())
            # Keep only notice-sized snippets (or anything carrying a date).
            if not (15 <= len(text) <= 400 or _extract_date(text)):
                continue
            if text[:80] in seen_text:
                continue
            seen_text.add(text[:80])

            link = None
            anchor = element.find("a", href=True)
            if anchor and not anchor["href"].startswith("#"):
                link = urljoin(base_url, anchor["href"])

            notices.append(
                {
                    "title": text[:200],
                    "text": text,
                    "link": link,
                    "published_at": _extract_date(text),
                }
            )

    logger.info("SSP parser: extracted %d notices", len(notices))
    return notices


def _split_notice_snippets(element):
    """Yield individual notice snippets from a container (list items, else text)."""
    items = element.find_all("li")
    if items:
        for li in items:
            yield li.get_text(" ", strip=True)
    else:
        yield element.get_text(" ", strip=True)


# --------------------------------------------------------------- helpers


def _is_scheme_link(href: str, text: str) -> bool:
    combined = f"{href} {text}".lower()
    if not any(hint in combined for hint in SCHEME_LINK_HINTS):
        return False
    if _is_junk(href, text):
        return False
    return True


def _is_junk(href: str, text: str) -> bool:
    """True for login/nav/document/in-page links that are not scheme records."""
    low_href = href.lower()
    if href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return True
    if any(low_href.endswith(suffix) for suffix in FILE_SUFFIXES):
        return True
    combined = f"{low_href} {text.lower()}"
    return any(hint in combined for hint in JUNK_HINTS)


def _extract_date(text: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            parts = match.groups()
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return None
