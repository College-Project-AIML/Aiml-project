"""
Live Sync Pipeline (docs/next.md §2)
--------------------------------------
Orchestrates near-real-time scheme updates:

    fetch → parse → normalize → validate → dedup → upsert → snapshot → emit updates

It reuses the existing pipeline stages verbatim
(``SchemeNormalizer → SchemeValidator → DedupEngine → PostgresLoader``) and adds
fingerprint/change bookkeeping around them:

    - NEW        first time we see a scheme          → insert + scheme_updates row
    - UPDATED    fingerprint changed                  → upsert + diff + row
    - UNCHANGED  same fingerprint, still active       → skip scheme upsert, refresh snapshot
    - CLOSED     missing for N consecutive runs (2)   → status INACTIVE + row

Each run writes a JSON run report to ``data/sync_logs/`` for observability.

Run manually:

    python -m ingestion.pipelines.live_sync_pipeline \
        [--sources myscheme,karnataka_ssp] [--skip-postgres]
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

from ingestion.dedup.dedup_engine import DedupEngine
from ingestion.enrichment.myscheme_detail import enrich_schemes
from ingestion.normalizers.scheme_normalizer import SchemeNormalizer
from ingestion.sync import change_detector as cd
from ingestion.sync.fingerprint import fingerprint_record
from ingestion.validators.scheme_validator import SchemeValidator

logger = logging.getLogger(__name__)

# Number of consecutive missed runs before a scheme is marked CLOSED/INACTIVE.
MISS_THRESHOLD = int(os.getenv("LIVE_SYNC_MISS_THRESHOLD", "2"))

SYNC_LOG_DIR = os.getenv("SYNC_LOG_DIR", "data/sync_logs")

# Connector factories: source name -> callable returning raw records.
CONNECTOR_FACTORIES = {
    "myscheme": lambda: __import__(
        "ingestion.sources.myscheme.client", fromlist=["MySchemeClient"]
    ).MySchemeClient(),
    "karnataka_ssp": lambda: __import__(
        "ingestion.sources.karnataka_ssp.client", fromlist=["KarnatakaSSPClient"]
    ).KarnatakaSSPClient(),
}


class LiveSyncPipeline:
    def __init__(self):
        self.normalizer = SchemeNormalizer()
        self.validator = SchemeValidator()
        self.dedup = DedupEngine()

    # ------------------------------------------------------------- public API

    def run(self, sources=None, skip_postgres: bool = False) -> dict:
        """Run a full sync pass for the given sources and write a run report."""
        sources = sources or list(CONNECTOR_FACTORIES.keys())
        report = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "sources": {},
            "totals": {
                "fetched": 0,
                "new": 0,
                "updated": 0,
                "unchanged": 0,
                "closed": 0,
                "errors": 0,
            },
        }

        for name in sources:
            try:
                source_report = self._sync_source(name, skip_postgres)
            except Exception as exc:  # noqa: BLE001 — one bad source never kills the run
                logger.exception("Live sync source %s failed", name)
                source_report = {"error": str(exc)}
            report["sources"][name] = source_report
            for key in ("fetched", "new", "updated", "unchanged", "closed", "errors"):
                report["totals"][key] += source_report.get(key, 0)

        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        self._write_report(report)
        return report

    # ------------------------------------------------------------- internals

    def _sync_source(self, name: str, skip_postgres: bool) -> dict:
        stats = {
            "fetched": 0,
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "closed": 0,
            "errors": 0,
        }

        raw_records = self._fetch(name)
        stats["fetched"] = len(raw_records)

        # Reuse the existing stages verbatim: normalize -> validate -> dedup.
        normalized = []
        for raw in raw_records:
            try:
                record = self.normalizer.normalize(raw)
                normalized.append(self.validator.validate(record))
            except Exception as exc:  # noqa: BLE001
                stats["errors"] += 1
                logger.warning(
                    "Normalize/validate failed for %r: %s", raw.get("scheme_name"), exc
                )
        stats["parsed"] = len(normalized)

        records = self.dedup.deduplicate(normalized)

        conn = None if skip_postgres else self._connect()
        if conn is None:
            if not skip_postgres:
                logger.warning(
                    "DATABASE_URL not set — Postgres bookkeeping skipped; "
                    "report-only run (%d records)", len(records)
                )
            stats["new"] = len(records)
            return stats

        try:
            self._apply_changes(conn, name, records, stats)
        finally:
            conn.close()
        return stats

    # ---------------------------------------------------------------- stages

    def _fetch(self, name: str) -> list:
        if name == "myscheme":
            records, status = CONNECTOR_FACTORIES["myscheme"]().fetch_schemes()
            logger.info("[%s] fetched %d records (status=%s)", name, len(records), status)
            return records
        if name == "karnataka_ssp":
            schemes, _notices, status = CONNECTOR_FACTORIES["karnataka_ssp"]().fetch()
            logger.info(
                "[%s] fetched %d scheme records, %d notices (status=%s)",
                name, len(schemes), len(_notices), status,
            )
            return schemes
        raise ValueError(f"unknown source: {name}")

    def _apply_changes(self, conn, source: str, records: list, stats: dict) -> None:
        """Classify every record, enrich NEW/UPDATED in batches, upsert and save snapshots incrementally."""
        cur = conn.cursor()
        try:
            BATCH_SIZE = 100  # Process in batches to save progress incrementally

            # Phase 1: Pre-load existing snapshots for this source in ONE query to avoid thousands of network roundtrips
            cur.execute(
                "SELECT snap.scheme_id, snap.fingerprint, snap.snapshot, sch.status "
                "FROM scheme_snapshots snap "
                "LEFT JOIN schemes sch ON sch.id = snap.scheme_id "
                "WHERE snap.source = %s",
                (source,),
            )
            existing_snapshots = {}
            for r in cur.fetchall():
                snap_val = r[2]
                if isinstance(snap_val, str):
                    try:
                        snap_val = json.loads(snap_val)
                    except Exception:
                        snap_val = None
                existing_snapshots[r[0]] = {
                    "fingerprint": r[1],
                    "snapshot": snap_val,
                    "status": r[3],
                }

            classification = []  # list of (scheme_id, record, change_type, previous)
            seen_scheme_ids = set()

            for record in records:
                scheme_id = _deterministic_uuid(record.get("scheme_id", ""))
                seen_scheme_ids.add(scheme_id)
                fingerprint = fingerprint_record(record)

                previous = existing_snapshots.get(scheme_id)
                change = cd.classify(fingerprint, previous["fingerprint"] if previous else None)

                classification.append((scheme_id, record, change, previous))

            # Separate NEW/UPDATED from UNCHANGED
            needs_upsert = [(sid, rec, ch, prev) for sid, rec, ch, prev in classification if ch in (cd.NEW, cd.UPDATED)]
            unchanged = [(sid, rec, ch, prev) for sid, rec, ch, prev in classification if ch not in (cd.NEW, cd.UPDATED)]

            # Handle UNCHANGED records immediately
            unchanged_ids = []
            for scheme_id, record, change, previous in unchanged:
                if previous and previous.get("status") == "INACTIVE":
                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
                    unchanged_ids.append(scheme_id)

            if unchanged_ids:
                placeholders = ','.join(['%s'] * len(unchanged_ids))
                cur.execute(
                    f"UPDATE scheme_snapshots SET fetched_at = CURRENT_TIMESTAMP, miss_count = 0 WHERE scheme_id IN ({placeholders})",
                    unchanged_ids,
                )
                conn.commit()

            # Phase 2: Process NEW/UPDATED records in batches
            if needs_upsert:
                do_enrich = os.getenv("ENRICH_DETAILS", "false").lower() in ("true", "1")
                logger.info("[%s] processing %d NEW/UPDATED records in batches of %d...", source, len(needs_upsert), BATCH_SIZE)
                
                for batch_start in range(0, len(needs_upsert), BATCH_SIZE):
                    batch = needs_upsert[batch_start:batch_start + BATCH_SIZE]
                    batch_num = batch_start // BATCH_SIZE + 1
                    total_batches = (len(needs_upsert) + BATCH_SIZE - 1) // BATCH_SIZE
                    
                    logger.info("[%s] processing batch %d/%d (%d records)", source, batch_num, total_batches, len(batch))
                    
                    try:
                        batch_records = [rec for _, rec, _, _ in batch]
                        if source == "myscheme" and do_enrich:
                            try:
                                enriched_records = enrich_schemes(batch_records, rate_limit=0.2)
                            except Exception as e:
                                logger.warning("[%s] enrichment failed, using raw records: %s", source, e)
                                enriched_records = batch_records
                        else:
                            enriched_records = batch_records
                        
                        batch_classification = []
                        for (sid, rec, ch, prev), er in zip(batch, enriched_records):
                            batch_classification.append((sid, er, ch, prev))
                        
                        # Upsert this batch immediately
                        self._upsert_batch(conn, cur, source, batch_classification, stats); logger.info(f"[{source}] upserted batch {batch_num}")
                        conn.commit()
                        logger.info("[%s] batch %d/%d committed (%d new, %d updated)", 
                                   source, batch_num, total_batches, 
                                   sum(1 for _, _, ch, _ in batch_classification if ch == cd.NEW),
                                   sum(1 for _, _, ch, _ in batch_classification if ch == cd.UPDATED))
                        
                    except Exception as exc:  # noqa: BLE001
                        stats["errors"] += len(batch)
                        logger.exception("Batch %d/%d failed for %s, continuing with next batch", batch_num, total_batches, source)
                        conn.rollback()
                        continue

            # Phase 3: Handle UNCHANGED reactivation (INACTIVE -> ACTIVE)
            reactivated = []
            for scheme_id, record, change, previous in unchanged:
                if previous and previous.get("status") == "INACTIVE":
                    stats["updated"] += 1
                    reactivated.append((scheme_id, record, {"status": ["INACTIVE", "ACTIVE"]}))

            if reactivated:
                self._upsert_batch(conn, cur, source, reactivated, stats)
                conn.commit()

            # Phase 4: CLOSED detection (once at the end for all seen schemes)
            stats["closed"] = self._detect_closed(cur, source, seen_scheme_ids)
            conn.commit()

        finally:
            cur.close()

    def _upsert_batch(self, conn, cur, source: str, batch_classification: list, stats: dict) -> None:
        
        """Upsert a single batch of records and save snapshots."""
        pending_new = []
        pending_updated = []
        to_upsert = []

        for scheme_id, record, change, previous in batch_classification:
            if change == cd.NEW:
                stats["new"] += 1
                pending_new.append((scheme_id, record))
                to_upsert.append(record)
            elif change == cd.UPDATED:
                stats["updated"] += 1
                old_record = _previous_semantic_record(cur, scheme_id, previous)
                changed = cd.diff_fields(old_record, record) if old_record else None
                pending_updated.append((scheme_id, record, changed))
                to_upsert.append(record)

        # Upsert this batch
        if to_upsert:
            
            self._upsert_schemes(to_upsert)
            

        # Emit updates + save snapshots for this batch
        event_ids = [sid for sid, _ in pending_new] + [sid for sid, *_ in pending_updated]
        existing_ids = set(_existing_scheme_ids(cur, event_ids))

        for scheme_id, record in pending_new:
            if scheme_id not in existing_ids:
                stats["errors"] += 1
                continue
            _emit_update(cur, scheme_id, cd.NEW, None)
            _upsert_snapshot(cur, scheme_id, fingerprint_record(record), record, source)
        for scheme_id, record, changed in pending_updated:
            if scheme_id not in existing_ids:
                stats["errors"] += 1
                continue
            _emit_update(cur, scheme_id, cd.UPDATED, changed)
            _upsert_snapshot(cur, scheme_id, fingerprint_record(record), record, source)

    def _upsert_schemes(self, records: list) -> None:
        """Delegate to the existing PostgresLoader (idempotent ON CONFLICT upsert)."""
        from ingestion.loaders.postgres_loader import PostgresLoader

        loader = PostgresLoader()
        try:
            loader.load(records)
        finally:
            loader.close()

    def _detect_closed(self, cur, source: str, seen_scheme_ids: set) -> int:
        """Mark schemes of this source missing N consecutive runs as INACTIVE."""
        if not seen_scheme_ids:
            # No schemes seen this run, mark all as missed
            cur.execute(
                "SELECT snap.scheme_id, snap.miss_count, sch.status "
                "FROM scheme_snapshots snap "
                "LEFT JOIN schemes sch ON sch.id = snap.scheme_id "
                "WHERE snap.source = %s",
                (source,),
            )
        else:
            # Use proper UUID array casting
            seen_list = list(seen_scheme_ids)
            placeholders = ','.join(['%s'] * len(seen_list))
            cur.execute(
                f"SELECT snap.scheme_id, snap.miss_count, sch.status "
                f"FROM scheme_snapshots snap "
                f"LEFT JOIN schemes sch ON sch.id = snap.scheme_id "
                f"WHERE snap.source = %s AND snap.scheme_id NOT IN ({placeholders})",
                (source, *seen_list),
            )
        rows = cur.fetchall()
        closed = 0
        for scheme_id, miss_count, status in rows:
            new_miss = (miss_count or 0) + 1
            if new_miss >= MISS_THRESHOLD and status == "ACTIVE":
                _emit_update(cur, scheme_id, cd.CLOSED, {"status": ["ACTIVE", "INACTIVE"]})
                cur.execute(
                    "UPDATE schemes SET status = 'INACTIVE', updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = %s",
                    (scheme_id,),
                )
                closed += 1
                new_miss = 0  # reset so it needs N more misses before re-emitting
            cur.execute(
                "UPDATE scheme_snapshots SET miss_count = %s WHERE scheme_id = %s",
                (new_miss, scheme_id),
            )
        return closed

    # ---------------------------------------------------------------- helpers

    def _connect(self):
        # Check the env var before importing PostgresLoader — its module-level
        # DB_URL init raises when DATABASE_URL is unset, so this keeps the
        # report-only fallback below reachable.
        if not os.getenv("DATABASE_URL"):
            return None
        from ingestion.loaders.postgres_loader import resolve_database_url

        url = resolve_database_url()
        if not url:
            return None
        import psycopg2

        return psycopg2.connect(url)

    def _write_report(self, report: dict) -> str:
        os.makedirs(SYNC_LOG_DIR, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(SYNC_LOG_DIR, f"{timestamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        with open(os.path.join(SYNC_LOG_DIR, "latest.json"), "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info("Run report written to %s", path)
        return path


# ---------------------------------------------------------------- DB helpers


def _deterministic_uuid(value: str) -> str:
    import hashlib
    import uuid

    h = hashlib.sha256(value.encode()).hexdigest()[:32]
    return str(uuid.UUID(h))


def _existing_scheme_ids(cur, scheme_ids):
    """Return the set of scheme ids (as strings) present in the schemes table."""
    if not scheme_ids:
        return set()
    scheme_list = list(scheme_ids)
    placeholders = ','.join(['%s'] * len(scheme_list))
    cur.execute(
        f"SELECT id FROM schemes WHERE id IN ({placeholders})",
        scheme_list,
    )
    return {str(row[0]) for row in cur.fetchall()}


def _load_snapshot(cur, scheme_id):
    """Return {fingerprint, snapshot, status} for a scheme, or None."""
    import json as _json

    cur.execute(
        "SELECT snap.fingerprint, snap.snapshot, sch.status "
        "FROM scheme_snapshots snap "
        "LEFT JOIN schemes sch ON sch.id = snap.scheme_id "
        "WHERE snap.scheme_id = %s",
        (scheme_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    snapshot = row[1]
    if isinstance(snapshot, str):
        try:
            snapshot = _json.loads(snapshot)
        except ValueError:
            snapshot = None
    return {"fingerprint": row[0], "snapshot": snapshot, "status": row[2]}


def _previous_semantic_record(cur, scheme_id, previous) -> dict:
    """Reconstruct the old normalized record for diffing (best effort)."""
    if previous and previous.get("snapshot"):
        return previous["snapshot"]
    return _load_scheme_as_record(cur, scheme_id)


def _load_scheme_as_record(cur, scheme_id) -> dict:
    cur.execute(
        """
        SELECT s.name, s.description, s.eligibility_text, s.state_code, s.status,
               s.link, s.tags, s.confidence_score, c.name AS category,
               p.name AS ministry
        FROM schemes s
        LEFT JOIN categories c ON s.category_id = c.id
        LEFT JOIN providers p ON s.provider_id = p.id
        WHERE s.id = %s
        """,
        (scheme_id,),
    )
    row = cur.fetchone()
    if not row:
        return {}
    return {
        "name": row[0],
        "description": row[1],
        "eligibility_text": row[2],
        "state_code": row[3],
        "status": row[4],
        "link": row[5],
        "tags": row[6] or [],
        "confidence_score": row[7],
        "category": row[8],
        "ministry": row[9],
    }


def _refresh_snapshot(cur, scheme_id: str) -> None:
    """Refresh fetched_at and clear the miss count for a seen-but-unchanged scheme."""
    cur.execute(
        "UPDATE scheme_snapshots SET fetched_at = CURRENT_TIMESTAMP, miss_count = 0 "
        "WHERE scheme_id = %s",
        (scheme_id,),
    )


def _upsert_snapshot(cur, scheme_id: str, fingerprint: str, record: dict, source: str) -> None:
    import json

    semantic = {
        field: record.get(field)
        for field in cd.DIFF_FIELDS
    }
    cur.execute(
        """
        INSERT INTO scheme_snapshots (scheme_id, fingerprint, snapshot, fetched_at, miss_count, source)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, 0, %s)
        ON CONFLICT (scheme_id) DO UPDATE SET
            fingerprint = EXCLUDED.fingerprint,
            snapshot = EXCLUDED.snapshot,
            fetched_at = CURRENT_TIMESTAMP,
            miss_count = 0,
            source = EXCLUDED.source
        """,
        (scheme_id, fingerprint, json.dumps(semantic, default=str), source),
    )


def _emit_update(cur, scheme_id: str, change_type: str, changed_fields) -> None:
    import json

    cur.execute(
        """
        INSERT INTO scheme_updates (scheme_id, change_type, changed_fields)
        VALUES (%s, %s, %s)
        """,
        (scheme_id, change_type, json.dumps(changed_fields, default=str) if changed_fields else None),
    )


# --------------------------------------------------------------------- CLI


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Live scheme sync pipeline")
    parser.add_argument("--sources", default=None, help="comma-separated sources")
    parser.add_argument("--skip-postgres", action="store_true")
    args = parser.parse_args()

    selected = [s.strip() for s in args.sources.split(",")] if args.sources else None
    pipeline = LiveSyncPipeline()
    result = pipeline.run(sources=selected, skip_postgres=args.skip_postgres)
    print(json.dumps(result, indent=2, default=str))
