import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

class StorageAdapter:

    def __init__(self):
        self._init_db()

    def _get_conn(self):
        return psycopg2.connect(DB_URL)

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            scheme_id TEXT PRIMARY KEY,
            name TEXT,
            source TEXT,
            version TEXT,
            status TEXT,
            category TEXT,
            ministry TEXT,
            state_code TEXT,
            description TEXT,
            eligibility_text TEXT,
            link TEXT,
            tags TEXT[],
            confidence_score FLOAT,
            ingested_at TIMESTAMP,
            last_updated TIMESTAMP,
            data_lineage TEXT,
            source_type TEXT,
            visibility TEXT,
            access_level TEXT,
            retention_policy TEXT,
            embedding_id TEXT,
            vector_status TEXT
        )
        """)

        conn.commit()
        cur.close()
        conn.close()

    def save(self, scheme: dict):
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO schemes VALUES (
            %(scheme_id)s,
            %(name)s,
            %(source)s,
            %(version)s,
            %(status)s,
            %(category)s,
            %(ministry)s,
            %(state_code)s,
            %(description)s,
            %(eligibility_text)s,
            %(link)s,
            %(tags)s,
            %(confidence_score)s,
            %(ingested_at)s,
            %(last_updated)s,
            %(data_lineage)s,
            %(source_type)s,
            %(visibility)s,
            %(access_level)s,
            %(retention_policy)s,
            %(embedding_id)s,
            %(vector_status)s
        )
        ON CONFLICT (scheme_id) DO NOTHING
        """, scheme)

        conn.commit()
        cur.close()
        conn.close()
