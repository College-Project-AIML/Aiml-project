"""
scheme_retriever.py - Cosine-similarity scheme matcher.

Given a user query, loads scheme embeddings from the database (cached in
module-level state to avoid repeated DB round-trips) and returns the top
matching schemes.
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from services.api.chatbot.embeddings import encode, encode_single

import os

_index_cache: dict = {}
INDEX_PATH = "data/scheme_embedding_index.npz"


def _build_searchable_text(row: dict) -> str:
    """Build searchable text representation of a scheme."""
    parts = []
    if row.get("name"):
        parts.append(str(row["name"]))
    if row.get("description"):
        parts.append(str(row["description"]))
    if row.get("eligibility_text"):
        parts.append(str(row["eligibility_text"]))
    
    tags = row.get("tags")
    if tags:
        if isinstance(tags, list):
            parts.append(" ".join(str(t) for t in tags))
        else:
            parts.append(str(tags))
            
    if row.get("category_name"):
        parts.append(str(row["category_name"]))
    if row.get("state_code"):
        parts.append(str(row["state_code"]))

    return " ".join(parts)


def build_scheme_embedding_index(cur) -> int:
    """
    Query all schemes, generate embeddings, and save to a local .npz file.
    Returns the number of indexed schemes.
    """
    cur.execute('''
        SELECT 
            s.id, 
            s.name, 
            s.description, 
            s.eligibility_text, 
            s.status, 
            s.state_code,
            c.name as category_name, 
            s.tags, 
            s.link, 
            s.source
        FROM schemes s
        LEFT JOIN categories c ON s.category_id = c.id
    ''')
    rows = cur.fetchall()
    if not rows:
        return 0

    schemes = [dict(r) for r in rows]
    texts_to_encode = [_build_searchable_text(s) for s in schemes]
    
    embeddings = encode(texts_to_encode)
    scheme_ids = np.array([str(s["id"]) for s in schemes])
    
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    np.savez_compressed(INDEX_PATH, embeddings=embeddings, scheme_ids=scheme_ids)
    
    _index_cache.clear()
    
    return len(schemes)


def find_matching_schemes(
    query: str, 
    cur, 
    limit: int = 5, 
    threshold: float = 0.35
) -> list[dict]:
    """
    Find schemes semantically closest to *query* using the local npz index.
    Fetches the top results dynamically from the PostgreSQL database.
    """
    if not _index_cache:
        if not os.path.exists(INDEX_PATH):
            raise RuntimeError(f"Embedding index not found at {INDEX_PATH}. Please run build_scheme_embedding_index.py first.")
        data = np.load(INDEX_PATH)
        _index_cache["embeddings"] = data["embeddings"]
        _index_cache["scheme_ids"] = data["scheme_ids"]
        
    embeddings = _index_cache["embeddings"]
    scheme_ids = _index_cache["scheme_ids"]
    
    if len(embeddings) == 0:
        return []
        
    q_emb = encode_single(query)                     # shape (384,)
    scores = (embeddings @ q_emb).tolist()           # dot product = cosine sim

    valid_indices = [i for i, score in enumerate(scores) if score >= threshold]
    if not valid_indices:
        return []
        
    # Sort indices by descending similarity score
    valid_indices.sort(key=lambda i: scores[i], reverse=True)
    top_indices = valid_indices[:limit]
    
    top_ids = [scheme_ids[i] for i in top_indices]
    if not top_ids:
        return []
        
    format_strings = ','.join(['%s::uuid'] * len(top_ids))
    cur.execute(f'''
        SELECT 
            s.id, 
            s.name, 
            s.description, 
            s.eligibility_text, 
            s.status, 
            s.state_code,
            c.name as category_name, 
            s.tags, 
            s.link, 
            s.source
        FROM schemes s
        LEFT JOIN categories c ON s.category_id = c.id
        WHERE s.id IN ({format_strings})
    ''', tuple(top_ids))
    
    rows = cur.fetchall()
    id_to_row = {str(r["id"]): dict(r) for r in rows}
    
    results = []
    for i in top_indices:
        s_id = scheme_ids[i]
        if s_id in id_to_row:
            scheme_copy = id_to_row[s_id]
            scheme_copy["similarity"] = round(scores[i], 4)
            results.append(scheme_copy)
            
    return results
