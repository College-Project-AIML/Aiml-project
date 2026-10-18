#!/usr/bin/env python3
"""
Phase 2: Bulk Enrich & Cache All MyScheme Schemes
---------------------------------------------------
Fetches detailed eligibility, benefits, and documents from the MyScheme
detail API for each scheme in parallel.

Results are:
1. Cached to disk: data/enriched_cache/myscheme_enriched.json (permanently saved)
2. Written directly to Neon Postgres in batches (schemes, eligibility_rules, benefits, documents_required)

Features:
- Parallel fetching (ThreadPoolExecutor) for high throughput
- Auto-reconnecting database writes: handles cloud Postgres drops or transient network blips
- Resumable: automatically skips already-cached schemes
- Batch saving: saves to disk cache and commits to Postgres every batch
- Retries with backoff for API errors
- Safe interrupt: Ctrl+C cleanly flushes cache to disk

Usage:
    python scripts/bulk_enrich_and_cache.py [--workers 8] [--batch-size 50]
"""

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import signal
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from ingestion.enrichment.myscheme_detail import MySchemeDetailEnricher
from ingestion.loaders.postgres_loader import resolve_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("enrich_all.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/enriched_cache")
CACHE_FILE = CACHE_DIR / "myscheme_enriched.json"


def deterministic_uuid(value: str) -> str:
    h = hashlib.sha256(value.encode()).hexdigest()[:32]
    return str(uuid.UUID(h))


def get_db_connection():
    """Get a new Postgres connection."""
    db_url = resolve_database_url()
    return psycopg2.connect(db_url)


def load_cache() -> dict:
    """Load the enrichment cache from disk."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            logger.info(f"Loaded cache with {len(cache)} existing schemes from {CACHE_FILE}")
            return cache
        except Exception as e:
            logger.warning(f"Could not load cache ({e}), starting fresh")
    return {}


def save_cache(cache: dict):
    """Save the enrichment cache to disk atomically."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=None, ensure_ascii=False)
    tmp.rename(CACHE_FILE)


