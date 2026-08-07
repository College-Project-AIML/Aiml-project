"""
Deduplication Engine
---------------------
Purpose:
- Remove exact duplicate scheme records (by scheme_id hash)
- Detect near-duplicate scheme names using string similarity
- Maintain dedup statistics for pipeline reporting
- Act as a data quality gate between validation and storage

This prevents data pollution from duplicate ingestion runs.

Scale: a full MyScheme catalog is ~4,800 records, so the near-duplicate stage
uses **min-hash LSH** (banded signatures over character trigrams) to propose
candidate pairs in near-linear time; only candidates that share a band are
checked with the exact ``SequenceMatcher`` ratio. Two names that meet the
similarity threshold almost always share a band, so the dedup *decision* is
unchanged from a naive pairwise scan while the runtime stays fast.
"""

import hashlib
import os
from difflib import SequenceMatcher
from typing import Dict, List, Set, Tuple
from dotenv import load_dotenv

load_dotenv()

# Min-hash LSH parameters. 120 hash functions split into 40 bands of 3 rows:
# two names with trigram-Jaccard ~0.7 collide in a band with p = 0.7^3 = 0.34
# and land in *some* band with p ≈ 1 - (1 - 0.34)^40 ≈ 1.0 — very high recall
# even for true duplicates whose trigram overlap is modest. Smaller bands mean
# more candidate pairs, but candidates are filtered by the exact
# SequenceMatcher + length guard, so the final decision stays exact.
NUM_HASHES = 120
BAND_SIZE = 3
NUM_BANDS = NUM_HASHES // BAND_SIZE  # 40


class DedupEngine:

    def __init__(self, similarity_threshold: float = float(os.getenv('DEDUP_SIMILARITY_THRESHOLD', '0.95'))):
        self.similarity_threshold = similarity_threshold
        self.stats = {
            "total_in": 0,
            "exact_duplicates": 0,
            "near_duplicates": 0,
            "total_out": 0,
        }

    def deduplicate(self, records: List[Dict]) -> List[Dict]:
        self.stats["total_in"] = len(records)

        unique = self._exact_dedup(records)
        unique = self._fuzzy_dedup(unique)

        self.stats["total_out"] = len(unique)
        return unique

    def _exact_dedup(self, records: List[Dict]) -> List[Dict]:
        seen = {}
        unique = []
        for record in records:
            rid = record.get("scheme_id", "")
            if rid not in seen:
                seen[rid] = True
                unique.append(record)
            else:
                self.stats["exact_duplicates"] += 1
        return unique

    def _fuzzy_dedup(self, records: List[Dict]) -> List[Dict]:
        """Near-duplicate detection via min-hash LSH.

        Each unique name is fingerprinted into a banded min-hash signature over
        its character trigrams. Records sharing at least one band are candidate
        pairs; those candidates are verified with the exact SequenceMatcher
        ratio (plus a length guard) so the final decision matches a naive
        pairwise scan.
        """
        unique: List[Dict] = []
        # band_id -> {(band values tuple): [indices into unique]}
        band_index: Dict[int, Dict[Tuple, List[int]]] = {
            b: {} for b in range(NUM_BANDS)
        }

        for record in records:
            name = (record.get("name") or "").lower().strip()
            state = record.get("state_code") or ""
            # Records without a name can never be matched meaningfully; keep
            # them (they should not occur — the validator rejects them — but
            # this keeps the engine robust standalone).
            if not name:
                unique.append(record)
                continue
            signature = _minhash_signature(_trigrams(name))

            candidates: Set[int] = set()
            for band_id in range(NUM_BANDS):
                band = tuple(signature[band_id * BAND_SIZE : (band_id + 1) * BAND_SIZE])
                candidates.update(band_index[band_id].get(band, ()))

            is_dup = False
            for idx in candidates:
                existing = unique[idx]
                # Only collapse records in the SAME state: two schemes that
                # share a name across states are distinct programs (e.g.
                # "Marriage Assistance Scheme" exists in many states).
                if (existing.get("state_code") or "") != state:
                    continue
                # Distinct official links mean distinct schemes (MyScheme links
                # are unique per slug). Never merge two differently-linked
                # records even if their names are near-identical.
                if not _links_compatible(existing.get("link"), record.get("link")):
                    continue
                existing_name = (existing.get("name") or "").lower().strip()
                if not _lengths_compatible(name, existing_name, self.similarity_threshold):
                    continue
                ratio = SequenceMatcher(None, name, existing_name).ratio()
                if ratio >= self.similarity_threshold:
                    is_dup = True
                    self.stats["near_duplicates"] += 1
                    break

            if not is_dup:
                unique.append(record)
                idx = len(unique) - 1
                for band_id in range(NUM_BANDS):
                    band = tuple(signature[band_id * BAND_SIZE : (band_id + 1) * BAND_SIZE])
                    band_index[band_id].setdefault(band, []).append(idx)

        return unique

    def report(self):
        print("\n--- Dedup Report ---")
        for k, v in self.stats.items():
            print(f"  {k}: {v}")


# --------------------------------------------------------------- near-dup math


def _trigrams(text: str) -> Set[str]:
    """Return the set of character trigrams of a lowercased name.

    Names shorter than three characters use the whole name as their only
    shingle, so identical short names still produce identical signatures.
    """
    text = (text or "").lower()
    if len(text) < 3:
        return {text} if text else set()
    return {text[i : i + 3] for i in range(len(text) - 2)}


def _minhash_signature(shingles: Set[str], num_hashes: int = NUM_HASHES) -> List[int]:
    """Return a deterministic min-hash signature for a shingle set.

    Uses SHA-256 of (seed, shingle) so results are stable across processes and
    Python hash-randomisation cannot change them.
    """
    if not shingles:
        return [0] * num_hashes
    signature = []
    for i in range(num_hashes):
        seed = b"ms" + str(i).encode()
        signature.append(
            min(
                int(hashlib.sha256(seed + shingle.encode()).hexdigest()[:8], 16)
                for shingle in shingles
            )
        )
    return signature


def _links_compatible(link_a, link_b) -> bool:
    """True if two records may be the same scheme by their official link.

    When both records carry a non-empty link, a merge is only allowed if the
    links are identical (the same official page). If either side has no link
    (seed/manual data), we cannot use links to distinguish them, so the name
    similarity decides.
    """
    a = (link_a or "").strip().lower()
    b = (link_b or "").strip().lower()
    if not a or not b:
        return True
    return a == b


def _lengths_compatible(a: str, b: str, threshold: float) -> bool:
    """True if two strings could possibly reach ``threshold`` similarity.

    SequenceMatcher ratio = 2M / (len_a + len_b) with M <= min(len_a, len_b).
    For ratio >= t this requires max_len / min_len <= (2/t) - 1. Cheap and
    exact — never discards a candidate that could meet the threshold.
    """
    len_a, len_b = len(a), len(b)
    if len_a == 0 or len_b == 0:
        return a == b
    short, long = min(len_a, len_b), max(len_a, len_b)
    return long / short <= (2.0 / threshold) - 1.0
