"""
scripts/test_search.py - 召回效果测试
用法: python scripts/test_search.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.loader import load_docs
from app.ingestion.indexer import build_index
from app.retrieval.searcher import Searcher

# 测试问题列表 - 模拟真实用户提问
TEST_QUERIES = [
    "导出Excel时内存不够怎么办",
    "PHP连接MySQL失败 Connection timed out",
    "session突然失效是什么原因",
    "慢查询怎么排查",
    "502 Bad Gateway 怎么解决",
]

if __name__ == "__main__":
    print("=" * 50)
    print("PHP-Sage 召回效果测试")
    print("=" * 50)

    # 重新摄入（保证数据最新）
    print("\n[初始化] 加载文档 + 构建索引...")
    docs = load_docs()

    print("docs", docs)
    vectorstore, chunks = build_index(docs)
    searcher = Searcher(vectorstore, chunks)

    print("\n" + "=" * 50)
    print("开始测试")
    print("=" * 50)

    for query in TEST_QUERIES:
        print(f"\n【问题】{query}")
        print("-" * 40)
        results = searcher.search(query)

        if not results:
            print("  ✗ 未召回任何结果")
            continue

        for i, r in enumerate(results, 1):
            print(f"  [{i}] score={r['score']}  来源={r['source']}")
            # 只打印前100字，看召回内容是否相关
            preview = r["content"][:100].replace("\n", " ")
            print(f"      {preview}...")
