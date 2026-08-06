"""
PostgreSQL Loader
------------------
Purpose:
- Bulk upsert scheme records into the PostgreSQL `schemes` table
- Handle ON CONFLICT (id) DO UPDATE for idempotent loads
- Auto-create categories and link them back to schemes
- Track load statistics (inserted, updated, failed)
- Provide connection lifecycle management

This is the primary persistent storage loader for the ingestion pipeline.
"""

import os
import uuid
import hashlib
import psycopg2
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError('DATABASE_URL is not set')


class PostgresLoader:

    def __init__(self):
        self.conn = psycopg2.connect(DB_URL)
        self._category_cache = {}
        self.stats = {
            "inserted": 0,
            "updated": 0,
            "failed": 0,
            "categories_created": 0,
        }

    def load(self, records: List[Dict]):
        cur = self.conn.cursor()
        for record in records:
            try:
                category_id = self._ensure_category(cur, record.get("category"))
                scheme_id = self._deterministic_uuid(record.get("scheme_id", ""))

                cur.execute("""
                    INSERT INTO schemes (
                        id, provider_id, category_id, name, description,
                        eligibility_text, state_code, status, source, source_type,
                        link, tags, confidence_score, ingested_at, last_updated
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        eligibility_text = EXCLUDED.eligibility_text,
                        state_code = EXCLUDED.state_code,
                        status = EXCLUDED.status,
                        tags = EXCLUDED.tags,
                        confidence_score = EXCLUDED.confidence_score,
                        last_updated = EXCLUDED.last_updated,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    scheme_id,
                    None,
                    category_id,
                    record.get("name"),
                    record.get("description"),
                    record.get("eligibility_text"),
                    record.get("state_code"),
                    record.get("status", "ACTIVE"),
                    record.get("source"),
                    record.get("source_type"),
                    record.get("link"),
                    record.get("tags", []),
                    record.get("confidence_score", 0.0),
                    record.get("ingested_at"),
                    record.get("last_updated"),
                ))

                if cur.statusmessage and "UPDATE" in cur.statusmessage:
                    self.stats["updated"] += 1
                else:
                    self.stats["inserted"] += 1

            except Exception as e:
                self.conn.rollback()
                self.stats["failed"] += 1
                print(f"[PostgresLoader] Failed to load record: {e}")
                continue

        self.conn.commit()
        cur.close()
        print(f"[PostgresLoader] Loaded {self.stats['inserted']} inserted, "
              f"{self.stats['updated']} updated, {self.stats['failed']} failed")

    def _ensure_category(self, cur, category_name: str):
        if not category_name:
            return None
        if category_name in self._category_cache:
            return self._category_cache[category_name]

        slug = category_name.lower().replace(" ", "_").replace("-", "_")
        cat_id = self._deterministic_uuid(f"category:{category_name}")

        # Reuse an existing category matching by name (exact) or slug — the slug
        # is UNIQUE, so case variants (e.g. "Scholarship" vs "SCHOLARSHIP")
        # would otherwise violate the unique constraint during ON CONFLICT.
        cur.execute(
            "SELECT id FROM categories WHERE name = %s OR slug = %s LIMIT 1",
            (category_name, slug),
        )
        existing = cur.fetchone()
        if existing:
            self._category_cache[category_name] = existing[0]
            return existing[0]

        cur.execute("""
            INSERT INTO categories (id, name, slug)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
        """, (cat_id, category_name, slug))

        result = cur.fetchone()
        if result:
            self._category_cache[category_name] = result[0]
            self.stats["categories_created"] += 1
            return result[0]

        cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
        result = cur.fetchone()
        if result:
            self._category_cache[category_name] = result[0]
            return result[0]

        return None

    def _deterministic_uuid(self, value: str) -> str:
        h = hashlib.sha256(value.encode()).hexdigest()[:32]
        return str(uuid.UUID(h))

    def close(self):
        if self.conn:
            self.conn.close()

    def report(self):
        print("\n--- PostgresLoader Report ---")
        for k, v in self.stats.items():
            print(f"  {k}: {v}")
