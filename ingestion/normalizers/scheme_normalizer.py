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
            "slug": self._normalize_text(raw.get("slug")),
            "tags": self._generate_tags(raw),
            "confidence_score": self._source_confidence(raw.get("source")),
            "version": "v1",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "ACTIVE"
        }

        extras = raw.get("raw_extras", {}) or {}
        normalized["benefits"] = self._normalize_benefits(extras.get("benefits"))
        normalized["documents"] = self._normalize_documents(extras.get("documents"))
        normalized["eligibility_rules"] = self._normalize_eligibility_rules(
            raw.get("eligibility"), normalized["state_code"]
        )
        normalized["deadline"] = extras.get("deadline")

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
    # Related Data Normalizers
    # -----------------------------

    def _normalize_benefits(self, raw_benefits):
        """Convert raw benefits data into structured benefit records."""
        if not raw_benefits:
            return []
        
        benefits = []
        if isinstance(raw_benefits, list):
            for b in raw_benefits:
                if isinstance(b, dict):
                    benefits.append({
                        "benefit_type": b.get("type") or b.get("benefit_type") or "financial",
                        "description": self._normalize_text(b.get("description") or b.get("details")),
                        "amount": self._parse_amount(b.get("amount") or b.get("value")),
                        "frequency": b.get("frequency") or b.get("period") or "annual"
                    })
                elif isinstance(b, str):
                    benefits.append({
                        "benefit_type": "financial",
                        "description": self._normalize_text(b),
                        "amount": None,
                        "frequency": "annual"
                    })
        elif isinstance(raw_benefits, dict):
            benefits.append({
                "benefit_type": raw_benefits.get("type", "financial"),
                "description": self._normalize_text(raw_benefits.get("description")),
                "amount": self._parse_amount(raw_benefits.get("amount")),
                "frequency": raw_benefits.get("frequency", "annual")
            })
        elif isinstance(raw_benefits, str):
            benefits.append({
                "benefit_type": "financial",
                "description": self._normalize_text(raw_benefits),
                "amount": None,
                "frequency": "annual"
            })
        
        return benefits

    def _normalize_documents(self, raw_documents):
        """Convert raw documents data into structured document records."""
        if not raw_documents:
            return []
        
        documents = []
        if isinstance(raw_documents, list):
            for d in raw_documents:
                if isinstance(d, dict):
                    documents.append({
                        "document_name": d.get("name") or d.get("document_name") or d.get("document"),
                        "is_mandatory": d.get("mandatory", d.get("is_mandatory", True))
                    })
                elif isinstance(d, str):
                    documents.append({
                        "document_name": d,
                        "is_mandatory": True
                    })
        elif isinstance(raw_documents, str):
            documents.append({
                "document_name": raw_documents,
                "is_mandatory": True
            })
        
        return [d for d in documents if d.get("document_name")]

    def _normalize_eligibility_rules(self, eligibility_text, state_code):
        """Extract structured eligibility rules from eligibility text."""
        if not eligibility_text:
            return None
        
        rules = {
            "min_age": None,
            "max_age": None,
            "max_income": None,
            "gender": None,
            "caste": None,
            "states": [state_code] if state_code and state_code != "IN" else None,
            "education_level": None
        }
        
        text = eligibility_text.lower()
        
        # Extract age
        import re
        age_matches = re.findall(r'age[:\s]*(\d+)[\s\-]*(\d+)?', text)
        if age_matches:
            rules["min_age"] = int(age_matches[0][0])
            if age_matches[0][1]:
                rules["max_age"] = int(age_matches[0][1])
        
        # Extract income (look for lakhs, rupees, etc.)
        income_matches = re.findall(r'(?:income|earning)[^\d]*(\d+(?:\.\d+)?)\s*(?:lakh|lac|crore)?', text)
        if income_matches:
            val = float(income_matches[0])
            if 'lakh' in text or 'lac' in text:
                val *= 100000
            elif 'crore' in text:
                val *= 10000000
            rules["max_income"] = val
        
        # Extract gender
        if 'girl' in text or 'women' in text or 'female' in text:
            rules["gender"] = ["female"]
        elif 'boy' in text or 'male' in text:
            rules["gender"] = ["male"]
        
        # Extract caste
        caste_keywords = ['sc', 'st', 'obc', 'general', 'minority', 'tribal', 'scheduled caste', 'scheduled tribe']
        found_castes = [c for c in caste_keywords if c in text]
        if found_castes:
            # Normalize caste names
            caste_map = {
                'sc': 'SC', 'scheduled caste': 'SC',
                'st': 'ST', 'scheduled tribe': 'ST',
                'obc': 'OBC',
                'general': 'general',
                'minority': 'minority',
                'tribal': 'ST'
            }
            rules["caste"] = [caste_map.get(c, c.upper()) for c in found_castes]
        
        # Extract education level
        edu_keywords = {
            '10th': '10th_pass', 'class 10': '10th_pass', 'matric': '10th_pass', 'ssc': '10th_pass',
            '12th': '12th_pass', 'class 12': '12th_pass', 'puc': '12th_pass', 'hsc': '12th_pass',
            'graduate': 'graduate', 'graduation': 'graduate', 'degree': 'graduate',
            'post graduate': 'post_graduate', 'postgraduate': 'post_graduate', 'masters': 'post_graduate', 'phd': 'post_graduate',
            'diploma': 'diploma', 'iti': 'diploma'
        }
        for keyword, level in edu_keywords.items():
            if keyword in text:
                rules["education_level"] = level
                break
        
        # Only return if we extracted something meaningful
        if any(v is not None for v in rules.values() if v not in ([], None)):
            return rules
        return None

    def _parse_amount(self, value):
        """Parse amount from various formats."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols, commas
            cleaned = re.sub(r'[₹$,\s]', '', value)
            # Handle lakhs/crores
            if 'lakh' in cleaned.lower() or 'lac' in cleaned.lower():
                num = re.search(r'(\d+(?:\.\d+)?)', cleaned)
                if num:
                    return float(num.group(1)) * 100000
            elif 'crore' in cleaned.lower():
                num = re.search(r'(\d+(?:\.\d+)?)', cleaned)
                if num:
                    return float(num.group(1)) * 10000000
            # Plain number
            num = re.search(r'(\d+(?:\.\d+)?)', cleaned)
            if num:
                return float(num.group(1))
        return None

    # -----------------------------
    # Utilities
    # -----------------------------

    def _hash(self, text):
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
