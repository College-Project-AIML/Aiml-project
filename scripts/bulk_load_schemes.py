#!/usr/bin/env python3
"""
Phase 1: Bulk Load All MyScheme Schemes from Raw Snapshot
----------------------------------------------------------
Loads all ~4,772 schemes from the latest raw snapshot into Postgres
WITHOUT making any API calls. Gets schemes on the portal immediately.

Enrichment (eligibility, benefits, documents) is handled separately
by bulk_enrich_and_cache.py.

Usage:
    python scripts/bulk_load_schemes.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from ingestion.normalizers.scheme_normalizer import SchemeNormalizer
from ingestion.validators.scheme_validator import SchemeValidator
from ingestion.dedup.dedup_engine import DedupEngine
from ingestion.loaders.postgres_loader import PostgresLoader


def load_latest_snapshot():
    """Load the latest raw MyScheme snapshot from disk."""
    latest_path = os.path.join("data", "raw", "myscheme", "latest.json")
    if not os.path.exists(latest_path):
        print("ERROR: No raw snapshot found at data/raw/myscheme/latest.json")
        print("Run the MyScheme sync first to fetch schemes.")
        sys.exit(1)

    with open(latest_path) as f:
        meta = json.load(f)

    snapshot_dir = meta["dir"]
    schemes_path = os.path.join(snapshot_dir, "schemes.json")

    if not os.path.exists(schemes_path):
        print(f"ERROR: Snapshot file not found: {schemes_path}")
        sys.exit(1)

    with open(schemes_path) as f:
        records = json.load(f)

    print(f"Loaded {len(records)} records from snapshot: {snapshot_dir}")
    return records


def main():
    start = time.time()

    # 1. Load raw snapshot
    print("=" * 60)
    print("PHASE 1: Bulk Load MyScheme Schemes into Postgres")
    print("=" * 60)
    raw_records = load_latest_snapshot()

    # 2. Normalize & validate
    print("\nNormalizing and validating...")
    normalizer = SchemeNormalizer()
    validator = SchemeValidator()

    normalized = []
    for r in raw_records:
        rec = normalizer.normalize(r)
        normalized.append(validator.validate(rec))

    # 3. Deduplicate
    dedup = DedupEngine()
    records = dedup.deduplicate(normalized)
    print(f"After dedup: {len(records)} unique records")

    # 4. Load into Postgres in chunks
    chunk_size = 200
    total = len(records)
    total_inserted = 0
    total_updated = 0
    total_failed = 0

    for i in range(0, total, chunk_size):
        chunk = records[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        total_chunks = (total + chunk_size - 1) // chunk_size
        print(f"\n  Loading chunk {chunk_num}/{total_chunks} "
              f"(records {i + 1}-{min(i + chunk_size, total)}/{total})...")

        try:
            loader = PostgresLoader()
            loader.load(chunk)
            total_inserted += loader.stats["inserted"]
            total_updated += loader.stats["updated"]
            total_failed += loader.stats["failed"]
            loader.close()
        except Exception as e:
            print(f"  ERROR in chunk {chunk_num}: {e}")
            total_failed += len(chunk)

    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print("BULK LOAD COMPLETE")
    print("=" * 60)
    print(f"  Total records: {total}")
    print(f"  Inserted:      {total_inserted}")
    print(f"  Updated:       {total_updated}")
    print(f"  Failed:        {total_failed}")
    print(f"  Time:          {elapsed:.1f}s")
    print(f"\nAll {total} schemes are now visible on the portal!")
    print("Run scripts/bulk_enrich_and_cache.py next for detailed data.")


if __name__ == "__main__":
    main()
