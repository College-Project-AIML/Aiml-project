"""
End-to-end DB test for the live-sync pipeline (docs/next.md §2 acceptance criteria).

Requires a running Postgres with the schema applied (postgres.sql + alembic head).

    DATABASE_URL=postgresql://admin:securepassword@localhost:5433/aiml_test \
        venv/bin/python scripts/test_live_sync_db.py

Covers:
    1. First run -> every scheme is NEW (one scheme_updates row each)
    2. Idempotent re-run -> zero new scheme_updates rows, all UNCHANGED
    3. Edited record -> exactly one UPDATED event with correct changed_fields
    4. Records missing for 2 consecutive runs -> CLOSED events + status INACTIVE
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

from ingestion.pipelines import live_sync_pipeline as lsp

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {detail}")


def db():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def count_updates(cur, change_type=None, since_run=None):
    query = "SELECT COUNT(*) FROM scheme_updates"
    params = []
    if change_type:
        query += " WHERE change_type = %s"
        params.append(change_type)
    cur.execute(query, params)
    return cur.fetchone()[0]


def reset():
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM scheme_updates")
    cur.execute("DELETE FROM scheme_snapshots")
    cur.execute("DELETE FROM schemes")
    cur.execute("DELETE FROM categories")
    conn.commit()
    cur.close()
    conn.close()


def set_records(records):
    """Point the pipeline's myscheme connector at controlled raw records."""
    def fake_fetch_schemes(self):
        return records, "sample"
    lsp.CONNECTOR_FACTORIES["myscheme"] = lambda: type(
        "FakeClient", (), {"fetch_schemes": fake_fetch_schemes}
    )()


def make_record(name, eligibility):
    return {
        "scheme_name": name,
        "source": "test.example.gov.in",
        "category": "scholarship",
        "ministry": "Test Department",
        "description": "A test scheme for the live-sync pipeline.",
        "eligibility": eligibility,
        "state": "karnataka",
        "link": "https://test.example.gov.in/scheme",
        "tags": ["test"],
    }


def main():
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL must be set")
        sys.exit(1)

    scheme_a = make_record("Karnataka Sync Test Scholarship Alpha", "Income below 2 lakh")
    scheme_b = make_record("National Sync Test Microcredit Loan Beta", "Income below 3 lakh")
    records_v1 = [scheme_a, scheme_b]

    reset()
    set_records(records_v1)

    print("\n[1] First run -> NEW")
    report1 = lsp.LiveSyncPipeline().run(sources=["myscheme"])
    check("2 NEW classified", report1["sources"]["myscheme"]["new"] == 2)
    conn = db()
    cur = conn.cursor()
    check("2 NEW rows in scheme_updates", count_updates(cur, "NEW") == 2)
    cur.execute("SELECT COUNT(*) FROM schemes")
    check("2 schemes in DB", cur.fetchone()[0] == 2)

    print("\n[2] Idempotent re-run -> UNCHANGED, zero new rows")
    report2 = lsp.LiveSyncPipeline().run(sources=["myscheme"])
    check("all UNCHANGED", report2["sources"]["myscheme"]["unchanged"] == 2)
    check("zero new update rows", count_updates(cur) == 2)  # still 2 total
    check("no new NEW rows", count_updates(cur, "NEW") == 2)

    print("\n[3] Edited record -> exactly one UPDATED with correct diff")
    edited_b = make_record("National Sync Test Microcredit Loan Beta", "Income below 5 lakh (deadline extended)")
    set_records([scheme_a, edited_b])
    report3 = lsp.LiveSyncPipeline().run(sources=["myscheme"])
    check("1 UPDATED classified", report3["sources"]["myscheme"]["updated"] == 1)
    check("1 UNCHANGED", report3["sources"]["myscheme"]["unchanged"] == 1)
    check("exactly 3 update rows total", count_updates(cur) == 3)
    cur.execute(
        "SELECT changed_fields FROM scheme_updates WHERE change_type = 'UPDATED'"
    )
    row = cur.fetchone()
    changed = row[0] if row else {}
    check(
        "changed_fields names eligibility_text",
        isinstance(changed, dict) and "eligibility_text" in changed,
        f"got {changed}",
    )

    print("\n[4] Missing for 2 consecutive runs -> CLOSED + INACTIVE")
    set_records([])
    lsp.LiveSyncPipeline().run(sources=["myscheme"])   # miss 1 -> tolerated
    check("miss 1: no CLOSED yet", count_updates(cur, "CLOSED") == 0)
    lsp.LiveSyncPipeline().run(sources=["myscheme"])   # miss 2 -> CLOSED
    check("2 CLOSED events", count_updates(cur, "CLOSED") == 2)
    cur.execute("SELECT COUNT(*) FROM schemes WHERE status = 'INACTIVE'")
    check("both schemes INACTIVE", cur.fetchone()[0] == 2)

    cur.close()
    conn.close()

    print(f"\n{'=' * 40}\nResult: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
