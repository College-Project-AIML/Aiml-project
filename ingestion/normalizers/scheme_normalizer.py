"""
Scheme Normalizer Layer
------------------------
Purpose:
- Convert raw ingested data into structured system format
- Enforce schema discipline
- Standardize fields
- Clean noise
- Normalize categories
- Prepare for eligibility + recommendation engines
- Act as governance gate between ingestion and storage

This is NOT data cleaning.
This is system normalization.
"""

import re
from datetime import datetime

# -----------------------------
# Controlled vocabularies
# -----------------------------

CATEGORY_MAP = {
    "scholarship": "SCHOLARSHIP",
    "fellowship": "FELLOWSHIP",
    "grant": "GRANT",
    "loan": "LOAN",
    "subsidy": "SUBSIDY",
    "internship": "INTERNSHIP",
    "skill": "SKILL_PROGRAM",
    "training": "TRAINING_PROGRAM",
    "welfare": "WELFARE_SCHEME"
}

STATE_MAP = {
    # All-India markers
    "india": "IN",
    "national": "IN",
    "all india": "IN",
    "all-india": "IN",
    "pan india": "IN",
    "pan-india": "IN",
    # States
    "andhra pradesh": "AP",
    "arunachal pradesh": "AR",
    "assam": "AS",
    "bihar": "BR",
    "chhattisgarh": "CG",
    "goa": "GA",
    "gujarat": "GJ",
    "haryana": "HR",
    "himachal pradesh": "HP",
    "jharkhand": "JH",
    "karnataka": "KA",
    "kerala": "KL",
    "madhya pradesh": "MP",
    "maharashtra": "MH",
    "manipur": "MN",
    "meghalaya": "ML",
    "mizoram": "MZ",
    "nagaland": "NL",
    "odisha": "OD",
    "orissa": "OD",
    "punjab": "PB",
    "rajasthan": "RJ",
    "sikkim": "SK",
    "tamil nadu": "TN",
    "tamilnadu": "TN",
    "telangana": "TG",
    "tripura": "TR",
    "uttar pradesh": "UP",
    "uttarakhand": "UK",
    "west bengal": "WB",
    # Union territories
    "andaman and nicobar islands": "AN",
    "andaman and nicobar": "AN",
    "chandigarh": "CH",
    "dadra & nagar haveli and daman & diu": "DN",
    "dadra and nagar haveli and daman and diu": "DN",
    "dadra and nagar haveli": "DN",
    "daman and diu": "DD",
    "delhi": "DL",
    "nct of delhi": "DL",
    "jammu and kashmir": "JK",
    "ladakh": "LA",
    "lakshadweep": "LD",
    "puducherry": "PY",
    "pondicherry": "PY",
}

# Fragments that identify a state regardless of surrounding words, so names
# like "The Andaman & Nicobar Islands Disability Allowance Scheme" still match.
STATE_SUBSTRING = [
    ("andaman", "AN"),
    ("arunachal", "AR"),
    ("chhattisgarh", "CG"),
    ("himachal", "HP"),
    ("madhya pradesh", "MP"),
    ("uttar pradesh", "UP"),
    ("uttarakhand", "UK"),
    ("tamil nadu", "TN"),
    ("tamilnadu", "TN"),
    ("west bengal", "WB"),
    ("jammu", "JK"),
    ("kashmir", "JK"),
    ("dadra", "DN"),
    ("nagar haveli", "DN"),
    ("daman", "DD"),
    ("diu", "DD"),
    ("lakshadweep", "LD"),
    ("puducherry", "PY"),
    ("pondicherry", "PY"),
    ("chandigarh", "CH"),
]

MINISTRY_NORMALIZATION = {
    "govt of india": "Government of India",
    "government of india": "Government of India",
    "dept of education": "Department of Education",
    "education department": "Department of Education",
    "social welfare dept": "Department of Social Welfare"
}

TAG_STOPWORDS = {"and", "for", "of", "the", "to", "in", "on", "with"}

# -----------------------------
# Core Normalizer
# -----------------------------

class SchemeNormalizer:

    def normalize(self, raw: dict) -> dict:
        """
        Input: raw ingested record
        Output: normalized scheme model
        """

        normalized = {
            "scheme_id": self._generate_id(raw),
            "source": self._normalize_source(raw.get("source")),
            "name": self._normalize_text(raw.get("scheme_name")),
            "category": self._normalize_category(raw.get("category")),
            "ministry": self._normalize_ministry(raw.get("ministry")),
            "description": self._normalize_text(raw.get("description")),
            "eligibility_text": self._normalize_text(raw.get("eligibility")),
            "state_code": self._normalize_state(raw.get("state")),
            "link": self._normalize_link(raw.get("link")),
            "application_link": self._normalize_link(raw.get("application_link")),
            "tags": self._generate_tags(raw),
            "confidence_score": self._source_confidence(raw.get("source")),
            "version": "v1",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "ACTIVE"
        }

        return normalized

    # -----------------------------
    # Field Normalizers
    # -----------------------------

    def _generate_id(self, raw):
        base = f"{raw.get('scheme_name','')}|{raw.get('source','')}|{raw.get('state','')}"
        return self._hash(base)

    def _normalize_text(self, text):
        if not text:
            return None
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize_category(self, cat):
        if not cat:
            return "UNKNOWN"
        key = cat.lower().strip()
        return CATEGORY_MAP.get(key, "OTHER")

    def _normalize_state(self, state):
        if not state:
            return None
        key = re.sub(r"\s+", " ", state.lower()).strip()
        if key in STATE_MAP:
            return STATE_MAP[key]
        # Try fragment matching for names wrapped in longer scheme titles.
        for fragment, code in STATE_SUBSTRING:
            if fragment in key:
                return code
        # Explicit state names should never fall through as a long raw string;
        # the validator requires 2–3 char codes. Fall back to all-India and
        # log a warning rather than fail validation.
        import logging

        logging.getLogger(__name__).warning(
            "Unrecognized state %r mapped to IN", state
        )
        return "IN"

    def _normalize_ministry(self, ministry):
        if not ministry:
            return None
        key = ministry.lower().strip()
        return MINISTRY_NORMALIZATION.get(key, ministry.strip())

    def _normalize_source(self, source):
        if not source:
            return "UNKNOWN"
        return source.strip().lower()

    def _normalize_link(self, link):
        if not link:
            return None
        if link.startswith("/"):
            return "https://scholarships.gov.in" + link
        return link.strip()

    # -----------------------------
    # Intelligence Support (Non-AI)
    # -----------------------------

    def _generate_tags(self, raw):
        text = f"{raw.get('scheme_name','')} {raw.get('description','')} {raw.get('eligibility','')}"
        tokens = re.findall(r"[a-zA-Z]+", text.lower())

        tags = set()
        for t in tokens:
            if len(t) > 3 and t not in TAG_STOPWORDS:
                tags.add(t)

        base_tags = set(raw.get("tags", [])) if raw.get("tags") else set()
        # Sorted for determinism: a Python set's iteration order varies with the
        # process hash seed, which would cause false-positive change events.
        return sorted(tags.union(base_tags))

    def _source_confidence(self, source):
        if not source:
            return 0.3
        if "gov.in" in source:
            return 0.95
        if "nic.in" in source:
            return 0.95
        if "karnataka.gov.in" in source:
            return 0.95
        return 0.6

    # -----------------------------
    # Utilities
    # -----------------------------

    def _hash(self, text):
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
