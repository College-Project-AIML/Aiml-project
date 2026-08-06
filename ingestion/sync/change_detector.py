"""
Change Detector
-----------------
Purpose:
- Classify each fetched scheme against its last known snapshot fingerprint
- NEW | UNCHANGED | UPDATED, plus CLOSED for schemes missing from consecutive runs
- Produce the `changed_fields` diff used by the "what's new" feed

This module is pure logic with no I/O, so it is trivial to unit test
(docs/next.md §2.3 acceptance criteria).
"""

from typing import Dict, List, Optional, Set

NEW = "NEW"
UNCHANGED = "UNCHANGED"
UPDATED = "UPDATED"
CLOSED = "CLOSED"

CHANGE_TYPES = {NEW, UNCHANGED, UPDATED, CLOSED}

# Fields reported in ``changed_fields`` diffs. ``tags`` is intentionally
# excluded: the normalizer auto-derives it from the text fields, so any text
# change would add a noisy word-list diff alongside the real change. Tags still
# participate in the fingerprint (see fingerprint.SEMANTIC_FIELDS), so a tags
# change alone still triggers an UPDATED event.
DIFF_FIELDS = {
    "name",
    "description",
    "eligibility_text",
    "category",
    "ministry",
    "link",
    "state_code",
    "status",
    "confidence_score",
}


def classify(current_fingerprint: str, previous_fingerprint: Optional[str]) -> str:
    """Classify a single scheme given its current and previous fingerprints.

    - no previous fingerprint  -> NEW
    - identical fingerprints   -> UNCHANGED
    - differing fingerprints   -> UPDATED
    """
    if previous_fingerprint is None:
        return NEW
    if current_fingerprint == previous_fingerprint:
        return UNCHANGED
    return UPDATED


def diff_fields(old: Dict, new: Dict, fields: Optional[Set[str]] = None) -> Dict[str, list]:
    """Return ``{field: [old_value, new_value]}`` for every semantic field that changed.

    Used to populate ``scheme_updates.changed_fields``.
    """
    changed: Dict[str, list] = {}
    candidates = fields if fields is not None else DIFF_FIELDS
    for field in candidates:
        old_value = old.get(field)
        new_value = new.get(field)
        if old_value != new_value:
            changed[field] = [old_value, new_value]
    return changed
