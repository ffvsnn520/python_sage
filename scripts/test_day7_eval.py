"""
Day7 retrieval evaluation.

Run after Qdrant has been initialized:
  python scripts/test_day7_eval.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.loader import load_docs
from app.ingestion.indexer import load_existing_index
from app.retrieval.searcher import Searcher


EVAL_CASES = [
    {
        "query": "PHP 连接 MySQL 超时怎么排查？",
        "expected_source": "pdo-connection-timeout.md",
    },
    {
        "query": "SQLSTATE HY000 2002 Connection timed out 是什么问题？",
        "expected_source": "pdo-connection-timeout.md",
    },
    {
        "query": "Nginx 502 Bad Gateway 怎么解决？",
        "expected_source": "nginx-php-502.md",
    },
    {
        "query": "PHP-FPM 没启动导致 502 怎么查？",
        "expected_source": "nginx-php-502.md",
    },
    {
        "query": "PHP session 登录后突然失效怎么办？",
        "expected_source": "session-not-working.md",
    },
    {
        "query": "多台服务器 session 丢失怎么解决？",
        "expected_source": "session-not-working.md",
    },
    {
        "query": "PHP 导出 Excel 内存溢出怎么办？",
        "expected_source": "memory-exhausted-export.md",
    },
    {
        "query": "Allowed memory size exhausted 怎么处理？",
        "expected_source": "memory-exhausted-export.md",
    },
    {
        "query": "MySQL 慢查询怎么优化？",
        "expected_source": "mysql-slow-query.md",
    },
    {
        "query": "接口查询超时，SQL 很慢怎么排查？",
        "expected_source": "mysql-slow-query.md",
    },
]


def find_rank(sources: list[str], expected_source: str) -> int | None:
    """
    Return the 1-based rank of expected_source in sources.

    If the expected source is not found, return None.
    """
    for index, source in enumerate(sources, start=1):
        if source == expected_source:
            return index
    return None


def hit_at_k(rank: int | None, k: int) -> int:
    if rank is None:
        return 0
    return 1 if rank <= k else 0


def reciprocal_rank(rank: int | None) -> float:
    if rank is None:
        return 0.0
    return 1.0 / rank


def main() -> None:
    print("=" * 60)
    print("Day7 retrieval evaluation: Hit@K + MRR")
    print("=" * 60)

    docs = load_docs()
    vectorstore, chunks = load_existing_index(docs)
    searcher = Searcher(vectorstore, chunks)

    hit1_total = 0
    hit3_total = 0
    mrr_total = 0.0

    for i, case in enumerate(EVAL_CASES, start=1):
        query = case["query"]
        expected = case["expected_source"]

        results = searcher.search(query)
        sources = [result["source"] for result in results]
        rank = find_rank(sources, expected)

        hit1 = hit_at_k(rank, 1)
        hit3 = hit_at_k(rank, 3)
        rr = reciprocal_rank(rank)

        hit1_total += hit1
        hit3_total += hit3
        mrr_total += rr

        rank_text = str(rank) if rank is not None else "miss"
        print(f"\n[{i}] {query}")
        print(f"    expected: {expected}")
        print(f"    sources : {sources}")
        print(f"    rank={rank_text} hit@1={hit1} hit@3={hit3} rr={rr:.4f}")

    total = len(EVAL_CASES)
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"cases : {total}")
    print(f"Hit@1: {hit1_total / total:.4f}")
    print(f"Hit@3: {hit3_total / total:.4f}")
    print(f"MRR  : {mrr_total / total:.4f}")


if __name__ == "__main__":
    main()
