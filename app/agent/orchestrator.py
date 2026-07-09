"""Minimal Day9 Agent orchestration.

The goal is intentionally small: show how an Agent chooses a tool,
observes the result, reflects on whether it is enough, and then stops.
"""
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.fallback import (
    has_usable_retrieval,
    no_retrieval_answer,
    safe_answer,
    service_not_ready_answer,
    tool_failed_answer,
)
from app.core.intent import detect_intent
from app.core.llm import ask
from app.core.prompt import build_chitchat_messages, build_messages
from app.tools.registry import ToolRegistry


Answerer = Callable[[list[dict[str, str]]], Awaitable[str]]


STATUS_KEYWORDS = ("状态", "健康", "health", "ready", "就绪", "知识库加载")


async def run_agent(
    query: str,
    history: list[dict],
    tool_registry: ToolRegistry,
    tool_context: dict[str, Any],
    max_steps: int = 3,
    answerer: Answerer = ask,
) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []

    if _looks_like_status_query(query):
        intent = "service_status"
    else:
        intent = await detect_intent(query)


    trace.append(
        {
            "stage": "planner",
            "thought": "判断用户目标，并选择下一步动作",
            "intent": intent,
        }
    )

    if intent == "out_of_scope":
        answer = "抱歉，我只能回答 PHP 生产环境相关的技术问题，这个问题超出了我的知识范围。"
        trace.append({"stage": "stop", "reason": "out_of_scope"})
        return _final(query, answer, [], intent, trace)

    if intent == "chitchat":
        messages = build_chitchat_messages(query, history)
        answer = await safe_answer(messages, answerer)
        trace.append({"stage": "stop", "reason": "chitchat_answered"})
        return _final(query, answer, [], intent, trace)

    tool_name = _select_tool(intent)
    arguments = _build_tool_arguments(tool_name, query)

    for step in range(1, max_steps + 1):
        trace.append(
            {
                "stage": "executor",
                "step": step,
                "tool": tool_name,
                "arguments": arguments,
            }
        )

        observation = tool_registry.execute(tool_name, arguments, tool_context)
        trace.append({"stage": "observation", "step": step, "result": observation})

        reflection = _reflect(tool_name, observation)
        trace.append({"stage": "reflection", "step": step, **reflection})

        if not reflection["continue"]:
            answer, sources = await _build_final_answer(
                query=query,
                history=history,
                tool_name=tool_name,
                observation=observation,
                answerer=answerer,
            )
            trace.append({"stage": "stop", "reason": reflection["reason"]})
            return _final(query, answer, sources, intent, trace)

        if step == max_steps:
            answer = "工具连续没有得到可用结果，建议稍后重试或补充更具体的问题。"
            trace.append({"stage": "stop", "reason": "max_steps_reached"})
            return _final(query, answer, [], intent, trace)

    answer = "Agent 未能完成任务。"
    trace.append({"stage": "stop", "reason": "unexpected_exit"})
    return _final(query, answer, [], intent, trace)


def _looks_like_status_query(query: str) -> bool:
    lowered = query.lower()
    return any(keyword in lowered for keyword in STATUS_KEYWORDS)


def _select_tool(intent: str) -> str:
    if intent == "service_status":
        return "get_service_status"
    return "search_knowledge_base"


def _build_tool_arguments(tool_name: str, query: str) -> dict[str, Any]:
    if tool_name == "get_service_status":
        return {}
    return {"query": query, "top_k": 3}


def _reflect(tool_name: str, observation: dict[str, Any]) -> dict[str, Any]:
    if not observation["success"]:
        return {
            "continue": False,
            "enough": False,
            "reason": "tool_failed",
        }

    data = observation["data"] or {}
    if tool_name == "search_knowledge_base" and not data.get("results"):
        return {
            "continue": False,
            "enough": False,
            "reason": "no_search_results",
        }

    return {
        "continue": False,
        "enough": True,
        "reason": "enough_to_answer",
    }


async def _build_final_answer(
    query: str,
    history: list[dict],
    tool_name: str,
    observation: dict[str, Any],
    answerer: Answerer,
) -> tuple[str, list[str]]:
    if not observation["success"]:
        error = observation.get("error")
        if "知识库尚未初始化" in str(error):
            return service_not_ready_answer(), []
        return tool_failed_answer(error), []

    data = observation["data"] or {}
    if tool_name == "get_service_status":
        ready = "已就绪" if data.get("ready") else "未就绪"
        answer = (
            f"当前服务状态：{ready}。"
            f"知识库 chunk 数量：{data.get('chunk_count', 0)}，"
            f"已注册工具数量：{data.get('tool_count', 0)}。"
        )
        return answer, []

    results = data.get("results", [])
    if not has_usable_retrieval(results):
        return no_retrieval_answer(), []

    messages = build_messages(query, results, history)
    answer = await safe_answer(messages, answerer)
    sources = data.get("sources", [])
    return answer, sources


def _final(
    query: str,
    answer: str,
    sources: list[str],
    intent: str,
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "intent": intent,
        "trace": trace,
    }
