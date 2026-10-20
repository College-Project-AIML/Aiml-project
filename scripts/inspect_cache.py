#!/usr/bin/env python3
"""
CLI utility to safely inspect and search the 22MB myscheme_enriched.json cache
without opening the monolithic file in the editor or risking browser/IDE crashes.
"""

import argparse
import json
import random
import sys
from pathlib import Path

CACHE_FILE = Path("data/enriched_cache/myscheme_enriched.json")


def load_cache():
    if not CACHE_FILE.exists():
        print(f"Error: Cache file not found at {CACHE_FILE}")
        sys.exit(1)
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def print_stats(cache):
    total = len(cache)
    enriched = [k for k, v in cache.items() if not v.get("empty") and not v.get("error")]
    empty = [k for k, v in cache.items() if v.get("empty")]
    errors = [k for k, v in cache.items() if v.get("error")]
    has_rules = [k for k, v in cache.items() if v.get("eligibility_rules")]
    has_benefits = [k for k, v in cache.items() if v.get("benefits")]
    has_docs = [k for k, v in cache.items() if v.get("documents")]

    print("=" * 60)
    print(" Enriched Cache Summary (myscheme_enriched.json)")
    print("=" * 60)
    print(f" Total Cached Schemes : {total:,}")
    print(f" Fully Enriched       : {len(enriched):,} ({len(enriched)/total*100:.1f}%)")
    print(f" With Eligibility Rules: {len(has_rules):,}")
    print(f" With Benefits Items  : {len(has_benefits):,}")
    print(f" With Required Docs   : {len(has_docs):,}")
    print(f" Empty / Not Found    : {len(empty):,}")
    print(f" Enrichment Errors    : {len(errors):,}")
    print("=" * 60)


def print_scheme(slug, data, as_json=False):
    if as_json:
        print(json.dumps({slug: data}, indent=2, ensure_ascii=False))
        return

    print("=" * 70)
    print(f" Scheme Slug: {slug}")
    print("=" * 70)
    if data.get("empty"):
        print(" [Status: Empty / Not Found]")
        return
    if data.get("error"):
        print(f" [Status: Error: {data.get('error')}]")
        return

    print(f"Eligibility Text Preview:")
    text = data.get("eligibility_text") or "(No text)"
    print(f"  {text[:200]}..." if len(text) > 200 else f"  {text}")

    print("\nParsed Rules:")
    rules = data.get("eligibility_rules") or {}
    for r_k, r_v in rules.items():
        if r_v is not None:
            print(f"  - {r_k}: {r_v}")

    print(f"\nBenefits ({len(data.get('benefits', []))} items):")
    for b in data.get("benefits", [])[:3]:
        print(f"  - [{b.get('benefit_type', 'benefit')}] {b.get('description', '')[:100]}")
    if len(data.get("benefits", [])) > 3:
        print(f"  ... and {len(data.get('benefits', [])) - 3} more")

    print(f"\nDocuments ({len(data.get('documents', []))} items):")
    for d in data.get("documents", [])[:3]:
        print(f"  - {d.get('document_name')}")
    if len(data.get("documents", [])) > 3:
        print(f"  ... and {len(data.get('documents', [])) - 3} more")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Inspect myscheme_enriched.json cache safely")
    parser.add_argument("--stats", action="store_true", help="Show summary stats")
    parser.add_argument("--slug", type=str, help="Lookup scheme by exact slug")
    parser.add_argument("--search", type=str, help="Search schemes by slug substring or keyword")
    parser.add_argument("--random", action="store_true", help="Show a random enriched scheme")
    parser.add_argument("--json", action="store_true", help="Output result as formatted JSON")
    parser.add_argument("--export", type=str, help="Export a specific slug into a standalone JSON file")
    parser.add_argument("--out", type=str, default="data/enriched_cache/exported_scheme.json", help="Export target path")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    cache = load_cache()

    if args.stats:
        print_stats(cache)
        return

    if args.export:
        slug = args.export
        if slug not in cache:
            print(f"Slug '{slug}' not found in cache.")
            sys.exit(1)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({slug: cache[slug]}, f, indent=2, ensure_ascii=False)
        print(f"Exported scheme '{slug}' to {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")
        return

    if args.slug:
        if args.slug in cache:
            print_scheme(args.slug, cache[args.slug], as_json=args.json)
        else:
            print(f"Slug '{args.slug}' not found.")
        return

    if args.random:
        enriched_slugs = [k for k, v in cache.items() if not v.get("empty") and not v.get("error")]
        if enriched_slugs:
            chosen = random.choice(enriched_slugs)
            print_scheme(chosen, cache[chosen], as_json=args.json)
        return

    if args.search:
        q = args.search.lower()
        matches = []
        for k, v in cache.items():
            if q in k.lower():
                matches.append(k)
            elif any(q in str(val).lower() for val in [v.get("eligibility_text"), v.get("benefits")] if val):
                matches.append(k)
        print(f"Found {len(matches)} matches for '{args.search}':")
        for m in matches[:15]:
            status = "empty" if cache[m].get("empty") else "enriched"
            print(f"  - {m} [{status}]")
        if len(matches) > 15:
            print(f"  ... and {len(matches) - 15} more matches. Use --slug <name> to view one.")


if __name__ == "__main__":
    main()
