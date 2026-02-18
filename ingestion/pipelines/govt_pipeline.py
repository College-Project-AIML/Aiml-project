
"""
Government Ingestion Pipeline (GIP)
-----------------------------------
Purpose:
- Orchestrate all government data ingestion flows
- Coordinate sources
- Enforce governance
- Control normalization
- Enforce validation
- Manage failures safely
- Maintain data integrity
- Act as ingestion control plane

This is the ingestion brain of Aiml-project.
"""

from datetime import datetime
import traceback

# Sources
from ingestion.sources.central.scholarships_gov_in import scrape as central_scraper
from ingestion.sources.karnataka.scholarship_pdf_ingestor import parse_pdf as karnataka_parser

# Core layers
from ingestion.normalizers.scheme_normalizer import SchemeNormalizer
from ingestion.validators.scheme_validator import SchemeValidator, ValidationError

# Storage
from ingestion.storage.storage_adapter import StorageAdapter   # you will implement next

# -----------------------------
# Pipeline Controller
# -----------------------------

class GovtIngestionPipeline:

    def __init__(self):
        self.normalizer = SchemeNormalizer()
        self.validator = SchemeValidator()
        self.storage = StorageAdapter()

        self.stats = {
            "fetched": 0,
            "normalized": 0,
            "validated": 0,
            "stored": 0,
            "failed": 0,
            "start_time": datetime.utcnow().isoformat()
        }

    # -----------------------------
    # Public Entry
    # -----------------------------

    def run(self):
        print("\n=== Govt Ingestion Pipeline Started ===\n")

        self._run_central_sources()
        self._run_state_sources()

        self.stats["end_time"] = datetime.utcnow().isoformat()

        self._report()

    # -----------------------------
    # Source Groups
    # -----------------------------

    def _run_central_sources(self):
        print("[Central Sources] Starting...")

        try:
            raw_records = central_scraper()
            self._process_records(raw_records, source_group="CENTRAL")

        except Exception as e:
            print("[Central Sources] FAILED")
            traceback.print_exc()

    def _run_state_sources(self):
        print("[State Sources] Starting...")

        try:
            raw_records = karnataka_parser()
            self._process_records(raw_records, source_group="KARNATAKA")

        except Exception as e:
            print("[State Sources] FAILED")
            traceback.print_exc()

    # -----------------------------
    # Core Processing
    # -----------------------------

    def _process_records(self, raw_records, source_group):
        for raw in raw_records:
            self.stats["fetched"] += 1

            try:
                normalized = self.normalizer.normalize(raw)
                self.stats["normalized"] += 1

                validated = self.validator.validate(normalized)
                self.stats["validated"] += 1

                self.storage.save(validated)
                self.stats["stored"] += 1

            except ValidationError as ve:
                self.stats["failed"] += 1
                self._log_failure(raw, ve, stage="VALIDATION", source_group=source_group)

            except Exception as e:
                self.stats["failed"] += 1
                self._log_failure(raw, e, stage="PIPELINE", source_group=source_group)

    # -----------------------------
    # Governance & Logging
    # -----------------------------

    def _log_failure(self, raw, error, stage, source_group):
        log = {
            "time": datetime.utcnow().isoformat(),
            "stage": stage,
            "source_group": source_group,
            "error": str(error),
            "raw_record": raw
        }

        print("\n[PIPELINE ERROR]")
        print(log)

        # Future:
        # self.storage.log_failure(log)
        # self.audit.log(log)

    def _report(self):
        print("\n=== Ingestion Report ===")
        for k, v in self.stats.items():
            print(f"{k}: {v}")
        print("========================\n")


# -----------------------------
# Execution
# -----------------------------

if __name__ == "__main__":
    pipeline = GovtIngestionPipeline()
    pipeline.run()
