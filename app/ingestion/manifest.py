import hashlib
import json
from pathlib import Path

from app.core.config import MANIFEST_PATH
from app.core.config import DOCS_DIR


def calculate_file_hash(path: Path) -> str:
    """
    计算文件内容的 sha256 指纹。
    文件内容不变，hash 就不变；文件内容变化，hash 基本一定变化。
    """
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def load_manifest() -> dict:
    """
    从 data/manifest.json 读取旧的文档指纹表。
    第一次运行时文件不存在，返回空字典。
    """
    if not MANIFEST_PATH.exists():
        return {}

    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    """
    把新的文档指纹表保存到 data/manifest.json。
    """
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_doc_changed(path: Path, manifest: dict) -> bool:
    """
    判断某个文档相对 manifest 是否发生变化。
    新文件、内容变化，都返回 True；内容没变返回 False。
    """
    current_hash = calculate_file_hash(path)
    old_info = manifest.get(path.name)

    if old_info is None:
        return True

    return old_info.get("hash") != current_hash


def build_manifest(docs_dir: Path) -> dict:
    """
    扫描 docs 目录，生成一份新的 manifest 数据。
    """
    manifest = {}

    for md_file in sorted(docs_dir.glob("*.md")):
        manifest[md_file.name] = {
            "hash": calculate_file_hash(md_file),
        }

    return manifest