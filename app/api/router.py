"""
router.py - 问答接口

POST /ask
  入参：{"query": "PHP连接MySQL失败怎么办"}
  出参：{"query": "...", "answer": "...", "sources": [...]}

GET  /ask/stream?query=xxx
  出参：SSE 流式文本（text/event-stream），打字机效果
  使用 GET 是因为 EventSource 浏览器 API 只支持 GET
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.llm import ask, ask_stream
from app.core.prompt import build_messages

router = APIRouter()


# ── 数据结构定义 ─────────────────────────────────────────────────────

class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    query: str
    answer: str           # LLM 生成的真实回答（Day3 新增）
    sources: list[str]    # 参考来源文件名列表


# ── POST /ask：普通接口，等待完整回答 ────────────────────────────────

@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(request: Request, body: AskRequest):
    """
    知识库问答接口（非流式）
    流程：query → searcher 召回 chunks → 拼 prompt → LLM → 返回 answer
    """
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    # 1. 召回相关 chunks
    searcher = request.state.searcher
    chunks = searcher.search(body.query)

    # 2. 构建 prompt（把 chunks 塞进上下文）
    messages = build_messages(body.query, chunks)


    # 3. 调用 LLM，等待完整回答
    answer = await ask(messages)


    # 4. 收集来源文件名（去重）
    sources = list(dict.fromkeys(c["source"] for c in chunks))


    return AskResponse(
        query=body.query,
        answer=answer,
        sources=sources,
    )


# ── GET /ask/stream：SSE 流式接口，打字机效果 ────────────────────────

@router.get("/ask/stream")
async def ask_stream_endpoint(query: str, request: Request):
    """
    流式问答接口（SSE）
    使用 GET + query 参数，浏览器 EventSource 可直接消费。

    SSE 格式：每行 "data: <内容>\\n\\n"
    约定：
      - 普通 token：data: <token>
      - 结束标记：data: [DONE]
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    searcher = request.state.searcher
    chunks = searcher.search(query)
    messages = build_messages(query, chunks)

    async def event_generator():
        """
        异步生成器：把 LLM 的 token 流转成 SSE 格式。

        SSE 协议要求每条消息格式：
            data: <内容>\n\n
        浏览器的 EventSource 看到 \n\n 才认为一条消息结束。
        """
        async for token in ask_stream(messages):
            # 把 token 里的换行替换成空格，避免破坏 SSE 帧格式
            # （真正的换行用 \n 表示，客户端自行处理）
            safe_token = token.replace("\n", "\\n")
            yield f"data: {safe_token}\n\n"

        # 发送结束标记，让客户端知道流结束了
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",          # 禁止缓存，确保实时推送
            "X-Accel-Buffering": "no",            # 禁止 Nginx 缓冲（生产环境关键）
        },
    )
