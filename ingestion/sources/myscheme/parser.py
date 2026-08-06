"""
MyScheme parser
-----------------
Converts raw JSON fetched from the MyScheme portal's internal API into the
standard raw-record shape our pipeline already understands
(docs/next.md §1.2):

    {
        "scheme_name": ..., "source": "myscheme.gov.in", "category": "scholarship",
        "ministry": ..., "description": ..., "eligibility": ...,
        "state": "karnataka" | "india", "link": "https://www.myscheme.gov.in/schemes/{slug}",
        "tags": [...]
    }

Source-specific extras (deadlines, benefits, documents) that don't fit the core
model are carried in ``raw_extras`` for later detail enrichment.

The API contract is undocumented and changes over time, so the parser is kept
defensive: it maps common field-name variants and ignores anything unknown.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

SCHEME_LINK_BASE = "https://www.myscheme.gov.in/schemes"

# Common field-name variants seen in undocumented government JSON payloads.
FIELD_VARIANTS = {
    "scheme_name": ("scheme_name", "schemeName", "title", "name", "scheme", "scheme_title"),
    "ministry": ("ministry", "ministryName", "department", "dept", "implementingAgency", "nodal"),
    "description": ("description", "objective", "overview", "schemeDetails", "about"),
    "eligibility": ("eligibility", "eligibilityCriteria", "whoCanApply", "beneficiary", "criteria"),
    "category": ("category", "categoryName", "sector", "schemeType"),
    "state": ("state", "stateName", "states", "stateCode"),
    "slug": ("slug", "schemeSlug", "url", "slugUrl"),
    "tags": ("tags", "keywords", "tag"),
}

EXTRAS_VARIANTS = {
    "deadline": ("deadline", "lastDate", "lastDateToApply", "endDate", "applyDeadline"),
    "benefits": ("benefits", "benefit", "assistance", "financialSupport"),
    "documents": ("documents", "documentsRequired", "requiredDocuments"),
    "contact": ("contact", "helpdesk", "helpline"),
}


def parse_schemes(payload) -> List[Dict]:
    """Convert a MyScheme API payload into raw records for the normalizer."""
    items = payload if isinstance(payload, list) else _extract_items(payload)
    records: List[Dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        record = _to_raw_record(item)
        if record.get("scheme_name"):
            records.append(record)
    return records


def _extract_items(payload: Dict) -> List[Dict]:
    for key in ("data", "results", "schemes", "items", "records"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _first(item: Dict, variants) -> object:
    for key in variants:
        value = item.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _to_raw_record(item: Dict) -> Dict:
    name = _first(item, FIELD_VARIANTS["scheme_name"])
    slug = _first(item, FIELD_VARIANTS["slug"])

    state = _first(item, FIELD_VARIANTS["state"]) or "india"
    if isinstance(state, list):
        state = state[0] if state else "india"
    state = str(state).strip().lower()
    if state in ("all india", "all-india", "national", "india", "in"):
        state = "india"

    tags = _first(item, FIELD_VARIANTS["tags"]) or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    extras = {}
    for extra_name, variants in EXTRAS_VARIANTS.items():
        value = _first(item, variants)
        if value is not None:
            extras[extra_name] = value

    record = {
        "scheme_name": str(name).strip() if name else None,
        "source": "myscheme.gov.in",
        "category": _first(item, FIELD_VARIANTS["category"]),
        "ministry": _first(item, FIELD_VARIANTS["ministry"]),
        "description": _first(item, FIELD_VARIANTS["description"]),
        "eligibility": _first(item, FIELD_VARIANTS["eligibility"]),
        "state": state,
        "link": f"{SCHEME_LINK_BASE}/{slug}" if slug else None,
        "tags": tags,
        "raw_extras": extras,
    }
    return record
