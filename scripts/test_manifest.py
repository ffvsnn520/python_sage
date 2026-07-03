import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import DOCS_DIR
from app.ingestion.manifest import build_manifest, load_manifest, save_manifest, is_doc_changed


if __name__ == "__main__":
    old_manifest = load_manifest()

    for md_file in sorted(DOCS_DIR.glob("*.md")):
        changed = is_doc_changed(md_file, old_manifest)
        print(md_file.name, "changed" if changed else "unchanged")

    new_manifest = build_manifest(DOCS_DIR)
    save_manifest(new_manifest)
    print("manifest updated")