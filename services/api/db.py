"""
Database connection module.
Uses psycopg2 with ThreadedConnectionPool for thread-safe connection pooling.
Loads DATABASE_URL from environment variables.
"""

import os
import time
from contextlib import contextmanager
import psycopg2
import psycopg2.pool
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError('DATABASE_URL is not set')

pool = None


def init_pool():
    global pool
    try:
        pool = psycopg2.pool.ThreadedConnectionPool(1, 20, DATABASE_URL)
    except psycopg2.OperationalError as e:
        if "@postgres:5432/" in DATABASE_URL:
            alt_url = DATABASE_URL.replace("@postgres:5432/", "@localhost:5433/")
            pool = psycopg2.pool.ThreadedConnectionPool(1, 20, alt_url)
        else:
            raise e


def close_pool():
    global pool
    if pool:
        pool.closeall()


def _get_valid_connection():
    """Get an active connection from pool, replacing dead connections if necessary."""
    for attempt in range(3):
        conn = pool.getconn()
        try:
            # Quick liveness ping
            if conn.closed:
                raise psycopg2.OperationalError("Connection is closed")
            with conn.cursor() as test_cur:
                test_cur.execute("SELECT 1")
            return conn
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            time.sleep(0.2)
    # If all failed, attempt a brand new connection
    return pool.getconn()


@contextmanager
def get_db():
    conn = _get_valid_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        conn.commit()
    except Exception:
        if not conn.closed:
            conn.rollback()
        raise
    finally:
        cur.close()
        if not conn.closed:
            pool.putconn(conn)
        else:
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
