"""Fallback policies for cold start and controlled degradation."""
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger("php_sage.fallback")

Answerer = Callable[[list[dict[str, str]]], Awaitable[str]]


SERVICE_NOT_READY_ANSWER = (
    "知识库正在初始化或暂时不可用，请稍后重试。"
    "如果你是在本地调试，可以先确认摄入脚本已经执行，并检查 /health 的 ready 状态。"
)

NO_RETRIEVAL_ANSWER = (
    "我没有在当前知识库里检索到足够相关的资料。"
    "建议补充更具体的 PHP 错误信息、日志关键字、组件名称或现象，例如 SQLSTATE、502、PHP-FPM、session 等。"
)

LLM_UNAVAILABLE_ANSWER = (
    "当前模型服务暂时不可用，系统没有继续生成答案。"
    "你可以稍后重试；如果是排障场景，建议先根据检索来源查看原始知识库文档。"
)

TOOL_FAILED_ANSWER = (
    "工具调用失败，系统已停止继续重试，避免重复调用造成额外风险。"
    "建议稍后重试，或先检查服务状态和工具参数。"
)


def service_not_ready_answer() -> str:
    return SERVICE_NOT_READY_ANSWER


def no_retrieval_answer() -> str:
    return NO_RETRIEVAL_ANSWER


def llm_unavailable_answer() -> str:
    return LLM_UNAVAILABLE_ANSWER


def tool_failed_answer(error: str | None = None) -> str:
    if not error:
        return TOOL_FAILED_ANSWER
    return f"{TOOL_FAILED_ANSWER} 错误信息：{error}"


def has_usable_retrieval(chunks: list[dict] | None) -> bool:
    return bool(chunks)


async def safe_answer(
    messages: list[dict[str, str]],
    answerer: Answerer,
    fallback_answer: str | None = None,
) -> str:
    """Call the LLM once and return a controlled answer if it fails."""
    try:
        return await answerer(messages)
    except Exception:
        logger.exception("LLM 调用失败，触发兜底响应")
        return fallback_answer or llm_unavailable_answer()
