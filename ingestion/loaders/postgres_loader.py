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

import logging
import os
import socket
import uuid
import hashlib
import psycopg2
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any

load_dotenv()

logger = logging.getLogger(__name__)


def resolve_database_url() -> Optional[str]:
    """Return a usable DATABASE_URL, applying the host-side Docker fallback.

    Inside docker-compose the Postgres hostname is ``postgres`` (resolves only
    on the compose network). From the host machine that name does not resolve,
    but the container exposes the DB on ``localhost:5433`` — the same fallback
    ``services/api/db.py`` applies. This keeps manual pipeline runs working
    from the host without changing .env.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    if "@postgres:5432/" in url:
        try:
            socket.gethostbyname("postgres")
        except socket.gaierror:
            url = url.replace("@postgres:5432/", "@localhost:5433/")
            logger.info(
                "postgres host not reachable from this machine — using %s", url
            )
    return url


DB_URL = resolve_database_url()
if not DB_URL:
    raise ValueError('DATABASE_URL is not set')


class PostgresLoader:

    def __init__(self):
        self.conn = psycopg2.connect(DB_URL)
        self._category_cache = {}
        self._provider_cache = {}
        self.stats = {
            "inserted": 0,
            "updated": 0,
            "failed": 0,
            "categories_created": 0,
            "providers_created": 0,
        }

    def load(self, records: List[Dict]):
        
        cur = self.conn.cursor()
        for record in records:
            try:
                category_id = self._ensure_category(cur, record.get("category"))
                provider_id = self._ensure_provider(cur, record.get("ministry"))
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
                    provider_id,
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

                # Upsert related tables
                self._upsert_eligibility_rules(cur, scheme_id, record.get("eligibility_rules"))
                self._upsert_benefits(cur, scheme_id, record.get("benefits", []))
                self._upsert_documents(cur, scheme_id, record.get("documents", []))

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
              f"{self.stats['updated']} updated, {self.stats['failed']} failed, "
              f"{self.stats['categories_created']} categories, "
              f"{self.stats['providers_created']} providers")

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

    def _ensure_provider(self, cur, ministry_name: str):
        """Look up or create a provider based on ministry name."""
        if not ministry_name:
            return None
        
        normalized = ministry_name.strip()
        if normalized in self._provider_cache:
            return self._provider_cache[normalized]
        
        prov_id = self._deterministic_uuid(f"provider:{normalized}")
        
        # Try to find existing provider by name
        cur.execute("SELECT id FROM providers WHERE name = %s LIMIT 1", (normalized,))
        existing = cur.fetchone()
        if existing:
            self._provider_cache[normalized] = existing[0]
            return existing[0]
        
        # Determine provider type
        ptype = "central_ministry"
        if any(kw in normalized.lower() for kw in ["state", "government of ", "govt of "]):
            ptype = "state_department"
        elif "university" in normalized.lower() or "institute" in normalized.lower():
            ptype = "academic"
        
        cur.execute("""
            INSERT INTO providers (id, name, type)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING id
        """, (prov_id, normalized, ptype))
        
        result = cur.fetchone()
        if result:
            self._provider_cache[normalized] = result[0]
            self.stats["providers_created"] += 1
            return result[0]
        
        cur.execute("SELECT id FROM providers WHERE name = %s", (normalized,))
        result = cur.fetchone()
        if result:
            self._provider_cache[normalized] = result[0]
            return result[0]
        
        return None

    def _deterministic_uuid(self, value: str) -> str:
        h = hashlib.sha256(value.encode()).hexdigest()[:32]
        return str(uuid.UUID(h))

    def _upsert_eligibility_rules(self, cur, scheme_id: str, rules: Optional[Dict]):
        """Upsert eligibility rules for a scheme."""
        if not rules:
            return
        
        rule_id = self._deterministic_uuid(f"elig:{scheme_id}")
        cur.execute("""
            INSERT INTO eligibility_rules (
                id, scheme_id, min_age, max_age, max_income,
                gender, caste, states, education_level
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
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
            rule_id,
            scheme_id,
            rules.get("min_age"),
            rules.get("max_age"),
            rules.get("max_income"),
            rules.get("gender"),
            rules.get("caste"),
            rules.get("states"),
            rules.get("education_level"),
        ))

    def _upsert_benefits(self, cur, scheme_id: str, benefits: List[Dict]):
        """Upsert benefits for a scheme."""
        if not benefits:
            return
        
        for i, benefit in enumerate(benefits):
            benefit_id = self._deterministic_uuid(f"benefit:{scheme_id}:{i}")
            cur.execute("""
                INSERT INTO benefits (
                    id, scheme_id, benefit_type, description, amount, frequency
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    benefit_type = EXCLUDED.benefit_type,
                    description = EXCLUDED.description,
                    amount = EXCLUDED.amount,
                    frequency = EXCLUDED.frequency,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                benefit_id,
                scheme_id,
                benefit.get("benefit_type", "financial"),
                benefit.get("description"),
                benefit.get("amount"),
                benefit.get("frequency", "annual"),
            ))

    def _upsert_documents(self, cur, scheme_id: str, documents: List[Dict]):
        """Upsert required documents for a scheme."""
        if not documents:
            return
        
        for i, doc in enumerate(documents):
            doc_id = self._deterministic_uuid(f"doc:{scheme_id}:{i}")
            cur.execute("""
                INSERT INTO documents_required (
                    id, scheme_id, document_name, is_mandatory
                ) VALUES (
                    %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    document_name = EXCLUDED.document_name,
                    is_mandatory = EXCLUDED.is_mandatory,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                doc_id,
                scheme_id,
                doc.get("document_name"),
                doc.get("is_mandatory", True),
            ))

    def close(self):
        if self.conn:
            self.conn.close()

    def report(self):
        print("\n--- PostgresLoader Report ---")
        for k, v in self.stats.items():
            print(f"  {k}: {v}")
