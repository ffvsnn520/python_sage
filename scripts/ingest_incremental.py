"""
scripts/ingest_incremental.py - 增量摄入变更文档到 Qdrant
用法: python scripts/ingest_incremental.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import DOCS_DIR
from app.ingestion.indexer import update_index
from app.ingestion.loader import load_docs_by_paths
from app.ingestion.manifest import build_manifest, get_changed_docs, load_manifest, save_manifest


if __name__ == "__main__":
    print("=" * 50)
    print("PHP-Sage 增量文档摄入")
    print("=" * 50)

    print("\n[1] 检查文档变化...")
    old_manifest = load_manifest()
    changed_paths = get_changed_docs(DOCS_DIR, old_manifest)

    if not changed_paths:
        print("没有文档变化，跳过摄入")
        sys.exit(0)

    print(f"发现 {len(changed_paths)} 个变化文档:")
    for path in changed_paths:
        print(f"  - {path.name}")

    print("\n[2] 加载变化文档...")
    docs = load_docs_by_paths(changed_paths)

    print("\n[3] 删除旧 chunks + 写入新 chunks...")
    vectorstore, chunks = update_index(docs)

    print("\n[4] 更新 manifest...")
    new_manifest = build_manifest(DOCS_DIR)
    save_manifest(new_manifest)

    print(f"\n✓ 增量摄入完成，本次写入 {len(chunks)} 个 chunk")
