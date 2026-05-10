"""
Deduplication Engine
---------------------
Purpose:
- Remove exact duplicate scheme records (by scheme_id hash)
- Detect near-duplicate scheme names using string similarity
- Maintain dedup statistics for pipeline reporting
- Act as a data quality gate between validation and storage

This prevents data pollution from duplicate ingestion runs.
"""

import os
from difflib import SequenceMatcher
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


class DedupEngine:

    def __init__(self, similarity_threshold: float = float(os.getenv('DEDUP_SIMILARITY_THRESHOLD', '0.85'))):
        self.similarity_threshold = similarity_threshold
        self.stats = {
            "total_in": 0,
            "exact_duplicates": 0,
            "near_duplicates": 0,
            "total_out": 0,
        }

    def deduplicate(self, records: List[Dict]) -> List[Dict]:
        self.stats["total_in"] = len(records)

        unique = self._exact_dedup(records)
        unique = self._fuzzy_dedup(unique)

        self.stats["total_out"] = len(unique)
        return unique

    def _exact_dedup(self, records: List[Dict]) -> List[Dict]:
        seen = {}
        unique = []
        for record in records:
            rid = record.get("scheme_id", "")
            if rid not in seen:
                seen[rid] = True
                unique.append(record)
            else:
                self.stats["exact_duplicates"] += 1
        return unique

    def _fuzzy_dedup(self, records: List[Dict]) -> List[Dict]:
        unique = []
        for record in records:
            name = (record.get("name") or "").lower().strip()
            is_dup = False
            for existing in unique:
                existing_name = (existing.get("name") or "").lower().strip()
                ratio = SequenceMatcher(None, name, existing_name).ratio()
                if ratio >= self.similarity_threshold:
                    is_dup = True
                    self.stats["near_duplicates"] += 1
                    break
            if not is_dup:
                unique.append(record)
        return unique

    def report(self):
        print("\n--- Dedup Report ---")
        for k, v in self.stats.items():
            print(f"  {k}: {v}")
