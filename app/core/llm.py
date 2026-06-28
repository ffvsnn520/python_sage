"""
llm.py - LLM 调用封装

提供两种调用方式：
  1. ask()        → 普通调用，返回完整字符串
  2. ask_stream() → 流式调用，返回 async generator（每次 yield 一个 token chunk）

使用 OpenAI 兼容接口，复用 langgraph_agent 的阿里云 DashScope 配置。

Day4 说明：
  ask() 被 intent.py 和 router.py 共用。
  intent.py 用它做单轮分类；router.py 用它做 RAG 问答和闲聊。
  所以 ask() 保持通用，不绑定任何业务逻辑。
"""
from openai import AsyncOpenAI
from app.core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE

# 创建异步客户端（全局复用，避免每次请求重建连接）
_client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


async def ask(messages: list[dict]) -> str:
    """
    非流式调用，等待完整回答后返回字符串。
    """
    response = await _client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
        stream=False,
    )
    return response.choices[0].message.content


async def ask_stream(messages: list[dict]):
    """
    流式调用，返回 async generator，每次 yield 一个 token 字符串。
    用于 SSE 推送（打字机效果）。
    """
    stream = await _client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
