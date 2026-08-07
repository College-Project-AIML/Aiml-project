"""
Content Fingerprinting
------------------------
Purpose:
- Produce a stable sha256 fingerprint over the *semantic* fields of a normalized scheme
- Exclude volatile metadata (ingested_at, last_updated, timestamps) so re-fetching
  a portal does not generate false-positive change events
- Provide the ground truth the change detector classifies against (NEW / UPDATED / CLOSED)

Per docs/next.md §2.2 the fingerprint covers name, description, eligibility_text,
category, ministry, link, tags (plus state_code and status for safety).
"""

import hashlib
import json
from typing import Dict

# The fields that make up a scheme's identity for change detection.
# Kept in sync with the diff logic in change_detector.py.
SEMANTIC_FIELDS = [
    "name",
    "description",
    "eligibility_text",
    "category",
    "ministry",
    "link",
    "state_code",
    "status",
    "tags",
    "confidence_score",
]


def fingerprint_record(normalized: Dict) -> str:
    """
    Compute the sha256 fingerprint of a normalized scheme record.

    The payload is a canonical JSON document over SEMANTIC_FIELDS, sorted by key
    so that field ordering never affects the fingerprint. List values (tags) are
    sorted too, so the fingerprint is stable regardless of how the caller ordered
    them.
    """
    canonical = {field: normalized.get(field) for field in SEMANTIC_FIELDS}
    canonical = {
        key: (sorted(value) if isinstance(value, list) else value)
        for key, value in canonical.items()
    }
    payload = json.dumps(canonical, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
