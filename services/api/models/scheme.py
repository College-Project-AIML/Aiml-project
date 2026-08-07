"""
Pydantic models for request / response validation.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SchemeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    eligibility_text: Optional[str] = None
    state_code: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    link: Optional[str] = None
    tags: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    category_name: Optional[str] = None
    provider_name: Optional[str] = None
    last_updated: Optional[datetime] = None
    is_new: bool = False


class EligibilityRuleResponse(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    max_income: Optional[float] = None
    gender: Optional[List[str]] = None
    caste: Optional[List[str]] = None
    states: Optional[List[str]] = None
    education_level: Optional[str] = None


class BenefitResponse(BaseModel):
    benefit_type: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None


class DocumentRequiredResponse(BaseModel):
    document_name: str
    is_mandatory: Optional[bool] = True


class SchemeDetailResponse(SchemeResponse):
    eligibility_rules: List[EligibilityRuleResponse] = []
    benefits: List[BenefitResponse] = []
    documents_required: List[DocumentRequiredResponse] = []


class SchemeListResponse(BaseModel):
    schemes: List[SchemeResponse]
    total: int
    page: int
    limit: int


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    scheme_count: int = 0


class EligibilityCheckRequest(BaseModel):
    age: Optional[int] = None
    income: Optional[float] = None
    gender: Optional[str] = None
    caste: Optional[str] = None
    state: Optional[str] = None
    education_level: Optional[str] = None


class EligibilityMatchResponse(BaseModel):
    scheme: SchemeResponse
    match_reason: str


class EligibilityCheckResponse(BaseModel):
    matches: List[EligibilityMatchResponse]
    total_matches: int


class SearchResponse(BaseModel):
    results: List[SchemeResponse]
    query: str
    total: int


class SchemeUpdateResponse(BaseModel):
    change_type: str
    changed_fields: Optional[dict] = None
    detected_at: Optional[datetime] = None
    scheme: Optional[SchemeResponse] = None


class UpdatesListResponse(BaseModel):
    updates: List[SchemeUpdateResponse]
    total: int
