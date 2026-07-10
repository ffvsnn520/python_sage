"""Day12 retrieval performance baseline.

Run after Qdrant has been initialized:
  python scripts/test_day12_performance.py

This script measures retrieval latency and retrieval quality together.
An optimization is only useful when it improves latency without silently
damaging Hit@K or MRR.
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.indexer import load_existing_index
from app.ingestion.loader import load_docs
from app.retrieval.searcher import Searcher
from scripts.test_day7_eval import (
    EVAL_CASES,
    find_rank,
    hit_at_k,
    reciprocal_rank,
)


def percentile(values: list[float], percent: float) -> float:
    """Return the nearest-rank percentile for a small benchmark dataset."""
    if not values:
        return 0.0

    ordered = sorted(values)
    rank = max(1, int(len(ordered) * percent + 0.999999))
    return ordered[min(rank - 1, len(ordered) - 1)]


def main() -> None:
    print("=" * 72)
    print("Day12 retrieval performance baseline")
    print("=" * 72)


    init_started = time.perf_counter()

    docs = load_docs()
    vectorstore, chunks = load_existing_index(docs)
    searcher = Searcher(vectorstore, chunks)
    init_ms = (time.perf_counter() - init_started) * 1000

    latencies_ms: list[float] = []
    profiles: list[dict[str, float]] = []
    hit1_total = 0
    hit3_total = 0
    mrr_total = 0.0

    for index, case in enumerate(EVAL_CASES, start=1):
        started = time.perf_counter()
        results, profile = searcher.search(case["query"], profile=True)
        latency_ms = (time.perf_counter() - started) * 1000
        latencies_ms.append(latency_ms)
        profiles.append(profile)

        sources = [result["source"] for result in results]

        rank = find_rank(sources, case["expected_source"])
        hit1_total += hit_at_k(rank, 1)
        hit3_total += hit_at_k(rank, 3)
        mrr_total += reciprocal_rank(rank)

        rank_text = str(rank) if rank is not None else "miss"
        print(
            f"[{index:02d}] {latency_ms:8.2f}ms "
            f"vector={profile['vector_ms']:7.2f}ms "
            f"bm25={profile['bm25_ms']:6.2f}ms "
            f"rerank={profile['rerank_ms']:8.2f}ms "
            f"candidates={profile['candidate_count']:<2} "
            f"rerank_n={profile['rerank_candidate_count']:<2} "
            f"rank={rank_text:<4} query={case['query']}"
        )

    total = len(EVAL_CASES)
    avg_profile = {
        key: statistics.fmean(profile[key] for profile in profiles)
        for key in [
            "vector_ms",
            "bm25_ms",
            "merge_ms",
            "rerank_ms",
            "format_ms",
            "candidate_count",
            "rerank_candidate_count",
        ]
    }

    print("\n" + "=" * 72)
    print("Summary")
    print("=" * 72)
    print(f"chunks       : {len(chunks)}")
    print(f"init         : {init_ms:.2f}ms")
    print(f"requests     : {total}")
    print(f"latency avg  : {statistics.fmean(latencies_ms):.2f}ms")
    print(f"latency p50  : {statistics.median(latencies_ms):.2f}ms")
    print(f"latency p95  : {percentile(latencies_ms, 0.95):.2f}ms")
    print(f"latency max  : {max(latencies_ms):.2f}ms")
    print(f"vector avg   : {avg_profile['vector_ms']:.2f}ms")
    print(f"bm25 avg     : {avg_profile['bm25_ms']:.2f}ms")
    print(f"merge avg    : {avg_profile['merge_ms']:.2f}ms")
    print(f"rerank avg   : {avg_profile['rerank_ms']:.2f}ms")
    print(f"format avg   : {avg_profile['format_ms']:.2f}ms")
    print(f"candidates   : {avg_profile['candidate_count']:.2f}")
    print(f"rerank n     : {avg_profile['rerank_candidate_count']:.2f}")
    print(f"Hit@1        : {hit1_total / total:.4f}")
    print(f"Hit@3        : {hit3_total / total:.4f}")
    print(f"MRR          : {mrr_total / total:.4f}")


if __name__ == "__main__":
    main()
