"""
Day8 tool calling smoke tests.

Run:
  python scripts/test_day8_tools.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools.php_tools import build_tool_registry


class FakeSearcher:
    def search(self, query: str) -> list[dict]:
        return [
            {"content": f"排查资料: {query}", "source": "pdo-connection-timeout.md", "score": 0.91},
            {"content": "检查 PHP-FPM 和数据库网络", "source": "nginx-php-502.md", "score": 0.62},
        ]


def main() -> None:
    registry = build_tool_registry()

    context = {
        "searcher": FakeSearcher(),
        "ready": True,
        "chunk_count": 12,
        "tool_count": len(registry.list_schemas()),
    }

    print("=" * 60)
    print("Day8 tool schemas")
    print("=" * 60)
    for schema in registry.list_schemas():
        print(f"- {schema['name']}: {schema['description']} risk={schema['risk_level']}")

    print("\n" + "=" * 60)
    print("Call: search_knowledge_base")
    print("=" * 60)
    result = registry.execute(
        "search_knowledge_base",
        {"query": "PHP 连接 MySQL 超时怎么排查？", "top_k": 1},
        context,
    )
    print(result)
    assert result["success"] is True
    assert len(result["data"]["results"]) == 1

    print("\n" + "=" * 60)
    print("Call: get_service_status")
    print("=" * 60)
    result = registry.execute("get_service_status", {}, context)
    print(result)
    assert result["success"] is True
    assert result["data"]["ready"] is True

    print("\n" + "=" * 60)
    print("Call: validation failure")
    print("=" * 60)
    result = registry.execute("search_knowledge_base", {"query": "", "top_k": 99}, context)
    print(result)
    assert result["success"] is False

    print("\nDay8 tool tests passed.")


if __name__ == "__main__":
    main()
