"""
Day13 deployment checklist.

This script checks the files and config needed for a minimal deployable service.
It does not start Docker, so it is safe to run in a local learning environment.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def require_file(path: str) -> None:
    target = ROOT / path
    if not target.exists():
        raise AssertionError(f"missing required file: {path}")


def require_text(path: str, expected: str) -> None:
    content = (ROOT / path).read_text(encoding="utf-8")
    if expected not in content:
        raise AssertionError(f"{path} missing expected text: {expected}")


def reject_text(path: str, forbidden: str) -> None:
    content = (ROOT / path).read_text(encoding="utf-8")
    if forbidden in content:
        raise AssertionError(f"{path} contains forbidden text: {forbidden}")


def main() -> None:
    for path in [
        ".env.example",
        ".dockerignore",
        "Dockerfile",
        "docker-compose.yml",
        "DEPLOY.md",
    ]:
        require_file(path)

    require_text("Dockerfile", "uvicorn")
    require_text("docker-compose.yml", "/health")
    require_text("docker-compose.yml", "mysql:8.0")
    require_text(".env.example", "API_KEY=replace-with-your-dashscope-api-key")
    require_text("app/core/config.py", "load_dotenv")
    reject_text("app/core/config.py", "sk-")

    print("Day13 deployment checklist passed.")


if __name__ == "__main__":
    main()
