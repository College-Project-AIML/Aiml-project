"""
matcher.py — Cosine-similarity FAQ matcher.

Given a user query, loads all FAQ embeddings from the database (cached in
module-level state to avoid repeated DB round-trips) and returns the best
matching FAQ + its linked scheme record.

Similarity threshold: 0.35  (tuned for short FAQ-style questions; lower it
if you want fuzzier matches, raise it to make the widget fall back more often).
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from services.api.chatbot.embeddings import encode_single, encode

# ── Module-level embedding cache ────────────────────────────────────────────
_cache: dict = {}          # {"embeddings": np.ndarray, "faq_ids": list[int], "ts": float}
_CACHE_TTL = 300           # seconds before re-fetching FAQ embeddings from DB


def _load_faq_embeddings(cur) -> tuple[np.ndarray, list[int], list[str]]:
    """
    Fetch all FAQs from the DB and encode their questions.
    Returns (embeddings, faq_ids, questions) or (None, [], []) if table is empty.
    """
    now = time.monotonic()
    if _cache and now - _cache["ts"] < _CACHE_TTL:
        return _cache["embeddings"], _cache["faq_ids"], _cache["questions"]

    cur.execute("SELECT id, question FROM faqs ORDER BY id")
    rows = cur.fetchall()
    if not rows:
        return None, [], []

    faq_ids = [r["id"] for r in rows]
    questions = [r["question"] for r in rows]
    embeddings = encode(questions)

    _cache.update({"embeddings": embeddings, "faq_ids": faq_ids, "questions": questions, "ts": now})
    return embeddings, faq_ids, questions


def invalidate_cache() -> None:
    """Call this after seeding / inserting new FAQs to force a reload."""
    _cache.clear()


def find_best_match(
    query: str,
    cur,
    threshold: float = 0.35,
) -> Optional[dict]:
    """
    Find the FAQ whose question is semantically closest to *query*.

    Returns a dict with keys:
        faq_id, faq_question, faq_answer, similarity, scheme_id
    or None if no FAQ exceeds *threshold*.
    """
    embeddings, faq_ids, questions = _load_faq_embeddings(cur)
    if embeddings is None or len(faq_ids) == 0:
        return None

    q_emb = encode_single(query)                     # shape (384,)
    scores = (embeddings @ q_emb).tolist()           # cosine sim (vecs are L2-normalised)
    best_idx = int(np.argmax(scores))
    best_score = scores[best_idx]

    if best_score < threshold:
        return None

    best_faq_id = faq_ids[best_idx]
    cur.execute(
        "SELECT id, question, answer, scheme_id FROM faqs WHERE id = %s",
        (best_faq_id,),
    )
    row = cur.fetchone()
    if not row:
        return None

    return {
        "faq_id": row["id"],
        "faq_question": row["question"],
        "faq_answer": row["answer"],
        "similarity": round(best_score, 4),
        "scheme_id": str(row["scheme_id"]) if row["scheme_id"] else None,
    }

# reload

# reload

# reload
