"""
Karnataka State Ingestion Pipeline
------------------------------------
Purpose:
- Orchestrate end-to-end ingestion of Karnataka government scheme data
- Load raw data from scholarships_api_dump.json or generate sample data
- Normalize → Validate → Deduplicate → Save to JSON + PostgreSQL
- Provide comprehensive pipeline statistics and reporting
- Act as a state-level ingestion controller

This is the Karnataka-specific ingestion brain.
"""

import os
import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ingestion.normalizers.scheme_normalizer import SchemeNormalizer
from ingestion.validators.scheme_validator import SchemeValidator, ValidationError
from ingestion.dedup.dedup_engine import DedupEngine
from ingestion.loaders.json_loader import JsonLoader
from ingestion.loaders.postgres_loader import PostgresLoader
from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = os.getenv("OUTPUT_PATH", "data/gov/karnataka/schemes.json")
DUMP_PATH = os.getenv("DUMP_PATH", "scholarships_api_dump.json")


class KarnatakaPipeline:

    def __init__(self, raw_records=None, skip_postgres=False):
        self.raw_records = raw_records
        self.skip_postgres = skip_postgres
        self.normalizer = SchemeNormalizer()
        self.validator = SchemeValidator()
        self.dedup = DedupEngine()
        self.json_loader = JsonLoader()
        self.stats = {
            "raw": 0, "normalized": 0, "validated": 0,
            "deduped": 0, "failed": 0, "errors": []
        }

    def run(self):
        start = datetime.utcnow()
        print("\n=== Karnataka Pipeline Started ===\n")

        raw = self._load_raw_data()
        self.stats["raw"] = len(raw)
        print(f"[1/5] Loaded {len(raw)} raw records")

        normalized = []
        for r in raw:
            try:
                normalized.append(self.normalizer.normalize(r))
                self.stats["normalized"] += 1
            except Exception as e:
                self.stats["failed"] += 1
                self.stats["errors"].append(f"Normalize: {e}")
        print(f"[2/5] Normalized {len(normalized)} records")

        validated = []
        for n in normalized:
            try:
                validated.append(self.validator.validate(n))
                self.stats["validated"] += 1
            except ValidationError as e:
                self.stats["failed"] += 1
                self.stats["errors"].append(f"Validate: {e}")
        print(f"[3/5] Validated {len(validated)} records")

        deduped = self.dedup.deduplicate(validated)
        self.stats["deduped"] = len(deduped)
        print(f"[4/5] Deduped to {len(deduped)} records")

        self.json_loader.save(deduped, OUTPUT_PATH)

        if not self.skip_postgres:
            try:
                pg = PostgresLoader()
                pg.load(deduped)
                pg.report()
                pg.close()
            except Exception as e:
                print(f"[PostgreSQL] Skipped: {e}")
        else:
            print("[5/5] PostgreSQL load skipped")

        duration = (datetime.utcnow() - start).total_seconds()
        self._report(duration)

    def _load_raw_data(self):
        if self.raw_records:
            return self.raw_records

        if os.path.exists(DUMP_PATH):
            with open(DUMP_PATH, "r") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data

        print("[Pipeline] No external data found, using sample data")
        return self._generate_sample_data()

    def _generate_sample_data(self):
        return [
            {
                "scheme_name": "Vidyasiri Scholarship for SC/ST Students",
                "source": "dce.karnataka.gov.in",
                "category": "scholarship",
                "ministry": "Department of Collegiate Education, Karnataka",
                "description": "Financial assistance to SC/ST students pursuing higher education in Karnataka. Covers tuition fees and provides maintenance allowance.",
                "eligibility": "SC/ST students enrolled in recognized colleges in Karnataka with family income below 2.5 lakh per annum",
                "state": "karnataka",
                "link": "https://dce.karnataka.gov.in",
                "tags": ["sc", "st", "scholarship", "karnataka"]
            },
            {
                "scheme_name": "Post-Matric Scholarship for OBC Students",
                "source": "sw.karnataka.gov.in",
                "category": "scholarship",
                "ministry": "Department of Backward Classes and Minorities, Karnataka",
                "description": "Scholarship for OBC students who have passed matriculation and are pursuing further studies in recognized institutions.",
                "eligibility": "OBC students with family income below 1 lakh, enrolled in post-matric courses",
                "state": "karnataka",
                "link": "https://sw.karnataka.gov.in",
                "tags": ["obc", "scholarship", "karnataka"]
            },
            {
                "scheme_name": "Arivu Educational Loan Scheme for Minorities",
                "source": "sw.karnataka.gov.in",
                "category": "loan",
                "ministry": "Karnataka Minorities Development Corporation",
                "description": "Interest-free educational loan for minority community students pursuing professional and technical courses.",
                "eligibility": "Minority community students with family income below 2.5 lakh pursuing professional courses",
                "state": "karnataka",
                "link": "https://kmdc.karnataka.gov.in",
                "tags": ["minority", "loan", "education", "karnataka"]
            },
            {
                "scheme_name": "Bhagyalakshmi Scheme for Girl Child",
                "source": "dwcd.karnataka.gov.in",
                "category": "welfare",
                "ministry": "Department of Women and Child Development, Karnataka",
                "description": "Financial assistance for girl children from BPL families. Provides a bond of Rs 19,300 at birth which matures to Rs 1,00,034 at age 18.",
                "eligibility": "Girl children born in BPL families in Karnataka, registered within one year of birth",
                "state": "karnataka",
                "link": "https://dwcd.karnataka.gov.in",
                "tags": ["girl", "child", "welfare", "bpl", "karnataka"]
            },
            {
                "scheme_name": "Krishi Yantra Dhare - Farm Equipment Subsidy",
                "source": "raitamitra.karnataka.gov.in",
                "category": "subsidy",
                "ministry": "Department of Agriculture, Karnataka",
                "description": "Subsidy on purchase of agricultural equipment and machinery for farmers in Karnataka. Up to 50% subsidy for small and marginal farmers.",
                "eligibility": "Farmers with landholding in Karnataka, priority to small and marginal farmers",
                "state": "karnataka",
                "link": "https://raitamitra.karnataka.gov.in",
                "tags": ["farmer", "subsidy", "equipment", "karnataka"]
            },
            {
                "scheme_name": "Karnataka Arogya Sanjeevini Health Insurance",
                "source": "suvarna-arogya.karnataka.gov.in",
                "category": "welfare",
                "ministry": "Department of Health and Family Welfare, Karnataka",
                "description": "Cashless health insurance coverage of up to Rs 5 lakh per family per year for BPL families in Karnataka.",
                "eligibility": "BPL families in Karnataka with valid ration card",
                "state": "karnataka",
                "link": "https://suvarna-arogya.karnataka.gov.in",
                "tags": ["health", "insurance", "bpl", "karnataka"]
            },
            {
                "scheme_name": "Sanchi Honnamma Scholarship for Girls",
                "source": "dce.karnataka.gov.in",
                "category": "scholarship",
                "ministry": "Department of Collegiate Education, Karnataka",
                "description": "Merit-based scholarship for girl students from economically weaker sections pursuing undergraduate courses in Karnataka.",
                "eligibility": "Girl students with 60% marks in PUC, family income below 2 lakh",
                "state": "karnataka",
                "link": "https://dce.karnataka.gov.in",
                "tags": ["girls", "merit", "scholarship", "karnataka"]
            },
            {
                "scheme_name": "Devaraj Urs Backward Classes Scholarship",
                "source": "sw.karnataka.gov.in",
                "category": "scholarship",
                "ministry": "Karnataka Backward Classes Welfare Department",
                "description": "Scholarship for students belonging to backward classes pursuing education from Class 1 to Post Graduation.",
                "eligibility": "Students from backward classes with family income below 1 lakh",
                "state": "karnataka",
                "link": "https://sw.karnataka.gov.in",
                "tags": ["backward", "classes", "scholarship", "karnataka"]
            },
            {
                "scheme_name": "Ambedkar Overseas Scholarship for SC/ST",
                "source": "sjd.karnataka.gov.in",
                "category": "scholarship",
                "ministry": "Social Justice Department, Karnataka",
                "description": "Scholarship for SC/ST students to pursue masters or PhD abroad. Covers tuition fees, living expenses, and air travel.",
                "eligibility": "SC/ST students with admission in top 200 QS ranked universities, family income below 6 lakh",
                "state": "karnataka",
                "link": "https://sjd.karnataka.gov.in",
                "tags": ["sc", "st", "overseas", "scholarship", "karnataka"]
            },
            {
                "scheme_name": "Udyogini Scheme for Women Entrepreneurs",
                "source": "dwcd.karnataka.gov.in",
                "category": "subsidy",
                "ministry": "Karnataka State Women's Development Corporation",
                "description": "Loan and subsidy scheme for women entrepreneurs from weaker sections to start or expand small businesses.",
                "eligibility": "Women aged 18-45 from SC/ST/OBC/Minority communities with family income below 1.5 lakh",
                "state": "karnataka",
                "link": "https://kswdc.karnataka.gov.in",
                "tags": ["women", "entrepreneur", "subsidy", "karnataka"]
            },
            {
                "scheme_name": "Ganga Kalyana - Irrigation Borewell Scheme",
                "source": "raitamitra.karnataka.gov.in",
                "category": "subsidy",
                "ministry": "Department of Agriculture, Karnataka",
                "description": "Free borewell and pump set for SC/ST farmers for irrigation purposes in Karnataka.",
                "eligibility": "SC/ST farmers with minimum 1 acre land, no existing irrigation source",
                "state": "karnataka",
                "link": "https://raitamitra.karnataka.gov.in",
                "tags": ["farmer", "irrigation", "sc", "st", "karnataka"]
            },
            {
                "scheme_name": "Shaadi Bhagya - Marriage Assistance for Minorities",
                "source": "sw.karnataka.gov.in",
                "category": "welfare",
                "ministry": "Karnataka Minorities Development Corporation",
                "description": "Financial assistance of Rs 50,000 for marriage of daughters from minority BPL families.",
                "eligibility": "Minority community BPL families with daughters aged 18+",
                "state": "karnataka",
                "link": "https://kmdc.karnataka.gov.in",
                "tags": ["minority", "marriage", "welfare", "karnataka"]
            },
            {
                "scheme_name": "Karnataka Skill Development - PMKVY State Component",
                "source": "kaushalya.karnataka.gov.in",
                "category": "skill",
                "ministry": "Department of Skill Development, Karnataka",
                "description": "Free skill training programs aligned with PMKVY in various trades like IT, healthcare, construction, and manufacturing.",
                "eligibility": "Youth aged 18-35, residents of Karnataka, minimum 10th pass",
                "state": "karnataka",
                "link": "https://kaushalya.karnataka.gov.in",
                "tags": ["skill", "training", "youth", "karnataka"]
            },
            {
                "scheme_name": "Mathrushree - Maternity Benefit Scheme",
                "source": "dwcd.karnataka.gov.in",
                "category": "welfare",
                "ministry": "Department of Women and Child Development, Karnataka",
                "description": "Cash incentive of Rs 6,000 for pregnant women from BPL families for institutional delivery.",
                "eligibility": "Pregnant women from BPL families delivering in government hospitals",
                "state": "karnataka",
                "link": "https://dwcd.karnataka.gov.in",
                "tags": ["maternity", "women", "health", "karnataka"]
            },
            {
                "scheme_name": "Kittur Rani Chennamma Award Scholarship",
                "source": "dce.karnataka.gov.in",
                "category": "scholarship",
                "ministry": "Department of Collegiate Education, Karnataka",
                "description": "Scholarship for meritorious girl students from rural areas pursuing higher education in Karnataka.",
                "eligibility": "Girl students from rural areas with 75% marks, family income below 2 lakh",
                "state": "karnataka",
                "link": "https://dce.karnataka.gov.in",
                "tags": ["girls", "rural", "merit", "scholarship", "karnataka"]
            },
            {
                "scheme_name": "National Means-cum-Merit Scholarship (Karnataka Quota)",
                "source": "scholarships.gov.in",
                "category": "scholarship",
                "ministry": "Government of India - Ministry of Education",
                "description": "Scholarship of Rs 12,000 per annum for meritorious students from economically weaker sections to reduce dropout rate at class VIII.",
                "eligibility": "Students scoring 55%+ in Class VII exam, family income below 3.5 lakh per annum",
                "state": "karnataka",
                "link": "https://scholarships.gov.in",
                "tags": ["merit", "scholarship", "national", "karnataka"]
            },
            {
                "scheme_name": "PM Scholarship Scheme for Karnataka Students",
                "source": "scholarships.gov.in",
                "category": "scholarship",
                "ministry": "Government of India - Ministry of Defence",
                "description": "Scholarship for wards and widows of ex-servicemen from Karnataka. Rs 3,000/month for boys and Rs 3,600/month for girls.",
                "eligibility": "Wards/widows of ex-servicemen/ex-coast guard, minimum 60% in qualifying exam",
                "state": "karnataka",
                "link": "https://scholarships.gov.in",
                "tags": ["defence", "exservicemen", "scholarship", "karnataka"]
            },
            {
                "scheme_name": "Anila Bhagya - Free LPG Connection Scheme",
                "source": "food.karnataka.gov.in",
                "category": "subsidy",
                "ministry": "Department of Food and Civil Supplies, Karnataka",
                "description": "Free LPG gas connection and initial cylinder for BPL families who do not have LPG connection.",
                "eligibility": "BPL families without existing LPG connection, valid BPL ration card",
                "state": "karnataka",
                "link": "https://food.karnataka.gov.in",
                "tags": ["lpg", "gas", "bpl", "subsidy", "karnataka"]
            },
            {
                "scheme_name": "Karnataka PhD Fellowship for SC/ST Researchers",
                "source": "sjd.karnataka.gov.in",
                "category": "fellowship",
                "ministry": "Social Justice Department, Karnataka",
                "description": "Fellowship for SC/ST candidates pursuing PhD in recognized universities in Karnataka. Provides monthly stipend and research grant.",
                "eligibility": "SC/ST candidates with admission for PhD in recognized Karnataka universities",
                "state": "karnataka",
                "link": "https://sjd.karnataka.gov.in",
                "tags": ["phd", "fellowship", "sc", "st", "research", "karnataka"]
            },
            {
                "scheme_name": "CM Housing Scheme for Economically Weaker Sections",
                "source": "housing.karnataka.gov.in",
                "category": "welfare",
                "ministry": "Karnataka Housing Board",
                "description": "Affordable housing for economically weaker sections with subsidy up to Rs 2.5 lakh for construction or purchase of dwelling unit.",
                "eligibility": "EWS families with annual income below 3 lakh, no existing house ownership",
                "state": "karnataka",
                "link": "https://housing.karnataka.gov.in",
                "tags": ["housing", "ews", "subsidy", "karnataka"]
            },
        ]

    def _report(self, duration):
        print(f"\n=== Karnataka Pipeline Report ===")
        print(f"  Duration: {duration:.2f}s")
        for k, v in self.stats.items():
            if k != "errors":
                print(f"  {k}: {v}")
        if self.stats["errors"]:
            print(f"  Errors ({len(self.stats['errors'])}):")
            for e in self.stats["errors"][:5]:
                print(f"    - {e}")
        self.dedup.report()
        print("=================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Karnataka Schemes Pipeline")
    parser.add_argument("--skip-postgres", action="store_true", help="Skip PostgreSQL loading")
    parser.add_argument("--input", type=str, help="Path to input JSON file")
    args = parser.parse_args()

    raw = None
    if args.input:
        with open(args.input) as f:
            raw = json.load(f)

    pipeline = KarnatakaPipeline(raw_records=raw, skip_postgres=args.skip_postgres)
    pipeline.run()
