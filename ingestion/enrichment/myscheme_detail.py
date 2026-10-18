"""
MyScheme Detail Enrichment
---------------------------
Fetches detailed scheme data from MyScheme's apisetu API using slugs from search results.
Enriches schemes with: eligibility criteria, benefits, documents, application process, etc.
"""

import logging
import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

APISETU_BASE = "https://www.myscheme.gov.in/api/apisetu/schemes"

DEFAULT_HEADERS = {
    "User-Agent": "Aiml-project-schemes-ingestion/1.0",
    "Accept": "application/json",
    "Origin": "https://www.myscheme.gov.in",
    "Referer": "https://www.myscheme.gov.in/",
}


@dataclass
class EnrichedScheme:
    scheme_id: str
    slug: str
    mongo_id: str
    basic_details: Dict
    eligibility_criteria: Dict
    scheme_content: Dict
    application_process: List
    scheme_definitions: List
    documents: Dict
    faqs: Dict


class MySchemeDetailEnricher:
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._last_request = 0.0

    def _rate_limited_get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """GET with rate limiting."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        try:
            resp = self.session.get(url, params=params, timeout=20)
            self._last_request = time.time()
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"API error {resp.status_code} for {url}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Request failed for {url}: {e}")
        return None

    def fetch_scheme_detail(self, slug: str, include_faqs: bool = False) -> Optional[EnrichedScheme]:
        """Fetch full detail for a scheme by slug."""
        # First, get the main detail which includes MongoDB _id
        url = f"{APISETU_BASE}"
        params = {"slug": slug, "lang": "en"}
        main = self._rate_limited_get(url, params)
        
        if not main or "data" not in main or not main["data"] or "_id" not in main["data"]:
            logger.warning(f"No detail data for slug: {slug}")
            return None
        
        mongo_id = main["data"]["_id"]
        en = main["data"].get("en", {})
        
        # Fetch documents
        doc_url = f"{APISETU_BASE}/{mongo_id}/documents"
        doc_data = self._rate_limited_get(doc_url, {"lang": "en"})
        
        # Fetch FAQs (only if requested)
        faq_en = {}
        if include_faqs:
            faq_url = f"{APISETU_BASE}/{mongo_id}/faqs"
            faq_data = self._rate_limited_get(faq_url, {"lang": "en"})
            if faq_data and isinstance(faq_data, dict):
                faq_en = faq_data.get("data", {}).get("en", {}) or {}
        
        # Handle None responses gracefully
        doc_en = {}
        if doc_data and isinstance(doc_data, dict):
            doc_en = doc_data.get("data", {}).get("en", {}) or {}
        
        return EnrichedScheme(
            scheme_id=mongo_id,
            slug=slug,
            mongo_id=mongo_id,
            basic_details=en.get("basicDetails", {}),
            eligibility_criteria=en.get("eligibilityCriteria", {}),
            scheme_content=en.get("schemeContent", {}),
            application_process=en.get("applicationProcess", []),
            scheme_definitions=en.get("schemeDefinitions", []),
            documents=doc_en,
            faqs=faq_en,
        )

    def parse_eligibility(self, criteria: Dict) -> Dict:
        """Parse eligibility criteria into structured rules."""
        if not criteria:
            return {}
        
        md = criteria.get("eligibilityDescription_md", "")
        if not md:
            return {}
        
        rules = {
            "min_age": None,
            "max_age": None,
            "max_income": None,
            "gender": None,
            "caste": None,
            "states": None,
            "education_level": None,
        }
        
        import re
        text = md.lower()
        
        # Age range: e.g. "between 18 and 70 years", "age 18 to 60 years", "18-50 years"
        range_match = re.search(r'between\s+(\d{1,2})\s*(?:years?|yrs?)?[^\d\n]*?(?:and|to|-)\s*(\d{1,2})\s*(?:years?|yrs?)', text)
        if not range_match:
            range_match = re.search(r'(?:age(?:d)?\s*:?\s*)(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s*(?:years?|yrs?)', text)
        
        if range_match:
            rules["min_age"] = int(range_match.group(1))
            rules["max_age"] = int(range_match.group(2))
        else:
            # Min age: "at least 18 years", "minimum age of 18", "18 years and above", "age 18 years"
            min_match = re.search(r'(?:at\s+least|minimum(?:\s+age)?(?:\s+of)?|above|not\s+less\s+than)\s*(\d{1,2})\s*(?:years?|yrs?)', text)
            if not min_match:
                min_match = re.search(r'(\d{1,2})\s*(?:years?|yrs?)\s*(?:and\s+above|or\s+older|or\s+above)', text)
            if not min_match:
                min_match = re.search(r'age\s*(?:is|must\s+be|of)?\s*(\d{1,2})\s*(?:years?|yrs?)', text)
            if min_match:
                rules["min_age"] = int(min_match.group(1))

            # Max age: "maximum age of 60", "up to 60 years", "not exceeding 50 years", "below 35 years"
            max_match = re.search(r'(?:maximum(?:\s+age)?(?:\s+of)?|up\s*to|upto|not\s+exceeding|below|less\s+than)\s*(\d{1,2})\s*(?:years?|yrs?)', text)
            if max_match:
                rules["max_age"] = int(max_match.group(1))

        # Income
        income_matches = re.findall(r'income.*?(\d+(?:\.\d+)?)\s*(?:lakh|lac|crore)', text, re.IGNORECASE)
        if income_matches:
            val = float(income_matches[0])
            if 'lakh' in text or 'lac' in text:
                val *= 100000
            elif 'crore' in text:
                val *= 10000000
            rules["max_income"] = val
        else:
            # Direct numeric income: "income not exceeding Rs 2,50,000"
            num_match = re.search(r'income[^\n\.\;]*?(?:rs\.?|inr|₹)\s*([\d,]+)', text)
            if num_match:
                try:
                    val = float(num_match.group(1).replace(',', ''))
                    if val >= 5000:
                        rules["max_income"] = val
                except ValueError:
                    pass
        
        # Gender
        if 'female' in text or 'women' in text or 'girl' in text or 'widow' in text:
            if 'male' not in text and 'men' not in text:
                rules["gender"] = ["female"]
        elif 'transgender' in text:
            rules["gender"] = ["transgender"]
        
        # Caste - use word boundaries to avoid partial matches
        caste_patterns = {
            r'\bsc\b': 'SC', r'\bscheduled caste\b': 'SC',
            r'\bst\b': 'ST', r'\bscheduled tribe\b': 'ST',
            r'\bobc\b': 'OBC', r'\bother backward\b': 'OBC',
            r'\bgeneral\b': 'general', r'\bminority\b': 'minority'
        }
        found = [caste_patterns[p] for p in caste_patterns if re.search(p, text, re.IGNORECASE)]
        if found:
            rules["caste"] = list(set(found))
        
        # Education
        edu_keywords = {
            '10th': '10th_pass', 'matric': '10th_pass', 'ssc': '10th_pass',
            '12th': '12th_pass', 'puc': '12th_pass', 'hsc': '12th_pass',
            'graduate': 'graduate', 'graduation': 'graduate', 'degree': 'graduate',
            'post graduate': 'post_graduate', 'masters': 'post_graduate', 'phd': 'post_graduate',
            'diploma': 'diploma', 'iti': 'diploma'
        }
        for kw, level in edu_keywords.items():
            if kw in text:
                rules["education_level"] = level
                break
        
        # Only return non-empty rules
        return {k: v for k, v in rules.items() if v not in (None, [])}

    def parse_benefits(self, content: Dict) -> List[Dict]:
        """Parse benefits from schemeContent."""
        if not content:
            return []
        
        benefits = []
        md = content.get("benefits_md", "")
        benefits_list = content.get("benefits", [])
        
        # Use markdown as primary source
        if md:
            import re
            items = re.findall(r'(?:^|\n)\d+\.\s*(.+?)(?=\n\d+\.|$)', md, re.DOTALL)
            for item in items:
                benefits.append({
                    "benefit_type": "financial",
                    "description": item.strip().replace('\n', ' '),
                    "amount": None,
                    "frequency": "annual",
                })
        
        # Also parse structured benefits if available
        if benefits_list and isinstance(benefits_list, list):
            for b in benefits_list:
                if isinstance(b, dict):
                    # Extract text from nested children structure
                    text = self._extract_text_from_children(b.get("children", []))
                    if text:
                        benefits.append({
                            "benefit_type": "financial",
                            "description": text,
                            "amount": None,
                            "frequency": "annual",
                        })
        
        return benefits

    def parse_documents(self, doc_data: Dict) -> List[Dict]:
        """Parse required documents from documents endpoint."""
        if not doc_data:
            return []
        
        documents = []
        md = doc_data.get("documentsRequired_md", "")
        docs_list = doc_data.get("documents_required", [])
        
        if md:
            import re
            # Parse markdown list items
            lines = md.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '-', '•'))):
                    # Remove numbering
                    cleaned = re.sub(r'^[\d\.\-\•\s]+', '', line).strip()
                    if cleaned:
                        documents.append({
                            "document_name": cleaned,
                            "is_mandatory": True,
                        })
        
        if docs_list and isinstance(docs_list, list):
            for d in docs_list:
                if isinstance(d, dict):
                    text = self._extract_text_from_children(d.get("children", []))
                    if text:
                        documents.append({
                            "document_name": text,
                            "is_mandatory": True,
                        })
        
        # Deduplicate by name
        seen = set()
        unique = []
        for d in documents:
            name = d["document_name"]
            if name not in seen:
                seen.add(name)
                unique.append(d)
        
        return unique

    def _extract_text_from_children(self, children: List) -> str:
        """Extract plain text from nested children structure."""
        texts = []
        for child in children:
            if isinstance(child, dict):
                if "text" in child:
                    texts.append(child["text"])
                if "children" in child:
                    texts.append(self._extract_text_from_children(child["children"]))
        return " ".join(texts).strip()

    def enrich_record(self, raw_record: Dict, enriched: EnrichedScheme) -> Dict:
        """Merge enriched data into normalized record."""
        if enriched is None:
            return raw_record
            
        record = raw_record.copy()
        
        # Update eligibility_text with detailed criteria
        ec = enriched.eligibility_criteria or {}
        if ec:
            md = ec.get("eligibilityDescription_md", "")
            if md and not record.get("eligibility_text"):
                record["eligibility_text"] = md
            
            # Parse structured eligibility rules
            record["eligibility_rules"] = self.parse_eligibility(ec)
        
        # Add benefits
        record["benefits"] = self.parse_benefits(enriched.scheme_content or {})
        
        # Add documents
        record["documents"] = self.parse_documents(enriched.documents or {})
        
        # Add application process
        if enriched.application_process:
            process_text = []
            for p in enriched.application_process:
                if isinstance(p, dict):
                    text = self._extract_text_from_children(p.get("process", []))
                    if text:
                        process_text.append(f"Mode: {p.get('mode', '')}\n{text}")
            if process_text:
                record["application_process"] = "\n\n".join(process_text)
        
        # Add basic details
        basic = enriched.basic_details
        if basic:
            # Update ministry/implementing agency
            if basic.get("implementingAgency"):
                record["ministry"] = basic["implementingAgency"]
            # Add dates
            if basic.get("schemeOpenDate"):
                record["start_date"] = basic["schemeOpenDate"]
            if basic.get("schemeCloseDate"):
                record["deadline"] = basic["schemeCloseDate"]
            # Add sub-category/tags
            if basic.get("schemeSubCategory"):
                subcats = [s.get("label", "") for s in basic["schemeSubCategory"] if isinstance(s, dict)]
                if subcats:
                    record["tags"] = list(set(record.get("tags", []) + subcats))
        
        # Add raw_extras for traceability
        record.setdefault("raw_extras", {}).update({
            "mongo_id": enriched.mongo_id,
            "slug": enriched.slug,
            "has_detail": True,
        })
        
        return record


def enrich_schemes(raw_records: List[Dict], rate_limit: float = 1.0) -> List[Dict]:
    """Enrich a list of raw scheme records with detail data."""
    enricher = MySchemeDetailEnricher(rate_limit=rate_limit)
    enriched_records = []
    
    
    for i, record in enumerate(raw_records):
        
        slug = record.get("slug") or record.get("link", "").split("/")[-1]
        if not slug:
            logger.warning(f"Record {i} has no slug, skipping enrichment")
            enriched_records.append(record)
            continue
        
        logger.info(f"Enriching {i+1}/{len(raw_records)}: {slug}")
        
        try:
            
            enriched = enricher.fetch_scheme_detail(slug)
            
            
            if enriched:
                
                record = enricher.enrich_record(record, enriched)
                
            else:
                record["raw_extras"] = record.get("raw_extras", {})
                record["raw_extras"]["has_detail"] = False
        except Exception as e:
            logger.warning(f"Enrichment failed for {slug}: {e}")
            record["raw_extras"] = record.get("raw_extras", {})
            record["raw_extras"]["has_detail"] = False
            record["raw_extras"]["enrichment_error"] = str(e)
        
        enriched_records.append(record)
    
    return enriched_records