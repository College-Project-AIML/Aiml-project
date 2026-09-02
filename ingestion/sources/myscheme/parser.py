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

Discovered API contract (verified 2026-08-07): search hits arrive as
``{id, fields: {...}}`` where ``fields`` uses camelCase keys:

    {
        "schemeName", "slug", "briefDescription", "nodalMinistryName",
        "schemeCategory": [...], "beneficiaryState": [...], "tags": [...],
        "schemeCloseDate": "YYYY-MM-DD", "level": "Central|State", "schemeFor": ...
    }

Source-specific extras (deadlines, level, schemeFor) that don't fit the core
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
    "scheme_name": ("schemeName", "scheme_name", "title", "name", "scheme", "scheme_title"),
    "ministry": ("nodalMinistryName", "ministry", "ministryName", "department", "dept", "implementingAgency", "nodal"),
    "description": ("briefDescription", "description", "objective", "overview", "schemeDetails", "about"),
    "eligibility": ("eligibility", "eligibilityCriteria", "whoCanApply", "beneficiary", "criteria"),
    "category": ("schemeCategory", "category", "categoryName", "sector", "schemeType"),
    "state": ("beneficiaryState", "state", "stateName", "states", "stateCode"),
    "slug": ("slug", "schemeSlug", "url", "slugUrl"),
    "tags": ("tags", "keywords", "tag"),
}

EXTRAS_VARIANTS = {
    "deadline": ("schemeCloseDate", "deadline", "lastDate", "lastDateToApply", "endDate", "applyDeadline"),
    "benefits": ("benefits", "benefit", "assistance", "financialSupport"),
    "documents": ("documents", "documentsRequired", "requiredDocuments"),
    "contact": ("contact", "helpdesk", "helpline"),
    "application_link": ("applicationUrl", "applyUrl", "applyLink", "registrationUrl"),
}

# MyScheme's free-form scheme categories → our normalizer's controlled keywords.
# Anything not matched falls back to a keyword scan, then "other".
CATEGORY_EXACT = {
    "Social welfare & Empowerment": "welfare",
    "Education & Learning": "scholarship",
    "Agriculture,Rural & Environment": "subsidy",
    "Business & Entrepreneurship": "loan",
    "Women and Child": "welfare",
    "Skills & Employment": "skill",
    "Banking,Financial Services and Insurance": "loan",
    "Health & Wellness": "welfare",
    "Sports & Culture": "grant",
    "Housing & Shelter": "subsidy",
    "Science, IT & Communications": "grant",
    "Transport & Infrastructure": "other",
    "Travel & Tourism": "other",
    "Utility & Sanitation": "other",
    "Public Safety,Law & Justice": "other",
}

CATEGORY_KEYWORD = [
    (("scholarship", "education", "learning", "student"), "scholarship"),
    (("skill", "employment", "job", "training", "apprentice"), "skill"),
    (("loan", "business", "entrepreneur", "banking", "finance", "credit", "insurance"), "loan"),
    (("welfare", "empower", "social", "women", "child", "health", "pension", "disabl"), "welfare"),
    (("agriculture", "rural", "environment", "housing", "shelter", "subsid"), "subsidy"),
    (("sport", "culture", "science", "technology", "communication", "research"), "grant"),
]

ALL_INDIA_STATES = {"all", "all india", "all-india", "national", "india", "in", "pan india", "pan-india"}


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
    for key in ("data", "results", "schemes", "items", "records", "hits"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _extract_items(value)
            if nested:
                return nested
    return []


def _first(item: Dict, variants) -> object:
    for key in variants:
        value = item.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _normalize_category(raw_category) -> str:
    """Map a MyScheme schemeCategory value onto the normalizer's vocabulary."""
    if isinstance(raw_category, list):
        raw_category = raw_category[0] if raw_category else None
    if not raw_category:
        return "other"
    name = str(raw_category).strip()
    exact = CATEGORY_EXACT.get(name)
    if exact:
        return exact
    lowered = name.lower()
    for keywords, category in CATEGORY_KEYWORD:
        if any(kw in lowered for kw in keywords):
            return category
    return "other"


def _normalize_state(raw_state) -> str:
    """beneficiaryState is a list like ['All'] or ['Karnataka', 'Maharashtra']."""
    if isinstance(raw_state, list):
        if not raw_state:
            return "india"
        states = [str(s).strip().lower() for s in raw_state if s]
        if not states:
            return "india"
        # "All" (or any all-India marker) means the scheme is national.
        if any(s in ALL_INDIA_STATES for s in states):
            return "india"
        return states[0]
    state = str(raw_state or "").strip().lower()
    if state in ALL_INDIA_STATES or not state:
        return "india"
    return state


def _to_raw_record(item: Dict) -> Dict:
    # Discovered shape wraps the camelCase payload under `fields` (search hits).
    if isinstance(item.get("fields"), dict):
        item = item["fields"]

    name = _first(item, FIELD_VARIANTS["scheme_name"])
    slug = _first(item, FIELD_VARIANTS["slug"])

    # nodalMinistryName may be a plain string or {"label": ...}.
    ministry = _first(item, FIELD_VARIANTS["ministry"])
    if isinstance(ministry, dict):
        ministry = ministry.get("label")

    tags = _first(item, FIELD_VARIANTS["tags"]) or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    extras = {}
    for extra_name, variants in EXTRAS_VARIANTS.items():
        value = _first(item, variants)
        if value is not None:
            extras[extra_name] = value
    for extra_name in ("level", "schemeFor", "schemeShortTitle", "priority"):
        value = item.get(extra_name)
        if value not in (None, "", [], {}):
            extras[extra_name] = value

    record = {
        "scheme_name": str(name).strip() if name else None,
        "source": "myscheme.gov.in",
        "category": _normalize_category(_first(item, FIELD_VARIANTS["category"])),
        "ministry": ministry,
        "description": _first(item, FIELD_VARIANTS["description"]),
        "eligibility": _first(item, FIELD_VARIANTS["eligibility"]),
        "state": _normalize_state(_first(item, FIELD_VARIANTS["state"])),
        "link": f"{SCHEME_LINK_BASE}/{slug}" if slug else None,
        "application_link": extras.get("application_link"),
        "tags": tags,
        "raw_extras": extras,
    }
    return record
