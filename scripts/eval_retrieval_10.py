#!/usr/bin/env python3

import json
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.api.db import get_db, init_pool, pool
from services.api.chatbot.scheme_retriever import find_matching_schemes


def load_benchmark(path: str) -> list[dict]:
    """Load the benchmark queries from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval(benchmark: list[dict], threshold: float = 0.35, limit: int = 5):
    """
    Evaluate retrieval accuracy for each query in the benchmark.
    
    Returns:
        dict with metrics and detailed results
    """
    results = []
    hits = 0
    total_reciprocal_rank = 0.0
    total_precision = 0.0
    total_recall = 0.0
    
    with get_db() as cur:
        for item in benchmark:
            query = item["query"]
            expected_ids = set(item["expected_scheme_ids"])
            expected_names = item["expected_scheme_names"]
            
            # Find matching schemes
            retrieved = find_matching_schemes(query, cur, limit=limit, threshold=threshold)
            retrieved_ids = [str(s["id"]) for s in retrieved]
            
            # Calculate metrics for this query
            relevant_retrieved = [rid for rid in retrieved_ids if rid in expected_ids]
            n_relevant = len(relevant_retrieved)
            n_expected = len(expected_ids)
            
            # Precision@K
            precision = n_relevant / limit if limit > 0 else 0.0
            
            # Recall@K
            recall = n_relevant / n_expected if n_expected > 0 else 0.0
            
            # Reciprocal Rank (rank of first relevant result)
            rr = 0.0
            rank_of_first = None
            for idx, rid in enumerate(retrieved_ids, 1):
                if rid in expected_ids:
                    rr = 1.0 / idx
                    rank_of_first = idx
                    break
            
            # Hit (at least one relevant in top-K)
            is_hit = n_relevant > 0
            if is_hit:
                hits += 1
            
            total_precision += precision
            total_recall += recall
            total_reciprocal_rank += rr
            
            results.append({
                "query_id": item["id"],
                "query": query,
                "expected_names": expected_names,
                "expected_ids": list(expected_ids),
                "retrieved": [
                    {"id": str(s["id"]), "name": s["name"], "similarity": s.get("similarity", 0)}
                    for s in retrieved
                ],
                "retrieved_ids": retrieved_ids,
                "relevant_retrieved": relevant_retrieved,
                "n_relevant": n_relevant,
                "precision_at_k": round(precision, 4),
                "recall_at_k": round(recall, 4),
                "reciprocal_rank": round(rr, 4),
                "rank_of_first": rank_of_first,
                "is_hit": is_hit,
            })
    
    n_queries = len(benchmark)
    
    return {
        "metrics": {
            "total_queries": n_queries,
            "threshold": threshold,
            "limit": limit,
            "precision_at_k": round(total_precision / n_queries, 4) if n_queries > 0 else 0.0,
            "recall_at_k": round(total_recall / n_queries, 4) if n_queries > 0 else 0.0,
            "mrr": round(total_reciprocal_rank / n_queries, 4) if n_queries > 0 else 0.0,
            "hit_rate": round(hits / n_queries, 4) if n_queries > 0 else 0.0,
            "hits": hits,
            "misses": n_queries - hits,
        },
        "results": results,
    }


def print_report(evaluation: dict):
    """Print a formatted evaluation report."""
    metrics = evaluation["metrics"]
    results = evaluation["results"]
    
    print()
    print("=" * 70)
    print("       SCHEME ASSISTANT RETRIEVAL EVALUATION REPORT")
    print("=" * 70)
    print()
    print(f"  Total Queries:        {metrics['total_queries']}")
    print(f"  Similarity Threshold: {metrics['threshold']}")
    print(f"  Top-K Retrieved:      {metrics['limit']}")
    print()
    print("-" * 70)
    print("  METRICS")
    print("-" * 70)
    print(f"  Precision@{metrics['limit']}:    {metrics['precision_at_k']:.4f}")
    print(f"  Recall@{metrics['limit']}:       {metrics['recall_at_k']:.4f}")
    print(f"  MRR:            {metrics['mrr']:.4f}")
    print(f"  Hit Rate@{metrics['limit']}:     {metrics['hit_rate'] * 100:.1f}% ({metrics['hits']}/{metrics['total_queries']})")
    print()
    print("-" * 70)
    print("  DETAILED RESULTS")
    print("-" * 70)
    
    for r in results:
        status = "PASS" if r["is_hit"] else "FAIL"
        print()
        print(f"  [{status}] Q{r['query_id']}: {r['query'][:60]}...")
        print(f"         Expected: {r['expected_names'][0]}")
        
        if r["retrieved"]:
            print(f"         Retrieved (top {len(r['retrieved'])}):")
            for i, s in enumerate(r["retrieved"], 1):
                marker = "<<" if str(s["id"]) in r["expected_ids"] else ""
                print(f"           {i}. {s['name'][:50]} (sim={s['similarity']:.4f}) {marker}")
        
        if r["is_hit"]:
            print(f"         Result: Correct scheme found at rank {r['rank_of_first']}")
        else:
            print(f"         Result: Expected scheme NOT found in top-{metrics['limit']}")
    
    print()
    print("=" * 70)
    
    hit_rate_pct = metrics["hit_rate"] * 100
    if hit_rate_pct >= 90:
        print(f"  RESULT: {hit_rate_pct:.1f}% hit rate@{metrics['limit']} - EXCELLENT!")
    elif hit_rate_pct >= 70:
        print(f"  RESULT: {hit_rate_pct:.1f}% hit rate@{metrics['limit']} - GOOD")
    else:
        print(f"  RESULT: {hit_rate_pct:.1f}% hit rate@{metrics['limit']} - NEEDS IMPROVEMENT")
    
    print("=" * 70)
    print()


def main():
    parser = argparse.ArgumentParser(description="Evaluate scheme retrieval accuracy")
    parser.add_argument(
        "--benchmark",
        default="scripts/eval_benchmark_10.json",
        help="Path to benchmark JSON file"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.35,
        help="Minimum similarity threshold (default: 0.35)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of schemes to retrieve per query (default: 5)"
    )
    args = parser.parse_args()
    
    # Load benchmark
    benchmark_path = Path(args.benchmark)
    if not benchmark_path.exists():
        print(f"ERROR: Benchmark file not found: {benchmark_path}")
        print("Please create the benchmark file first.")
        sys.exit(1)
    
    benchmark = load_benchmark(str(benchmark_path))
    print(f"Loaded {len(benchmark)} test queries from {benchmark_path}")
    
    # Initialize database connection
    init_pool()
    
    # Run evaluation
    evaluation = evaluate_retrieval(benchmark, threshold=args.threshold, limit=args.limit)
    
    # Print report
    print_report(evaluation)
    
    # Save results to JSON
    result_stem = benchmark_path.stem.replace("eval_benchmark", "eval_results", 1)
    if result_stem == benchmark_path.stem:
        result_stem = f"{benchmark_path.stem}_results"
    output_path = benchmark_path.with_name(f"{result_stem}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)
    print(f"Detailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
