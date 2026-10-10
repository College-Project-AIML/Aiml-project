#!/usr/bin/env python3
"""Create a 100-case named-scheme retrieval benchmark from the local database.

The generated cases are a reproducible smoke test: each query includes the
scheme name. Review and paraphrase queries before using the score as a broader
estimate of natural-language retrieval quality.
"""

import json
import sys
from pathlib import Path

# Running this file directly puts only scripts/ on sys.path. Add the project
# root so the services package can be imported just like in eval_retrieval_10.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.api.db import close_pool, get_db, init_pool


OUTPUT_PATH = Path(__file__).with_name("eval_benchmark_100.json")
BENCHMARK_SIZE = 100


def main() -> None:
    init_pool()
    try:
        with get_db() as cur:
            cur.execute(
                """
                SELECT id, name
                FROM schemes
                WHERE status = 'ACTIVE' AND name IS NOT NULL AND name <> ''
                ORDER BY md5(id::text), id
                LIMIT %s
                """,
                (BENCHMARK_SIZE,),
            )
            rows = cur.fetchall()
    finally:
        close_pool()

    if len(rows) < BENCHMARK_SIZE:
        raise SystemExit(
            f"Found only {len(rows)} active named schemes; need {BENCHMARK_SIZE}. "
            "Seed or sync more schemes, then run this script again."
        )

    benchmark = [
        {
            "id": index,
            "query": f"Tell me about the {row['name']} scheme and its eligibility.",
            "expected_scheme_names": [row["name"]],
            "expected_scheme_ids": [str(row["id"])],
        }
        for index, row in enumerate(rows, start=1)
    ]

    OUTPUT_PATH.write_text(
        json.dumps(benchmark, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Created {len(benchmark)} benchmark cases: {OUTPUT_PATH}")
    print("These are named-scheme smoke tests; review/paraphrase them for a broader accuracy estimate.")


if __name__ == "__main__":
    main()
