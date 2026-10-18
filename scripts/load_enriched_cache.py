#!/usr/bin/env python3
"""
Load Enriched Cache into Postgres (Ultra-Fast Batch Mode)
-----------------------------------------------------------
Reads data/enriched_cache/myscheme_enriched.json and performs
bulk upserts into Postgres using psycopg2.extras.execute_values.

Features:
- High speed: uses multi-row SQL execute_values (~1s per batch of 150 schemes)
- Batched commits: commits every batch so progress is immediate and resilient
- Reconnects automatically on network hiccups
- Full upserts: schemes.eligibility_text, eligibility_rules, benefits, documents_required

Usage:
    python scripts/load_enriched_cache.py [--batch-size 150]
"""

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import execute_values
from ingestion.loaders.postgres_loader import resolve_database_url

CACHE_FILE = Path("data/enriched_cache/myscheme_enriched.json")


def deterministic_uuid(value: str) -> str:
    h = hashlib.sha256(value.encode()).hexdigest()[:32]
    return str(uuid.UUID(h))


def get_connection():
    db_url = resolve_database_url()
    return psycopg2.connect(db_url)


def main():
    parser = argparse.ArgumentParser(description="Bulk load enrichment cache into Postgres")
    parser.add_argument("--batch-size", type=int, default=150, help="Batch size (default: 150)")
    args = parser.parse_args()

    if not CACHE_FILE.exists():
        print(f"ERROR: Cache file not found: {CACHE_FILE}")
        sys.exit(1)

    print(f"Reading cache from {CACHE_FILE}...")
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)

    enriched = {slug: data for slug, data in cache.items()
                if not data.get("empty") and not data.get("error")}
    print(f"Cache entries: {len(cache)} | Enriched schemes: {len(enriched)}")

    # Load mapping from DB
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, link FROM schemes
        WHERE source = 'myscheme.gov.in' OR source LIKE '%myscheme%'
    """)
    slug_to_id = {}
    for r in cur.fetchall():
        link = r[1] or ""
        slug = link.rstrip("/").split("/")[-1] if link else ""
        if slug:
            slug_to_id[slug] = str(r[0])

    cur.execute("SELECT id FROM schemes")
    all_ids = {str(r[0]) for r in cur.fetchall()}
    print(f"Mapped {len(slug_to_id)} schemes in DB")

    items = list(enriched.items())
    total = len(items)
    batch_size = args.batch_size
    t0 = time.time()
    total_updated = 0

    for idx in range(0, total, batch_size):
        chunk = items[idx:idx + batch_size]

        scheme_updates = []
        rule_rows = []
        benefit_rows = []
        doc_rows = []

        for slug, data in chunk:
            sid = slug_to_id.get(slug)
            if not sid:
                candidate = deterministic_uuid(f"myscheme.gov.in:{slug}")
                if candidate in all_ids:
                    sid = candidate

            if not sid:
                continue

            total_updated += 1

            # 1. Eligibility text
            elig_text = data.get("eligibility_text")
            if elig_text:
                scheme_updates.append((sid, elig_text))

            # 2. Eligibility rules
            rules = data.get("eligibility_rules")
            if rules:
                rid = deterministic_uuid(f"elig:{sid}")
                rule_rows.append((
                    rid, sid, rules.get("min_age"), rules.get("max_age"),
                    rules.get("max_income"), rules.get("gender"),
                    rules.get("caste"), rules.get("states"),
                    rules.get("education_level")
                ))

            # 3. Benefits
            for b_idx, b in enumerate(data.get("benefits", [])):
                bid = deterministic_uuid(f"benefit:{sid}:{b_idx}")
                benefit_rows.append((
                    bid, sid, b.get("benefit_type", "financial"),
                    b.get("description"), b.get("amount"), b.get("frequency", "annual")
                ))

            # 4. Documents
            for d_idx, d in enumerate(data.get("documents", [])):
                did = deterministic_uuid(f"doc:{sid}:{d_idx}")
                doc_rows.append((
                    did, sid, d.get("document_name"), d.get("is_mandatory", True)
                ))

        # Execute batch with retry
        for attempt in range(5):
            try:
                if scheme_updates:
                    execute_values(cur, """
                        UPDATE schemes AS s SET
                            eligibility_text = v.elig_text
                        FROM (VALUES %s) AS v(scheme_id, elig_text)
                        WHERE s.id = v.scheme_id::uuid
                    """, scheme_updates, page_size=200)

                if rule_rows:
                    execute_values(cur, """
                        INSERT INTO eligibility_rules (
                            id, scheme_id, min_age, max_age, max_income,
                            gender, caste, states, education_level
                        ) VALUES %s
                        ON CONFLICT (id) DO UPDATE SET
                            min_age = EXCLUDED.min_age,
                            max_age = EXCLUDED.max_age,
                            max_income = EXCLUDED.max_income,
                            gender = EXCLUDED.gender,
                            caste = EXCLUDED.caste,
                            states = EXCLUDED.states,
                            education_level = EXCLUDED.education_level,
                            updated_at = CURRENT_TIMESTAMP
                    """, rule_rows, page_size=200)

                if benefit_rows:
                    execute_values(cur, """
                        INSERT INTO benefits (
                            id, scheme_id, benefit_type, description, amount, frequency
                        ) VALUES %s
                        ON CONFLICT (id) DO UPDATE SET
                            benefit_type = EXCLUDED.benefit_type,
                            description = EXCLUDED.description,
                            amount = EXCLUDED.amount,
                            frequency = EXCLUDED.frequency,
                            updated_at = CURRENT_TIMESTAMP
                    """, benefit_rows, page_size=300)

                if doc_rows:
                    execute_values(cur, """
                        INSERT INTO documents_required (
                            id, scheme_id, document_name, is_mandatory
                        ) VALUES %s
                        ON CONFLICT (id) DO UPDATE SET
                            document_name = EXCLUDED.document_name,
                            is_mandatory = EXCLUDED.is_mandatory,
                            updated_at = CURRENT_TIMESTAMP
                    """, doc_rows, page_size=500)

                conn.commit()
                break

            except Exception as e:
                try:
                    conn.rollback()
                    conn.close()
                except Exception:
                    pass
                print(f"  Warning on batch {idx//batch_size + 1} (attempt {attempt + 1}/5): {e}")
                time.sleep(1.5 * (attempt + 1))
                conn = get_connection()
                cur = conn.cursor()

        processed_so_far = min(idx + batch_size, total)
        elapsed = time.time() - t0
        rate = processed_so_far / elapsed if elapsed > 0 else 0
        print(f"[{processed_so_far}/{total}] Synced {total_updated} schemes ({rate:.1f} schemes/s, {elapsed:.1f}s elapsed)")

    cur.close()
    conn.close()

    elapsed = time.time() - t0
    print()
    print("=" * 60)
    print("ULTRA-FAST ENRICHMENT LOAD COMPLETE")
    print("=" * 60)
    print(f"  Total enriched schemes: {total}")
    print(f"  Postgres updated:       {total_updated}")
    print(f"  Total execution time:   {elapsed:.1f}s ({elapsed / 60:.1f}m)")
    print("=" * 60)


if __name__ == "__main__":
    main()
