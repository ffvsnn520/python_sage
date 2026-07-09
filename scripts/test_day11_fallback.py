"""Day11 cold-start and fallback smoke tests.

Run:
  python scripts/test_day11_fallback.py
"""
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.agent.orchestrator import run_agent
from app.core.fallback import (
    has_usable_retrieval,
    llm_unavailable_answer,
    no_retrieval_answer,
    service_not_ready_answer,
)
from app.tools.php_tools import build_tool_registry


class EmptySearcher:
    def search(self, query: str) -> list[dict]:
        return []


class FakeSearcher:
    def search(self, query: str) -> list[dict]:
        return [
            {
                "content": "PDO 连接 MySQL 超时通常需要检查网络、端口、防火墙和连接超时配置。",
                "source": "pdo-connection-timeout.md",
                "score": 0.92,
            }
        ]


async def failing_answerer(messages: list[dict[str, str]]) -> str:
    raise RuntimeError("mock llm timeout")


async def ok_answerer(messages: list[dict[str, str]]) -> str:
    return "测试答案"


async def main() -> None:
    registry = build_tool_registry()

    assert has_usable_retrieval([{"source": "a.md"}]) is True
    assert has_usable_retrieval([]) is False
    assert "知识库" in service_not_ready_answer()
    assert "检索" in no_retrieval_answer()
    assert "模型服务" in llm_unavailable_answer()

    cold = await run_agent(
        query="PHP 连接 MySQL 超时怎么排查？",
        history=[],
        tool_registry=registry,
        tool_context={"searcher": None, "ready": False, "chunk_count": 0, "tool_count": 2},
        answerer=ok_answerer,
    )
    assert cold["trace"][-1]["reason"] == "tool_failed"
    assert "知识库正在初始化" in cold["answer"]

    empty = await run_agent(
        query="PHP 出现一个知识库没有的奇怪错误怎么办？",
        history=[],
        tool_registry=registry,
        tool_context={"searcher": EmptySearcher(), "ready": True, "chunk_count": 0, "tool_count": 2},
        answerer=ok_answerer,
    )
    assert empty["trace"][-1]["reason"] == "no_search_results"
    assert "检索到足够相关" in empty["answer"]

    llm_failed = await run_agent(
        query="PHP 连接 MySQL 超时怎么排查？",
        history=[],
        tool_registry=registry,
        tool_context={"searcher": FakeSearcher(), "ready": True, "chunk_count": 1, "tool_count": 2},
        answerer=failing_answerer,
    )
    assert llm_failed["trace"][-1]["reason"] == "enough_to_answer"
    assert "模型服务暂时不可用" in llm_failed["answer"]

    print("Day11 fallback tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
