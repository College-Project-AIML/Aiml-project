"""
embeddings.py — Sentence-transformers wrapper for FAQ semantic search.

Uses the lightweight all-MiniLM-L6-v2 model (22 MB, no external API calls).
Model is loaded once on first use and cached for the lifetime of the process.
"""

from __future__ import annotations

from typing import List
import numpy as np

_model = None


def _get_model():
    """Lazy-load the sentence-transformer model (once per process)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def encode(texts: List[str]) -> np.ndarray:
    """
    Encode a list of strings into L2-normalised embedding vectors.

    Returns:
        np.ndarray of shape (len(texts), 384), dtype float32.
    """
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)


def encode_single(text: str) -> np.ndarray:
    """Encode a single string.  Returns shape (384,)."""
    return encode([text])[0]
