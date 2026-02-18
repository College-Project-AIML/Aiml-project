"""
Scheme Domain Model
--------------------
Purpose:
- Define canonical structure for all schemes/programs/scholarships
- Enforce system-wide consistency
- Act as contract between layers
- Prevent schema drift
- Enable system governance
- Support eligibility + recommendation + AI layers

This is the data constitution of Aiml-project.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

# -----------------------------
# Core Scheme Model
# -----------------------------

@dataclass
class SchemeModel:
    # Identity
    scheme_id: str                    # Deterministic hash ID
    name: str                         # Official scheme name
    source: str                       # Source system
    version: str                      # Schema version
    status: str                       # ACTIVE | INACTIVE | DEPRECATED

    # Classification
    category: str                     # SCHOLARSHIP, WELFARE, etc.
    ministry: Optional[str]           # Owning authority
    state_code: Optional[str]         # IN, KA, etc.

    # Content
    description: Optional[str]
    eligibility_text: Optional[str]
    link: Optional[str]

    # Intelligence Layer Support
    tags: List[str] = field(default_factory=list)
    confidence_score: float = 0.0     # Source trust score (0–1)

    # Governance & Metadata
    ingested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: Optional[str] = None
    data_lineage: Optional[str] = None     # source tracking
    source_type: Optional[str] = None      # PDF | PORTAL | API | MANUAL

    # System Control
    visibility: str = "PUBLIC"        # PUBLIC | INTERNAL
    access_level: str = "OPEN"        # OPEN | RESTRICTED
    retention_policy: str = "PERMANENT"

    # AI Support Layer (non-authoritative)
    embedding_id: Optional[str] = None
    vector_status: str = "PENDING"    # PENDING | INDEXED | FAILED
