"""
Scheme Validator Layer
-----------------------
Purpose:
- Validate normalized scheme objects
- Enforce schema integrity
- Enforce governance rules
- Prevent data pollution
- Block unsafe data
- Protect privacy model
- Ensure system compatibility
- Maintain data quality over time

This is a governance gate, not a form validator.
"""

from typing import Dict, List

REQUIRED_FIELDS = {
    "scheme_id",
    "source",
    "name",
    "category",
    "ministry",
    "description",
    "state_code",
    "confidence_score",
    "status",
    "version"
}

ALLOWED_STATUS = {"ACTIVE", "INACTIVE", "DEPRECATED"}

ALLOWED_CATEGORIES = {
    "SCHOLARSHIP",
    "FELLOWSHIP",
    "GRANT",
    "LOAN",
    "SUBSIDY",
    "INTERNSHIP",
    "SKILL_PROGRAM",
    "TRAINING_PROGRAM",
    "WELFARE_SCHEME",
    "OTHER",
    "UNKNOWN"
}

BANNED_FIELDS = {
    "aadhaar",
    "pan",
    "bank",
    "account",
    "biometric",
    "passport",
    "address",
    "document",
    "photo",
    "identity",
    "certificate"
}

class ValidationError(Exception):
    pass

class SchemeValidator:

    def validate(self, scheme: Dict) -> Dict:
        """
        Main validation entrypoint.
        Raises ValidationError on failure.
        Returns scheme if valid.
        """

        self._check_required_fields(scheme)
        self._check_types(scheme)
        self._check_category(scheme)
        self._check_status(scheme)
        self._check_privacy(scheme)
        self._check_confidence(scheme)
        self._check_state_code(scheme)
        self._check_links(scheme)

        return scheme

    # -----------------------------
    # Validation Rules
    # -----------------------------

    def _check_required_fields(self, scheme: Dict):
        missing = REQUIRED_FIELDS - scheme.keys()
        if missing:
            raise ValidationError(f"Missing required fields: {missing}")

    def _check_types(self, scheme: Dict):
        if not isinstance(scheme.get("scheme_id"), str):
            raise ValidationError("scheme_id must be string")

        if not isinstance(scheme.get("name"), str):
            raise ValidationError("name must be string")

        if not isinstance(scheme.get("category"), str):
            raise ValidationError("category must be string")

        if not isinstance(scheme.get("confidence_score"), (float, int)):
            raise ValidationError("confidence_score must be numeric")

        if scheme.get("tags") and not isinstance(scheme.get("tags"), list):
            raise ValidationError("tags must be list")

    def _check_category(self, scheme: Dict):
        if scheme["category"] not in ALLOWED_CATEGORIES:
            raise ValidationError(f"Invalid category: {scheme['category']}")

    def _check_status(self, scheme: Dict):
        if scheme["status"] not in ALLOWED_STATUS:
            raise ValidationError(f"Invalid status: {scheme['status']}")

    def _check_privacy(self, scheme: Dict):
        full_text = " ".join([
            str(v).lower() for v in scheme.values() if isinstance(v, str)
        ])

        for banned in BANNED_FIELDS:
            if banned in full_text:
                raise ValidationError(f"Privacy violation detected: {banned}")

    def _check_confidence(self, scheme: Dict):
        score = scheme.get("confidence_score")
        if score < 0 or score > 1:
            raise ValidationError("confidence_score must be between 0 and 1")

    def _check_state_code(self, scheme: Dict):
        state = scheme.get("state_code")
        if state and len(state) not in (2, 3):
            raise ValidationError("Invalid state_code format")

    def _check_links(self, scheme: Dict):
        link = scheme.get("link")
        if link and not link.startswith("http"):
            raise ValidationError("Invalid link format")
