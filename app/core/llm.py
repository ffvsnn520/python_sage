"""
llm.py - LLM 调用封装
ask()        -> 普通调用，返回完整字符串
ask_stream() -> 流式调用，返回 async generator
"""
from openai import AsyncOpenAI
from app.core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE

_client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


async def ask(messages: list[dict]) -> str:
    response = await _client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
        stream=False,
    )

    if response.usage:
        print("prompt_tokens:", response.usage.prompt_tokens)
        print("completion_tokens:", response.usage.completion_tokens)
        print("total_tokens:", response.usage.total_tokens)


    return response.choices[0].message.content


async def ask_stream(messages: list[dict]):
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
