"""
scripts/ingest.py - 一键摄入文档到 Qdrant
用法: python scripts/ingest.py
"""
import sys
from pathlib import Path

# 把项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.loader import load_docs
from app.ingestion.indexer import build_index
from app.ingestion.manifest import build_manifest, save_manifest
from app.core.config import DOCS_DIR

if __name__ == "__main__":
    print("=" * 50)
    print("PHP-Sage 文档摄入")
    print("=" * 50)

    print("\n[1] 加载文档...")
    docs = load_docs()
    print(f"共加载 {len(docs)} 个文档")

    print("\n[2] 切块 + 写入 Qdrant...")
    vectorstore, chunks = build_index(docs)

    print("\n[3] 保存 manifest...")
    manifest = build_manifest(DOCS_DIR)
    save_manifest(manifest)

    print("\n✓ 摄入完成，可以运行 test_search.py 验证召回效果")
