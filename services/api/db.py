"""
Database connection module.
Uses psycopg2 with SimpleConnectionPool for connection pooling.
Loads DATABASE_URL from environment variables.
"""

import os
from contextlib import contextmanager
import psycopg2
import psycopg2.pool
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:securepassword@localhost:5433/aiml_core"
)

pool = None


def init_pool():
    global pool
    pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)


def close_pool():
    global pool
    if pool:
        pool.closeall()


@contextmanager
def get_db():
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        pool.putconn(conn)