def load_slugs_from_snapshot() -> list:
    """Load all scheme slugs from the latest raw snapshot."""
    latest_path = Path("data/raw/myscheme/latest.json")
    if not latest_path.exists():
        logger.error("No raw snapshot found at data/raw/myscheme/latest.json")
        sys.exit(1)

    with open(latest_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    schemes_path = Path(meta["dir"]) / "schemes.json"
    with open(schemes_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    slugs = []
    for r in records:
        slug = r.get("slug")
        if slug:
            slugs.append(slug)

    seen = set()
    unique_slugs = []
    for s in slugs:
        if s not in seen:
            seen.add(s)
            unique_slugs.append(s)

    logger.info(f"Found {len(unique_slugs)} unique slugs in snapshot")
    return unique_slugs


def build_db_mapping() -> Tuple[Dict[str, str], set]:
    """Build slug -> scheme_id mapping from Postgres with retry."""
    for attempt in range(5):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, link FROM schemes
                        WHERE source = 'myscheme.gov.in' OR source LIKE '%myscheme%'
                    """)
                    slug_to_id = {}
                    for row in cur.fetchall():
                        scheme_id = str(row[0])
                        link = row[1] or ""
                        slug = link.rstrip("/").split("/")[-1] if link else ""
                        if slug:
                            slug_to_id[slug] = scheme_id

                    cur.execute("SELECT id FROM schemes")
                    all_ids = {str(row[0]) for row in cur.fetchall()}

            logger.info(f"Loaded {len(slug_to_id)} scheme slug mappings from DB ({len(all_ids)} total schemes)")
            return slug_to_id, all_ids
        except Exception as e:
            logger.warning(f"Error loading DB mapping (attempt {attempt + 1}/5): {e}")
            time.sleep(2)

    return {}, set()


def enrich_single_slug(slug: str, max_retries: int = 3) -> Tuple[str, Optional[dict]]:
    """Enrich a single scheme slug with retries and rate limiting."""
    enricher = MySchemeDetailEnricher(rate_limit=0.05)

    for retry in range(max_retries):
        try:
            # fetch_scheme_detail without faqs to save 33% of HTTP requests
            detail = enricher.fetch_scheme_detail(slug, include_faqs=False)
            if not detail:
                return slug, {"slug": slug, "empty": True, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

            result = {
                "slug": slug,
                "mongo_id": detail.mongo_id,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            # Parse eligibility
            elig = enricher.parse_eligibility(detail.eligibility_criteria or {})
            if elig:
                result["eligibility_rules"] = elig

            # Raw eligibility text
            ec = detail.eligibility_criteria or {}
            md = ec.get("eligibilityDescription_md", "")
            if md:
                result["eligibility_text"] = md

            # Parse benefits
            benefits = enricher.parse_benefits(detail.scheme_content or {})
            if benefits:
                result["benefits"] = benefits

            # Raw benefits text
            sc = detail.scheme_content or {}
            ben_md = sc.get("benefits_md", "")
            if ben_md:
                result["benefits_text"] = ben_md

            # Parse documents
            docs = enricher.parse_documents(detail.documents or {})
            if docs:
                result["documents"] = docs

            # Application process
            if detail.application_process:
                process_text = []
                for p in detail.application_process:
                    if isinstance(p, dict):
                        text = enricher._extract_text_from_children(p.get("process", []))
                        if text:
                            process_text.append(f"Mode: {p.get('mode', '')}\n{text}")
                if process_text:
                    result["application_process"] = "\n\n".join(process_text)

            # Basic details extras
            basic = detail.basic_details or {}
            if basic.get("implementingAgency"):
                result["implementing_agency"] = basic["implementingAgency"]
            if basic.get("schemeOpenDate"):
                result["start_date"] = basic["schemeOpenDate"]
            if basic.get("schemeCloseDate"):
                result["deadline"] = basic["schemeCloseDate"]
            if basic.get("schemeSubCategory"):
                subcats = [s.get("label", "") for s in basic["schemeSubCategory"] if isinstance(s, dict)]
                if subcats:
                    result["sub_categories"] = subcats

            return slug, result

        except Exception as e:
            if retry < max_retries - 1:
                time.sleep(1.5 * (retry + 1))
            else:
                return slug, {"slug": slug, "error": str(e), "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    return slug, {"slug": slug, "error": "unknown_failure", "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def write_batch_to_db_with_retry(batch_items: List[Tuple[str, dict]], slug_to_id: Dict[str, str], all_ids: set, max_retries: int = 5) -> int:
    """Upsert enriched batch items into Postgres with automatic reconnect on network blips."""
    for attempt in range(max_retries):
        conn = None
        try:
            conn = get_db_connection()
            updated = 0
            with conn.cursor() as cur:
                for slug, data in batch_items:
                    if not data or data.get("empty") or data.get("error"):
                        continue

                    scheme_id = slug_to_id.get(slug)
                    if not scheme_id:
                        candidate = deterministic_uuid(f"myscheme.gov.in:{slug}")
                        if candidate in all_ids:
                            scheme_id = candidate

                    if not scheme_id:
                        continue

                    try:
                        # Update eligibility_text on schemes table
                        elig_text = data.get("eligibility_text")
                        if elig_text:
                            cur.execute("""
                                UPDATE schemes SET eligibility_text = %s
                                WHERE id = %s
                            """, (elig_text, scheme_id))

                        # Upsert eligibility rules
                        rules = data.get("eligibility_rules")
                        if rules:
                            rule_id = deterministic_uuid(f"elig:{scheme_id}")
                            cur.execute("""
                                INSERT INTO eligibility_rules (
                                    id, scheme_id, min_age, max_age, max_income,
                                    gender, caste, states, education_level
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                    min_age = EXCLUDED.min_age,
                                    max_age = EXCLUDED.max_age,
                                    max_income = EXCLUDED.max_income,
                                    gender = EXCLUDED.gender,
                                    caste = EXCLUDED.caste,
                                    states = EXCLUDED.states,
                                    education_level = EXCLUDED.education_level,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (
                                rule_id, scheme_id,
                                rules.get("min_age"), rules.get("max_age"),
                                rules.get("max_income"), rules.get("gender"),
                                rules.get("caste"), rules.get("states"),
                                rules.get("education_level"),
                            ))

                        # Upsert benefits
                        benefits = data.get("benefits", [])
                        for i, benefit in enumerate(benefits):
                            benefit_id = deterministic_uuid(f"benefit:{scheme_id}:{i}")
                            cur.execute("""
                                INSERT INTO benefits (
                                    id, scheme_id, benefit_type, description, amount, frequency
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                    benefit_type = EXCLUDED.benefit_type,
                                    description = EXCLUDED.description,
                                    amount = EXCLUDED.amount,
                                    frequency = EXCLUDED.frequency,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (
                                benefit_id, scheme_id,
                                benefit.get("benefit_type", "financial"),
                                benefit.get("description"),
                                benefit.get("amount"),
                                benefit.get("frequency", "annual"),
                            ))

                        # Upsert documents
                        documents = data.get("documents", [])
                        for i, doc in enumerate(documents):
                            doc_id = deterministic_uuid(f"doc:{scheme_id}:{i}")
                            cur.execute("""
                                INSERT INTO documents_required (
                                    id, scheme_id, document_name, is_mandatory
                                ) VALUES (%s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                    document_name = EXCLUDED.document_name,
                                    is_mandatory = EXCLUDED.is_mandatory,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (
                                doc_id, scheme_id,
                                doc.get("document_name"),
                                doc.get("is_mandatory", True),
                            ))

                        updated += 1
                    except Exception as inner_e:
                        logger.warning(f"Error saving {slug} to DB: {inner_e}")

                conn.commit()
            conn.close()
            return updated

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                    conn.close()
                except Exception:
                    pass
            logger.warning(f"Database batch write error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                logger.error("Failed to commit batch to Postgres; data is preserved in disk cache.")
                return 0

    return 0


def main():
    parser = argparse.ArgumentParser(description="Bulk enrich MyScheme schemes in parallel")
    parser.add_argument("--workers", type=int, default=8,
                        help="Parallel worker threads (default: 8)")
    parser.add_argument("--batch-size", type=int, default=50,
                        help="Batch size for saving to cache and Postgres (default: 50)")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Max retries per scheme (default: 3)")
    args = parser.parse_args()

    start_time = time.time()

    # Load cache and raw snapshot slugs
    cache = load_cache()
    slugs = load_slugs_from_snapshot()

    pending = [s for s in slugs if s not in cache]
    total_schemes = len(slugs)
    cached_count = len(cache)
    pending_count = len(pending)

    logger.info("=" * 60)
    logger.info("PHASE 2: BULK ENRICHMENT & CACHING")
    logger.info("=" * 60)
    logger.info(f"  Total schemes:    {total_schemes}")
    logger.info(f"  Already cached:   {cached_count}")
    logger.info(f"  Pending to fetch: {pending_count}")
    logger.info(f"  Workers:          {args.workers}")
    logger.info(f"  Batch size:       {args.batch_size}")
    logger.info("=" * 60)

    slug_to_id, all_ids = build_db_mapping()

    # Handle graceful exit on SIGINT / SIGTERM
    interrupted = False
    def signal_handler(sig, frame):
        nonlocal interrupted
        interrupted = True
        logger.info("\nGracefully pausing! Saving cache to disk...")
        save_cache(cache)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not pending:
        logger.info("All schemes already in disk cache! Syncing to Postgres...")
        cached_items = list(cache.items())
        total_synced = 0
        for i in range(0, len(cached_items), args.batch_size):
            chunk = cached_items[i:i + args.batch_size]
            total_synced += write_batch_to_db_with_retry(chunk, slug_to_id, all_ids)
        logger.info(f"Sync complete. {total_synced} schemes updated in Postgres.")
        return

    processed = 0
    enriched_success = 0
    batch_items = []
    total_db_updated = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(enrich_single_slug, s, args.max_retries): s for s in pending}

        for future in concurrent.futures.as_completed(futures):
            if interrupted:
                break

            slug, result = future.result()
            processed += 1
            cache[slug] = result
            batch_items.append((slug, result))

            if result and not result.get("empty") and not result.get("error"):
                enriched_success += 1

            # Save batch to disk cache FIRST, then write to Postgres
            if len(batch_items) >= args.batch_size or processed == pending_count:
                save_cache(cache)
                db_upserted = write_batch_to_db_with_retry(batch_items, slug_to_id, all_ids)
                total_db_updated += db_upserted

                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (pending_count - processed) / rate if rate > 0 else 0

                logger.info(
                    f"[{cached_count + processed}/{total_schemes}] "
                    f"Processed {processed}/{pending_count} | "
                    f"DB updated: +{db_upserted} ({total_db_updated} total) | "
                    f"Speed: {rate:.1f} schemes/s | "
                    f"ETA: ~{remaining / 60:.1f}m"
                )
                batch_items = []

    # Final save
    save_cache(cache)
    if batch_items:
        total_db_updated += write_batch_to_db_with_retry(batch_items, slug_to_id, all_ids)

    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info("BULK ENRICHMENT COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Total processed:       {processed}")
    logger.info(f"  Successfully enriched: {enriched_success}")
    logger.info(f"  Postgres updated:      {total_db_updated}")
    logger.info(f"  Total cached on disk:  {len(cache)}")
    logger.info(f"  Cache file:            {CACHE_FILE}")
    logger.info(f"  Elapsed time:          {elapsed:.1f}s ({elapsed / 60:.1f}m)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
