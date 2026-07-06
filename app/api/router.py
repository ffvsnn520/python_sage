"""
router.py - 问答接口（Day4：意图识别 + 多轮对话 + session管理）

POST /ask
  入参：{"query": "...", "session_id": "abc", "history": [...]}
  出参：{"query": "...", "answer": "...", "sources": [...], "intent": "..."}

GET /ask/stream?query=xxx&session_id=xxx
  出参：SSE 流式

DELETE /session/{session_id}     → 清除历史
GET    /session/{session_id}/history → 查看历史（调试用）
"""
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.llm import ask, ask_stream
from app.core.prompt import build_messages, build_chitchat_messages
from app.core.intent import detect_intent
from app.tools.php_tools import build_tool_registry

router = APIRouter()
logger = logging.getLogger("php_sage.api")
tool_registry = build_tool_registry()


class HistoryItem(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    query: str
    session_id: str = "default"
    history: list[HistoryItem] = Field(default_factory=list)


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]
    intent: str


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    success: bool
    tool: str
    error: str | None
    data: dict | None


# 内存级 session store，key=session_id，value=最近 MAX_HISTORY 条消息
_sessions: dict[str, list[dict]] = {}
MAX_HISTORY = 6


def get_history(session_id: str) -> list[dict]:
    return _sessions.get(session_id, [])


def append_history(session_id: str, role: str, content: str):
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})
    if len(_sessions[session_id]) > MAX_HISTORY:
        _sessions[session_id] = _sessions[session_id][-MAX_HISTORY:]


def get_searcher(request: Request):
    searcher = getattr(request.state, "searcher", None)
    if searcher is None:
        raise HTTPException(status_code=503, detail="知识库尚未初始化完成，请稍后重试")
    return searcher

def build_tool_context(request: Request) -> dict:
    return {
        "searcher": getattr(request.state, "searcher", None),
        "ready": getattr(request.state, "ready", False),
        "chunk_count": getattr(request.state, "chunk_count", 0),
        "tool_count": len(tool_registry.list_schemas()),
    }


@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(request: Request, body: AskRequest):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    session_id = body.session_id

    # 1. 意图识别
    intent = await detect_intent(body.query)
    logger.info("intent query=%r session=%s -> %s", body.query, session_id, intent)

    # 2. 根据意图分流
    if intent == "out_of_scope":
        answer = "抱歉，我只能回答 PHP 生产环境相关的技术问题，这个问题超出了我的知识范围。"
        sources = []

    elif intent == "chitchat":
        history = get_history(session_id)
        messages = build_chitchat_messages(body.query, history)
        answer = await ask(messages)
        sources = []

    else:  # rag_query
        searcher = get_searcher(request)
        chunks = searcher.search(body.query)
        history = get_history(session_id)
        messages = build_messages(body.query, chunks, history)
        answer = await ask(messages)
        sources = list(dict.fromkeys(c["source"] for c in chunks))

    # 3. 写入 session（先读后写，顺序不能反）
    append_history(session_id, "user", body.query)
    append_history(session_id, "assistant", answer)

    return AskResponse(query=body.query, answer=answer, sources=sources, intent=intent)


@router.get("/ask/stream")
async def ask_stream_endpoint(query: str, request: Request, session_id: str = "default"):
    if not query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    intent = await detect_intent(query)
    logger.info("intent stream query=%r session=%s -> %s", query, session_id, intent)

    history = get_history(session_id)

    if intent == "out_of_scope":
        async def out_of_scope_gen():
            msg = "抱歉，我只能回答 PHP 生产环境相关的技术问题，这个问题超出了我的知识范围。"
            yield f"data: {msg}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(out_of_scope_gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    elif intent == "chitchat":
        messages = build_chitchat_messages(query, history)
    else:
        searcher = get_searcher(request)
        chunks = searcher.search(query)
        messages = build_messages(query, chunks, history)

    collected = []

    async def event_generator():
        async for token in ask_stream(messages):
            collected.append(token)
            safe_token = token.replace("\n", "\\n")
            yield f"data: {safe_token}\n\n"
        yield "data: [DONE]\n\n"
        # 流结束后才能拼完整答案，再写 session
        full_answer = "".join(collected)
        append_history(session_id, "user", query)
        append_history(session_id, "assistant", full_answer)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]
        return {"message": f"session {session_id!r} 已清除"}
    return {"message": f"session {session_id!r} 不存在"}


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    return {"session_id": session_id, "history": get_history(session_id)}


@router.get("/tools")
async def list_tools():
    return {"tools": tool_registry.list_schemas()}


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: Request, body: ToolCallRequest):
    result = tool_registry.execute(body.name, body.arguments, build_tool_context(request))
    return ToolCallResponse(**result)
