"""
loader.py - 从 docs/ 目录加载 md 文档
"""
from pathlib import Path
from app.core.config import DOCS_DIR


def load_docs() -> list[dict]:
    """
    读取 docs/ 下所有 .md 文件
    返回 [{"filename": "xxx.md", "content": "..."}]
    """
    docs = []
    for md_file in sorted(Path(DOCS_DIR).glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        docs.append({
            "filename": md_file.name,
            "content": content,
        })
        print(f"  已加载: {md_file.name} ({len(content)} 字符)")
    return docs
