import hashlib
import json
from pathlib import Path

from app.core.config import MANIFEST_PATH


def calculate_file_hash(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}

    content = MANIFEST_PATH.read_text(encoding="utf-8").strip()
    if not content:
        return {}

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def save_manifest(data: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_doc_changed(path: Path, manifest: dict) -> bool:
    current_hash = calculate_file_hash(path)
    old_info = manifest.get(path.name)

    if old_info is None:
        return True

    return old_info.get("hash") != current_hash


def get_changed_docs(docs_dir: Path, old_manifest: dict) -> list[Path]:
    changed_docs = []

    for md_file in sorted(docs_dir.glob("*.md")):
        if is_doc_changed(md_file, old_manifest):
            changed_docs.append(md_file)

    return changed_docs


def build_manifest(docs_dir: Path) -> dict:
    manifest = {}

    for md_file in sorted(docs_dir.glob("*.md")):
        manifest[md_file.name] = {
            "hash": calculate_file_hash(md_file),
        }

    return manifest
