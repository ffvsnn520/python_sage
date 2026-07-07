"""
Day9 minimal Agent orchestration smoke tests.

Run:
  python scripts/test_day9_agent.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.orchestrator import run_agent
from app.tools.php_tools import build_tool_registry


class FakeSearcher:
    def search(self, query: str) -> list[dict]:
        return [
            {"content": f"排查资料: {query}", "source": "pdo-connection-timeout.md", "score": 0.91},
            {"content": "检查 PHP-FPM 和数据库网络", "source": "nginx-php-502.md", "score": 0.62},
        ]


async def fake_answerer(messages: list[dict[str, str]]) -> str:
    return "这是基于知识库生成的测试答案。"


async def main() -> None:
    registry = build_tool_registry()
    
    context = {
        "searcher": FakeSearcher(),
        "ready": True,
        "chunk_count": 12,
        "tool_count": len(registry.list_schemas()),
    }

    print("=" * 60)
    print("Agent: service status")
    print("=" * 60)
    result = await run_agent(
        "服务健康状态怎么样？",
        [],
        registry,
        context,
        answerer=fake_answerer,
    )
    print(result)
    assert result["intent"] == "service_status"
    assert result["trace"][1]["tool"] == "get_service_status"
    assert "已就绪" in result["answer"]

    print("\n" + "=" * 60)
    print("Agent: knowledge search")
    print("=" * 60)
    result = await run_agent(
        "PHP 连接 MySQL 超时怎么排查？",
        [],
        registry,
        context,
        answerer=fake_answerer,
    )
    print(result)
    assert result["intent"] == "rag_query"
    assert result["trace"][1]["tool"] == "search_knowledge_base"
    assert result["sources"] == ["pdo-connection-timeout.md", "nginx-php-502.md"]

    print("\nDay9 agent tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
