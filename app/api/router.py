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

from app.agent.orchestrator import run_agent
from app.core.fallback import (
    has_usable_retrieval,
    llm_unavailable_answer,
    no_retrieval_answer,
    safe_answer,
    service_not_ready_answer,
)
from app.core.llm import ask, ask_stream
from app.core.prompt import build_messages, build_chitchat_messages
from app.core.intent import detect_intent
from app.memory.store import append_history, clear_history, get_history
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


class AgentResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]
    intent: str
    trace: list[dict]


def get_searcher(request: Request):
    searcher = getattr(request.state, "searcher", None)
    if searcher is None:
        raise HTTPException(status_code=503, detail="知识库尚未初始化完成，请稍后重试")
    return searcher


def get_optional_searcher(request: Request):
    return getattr(request.state, "searcher", None)

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
        answer = await safe_answer(messages, ask)
        sources = []

    else:  # rag_query
        searcher = get_optional_searcher(request)
        if searcher is None:
            answer = service_not_ready_answer()
            sources = []
        else:
            chunks = searcher.search(body.query)
            if not has_usable_retrieval(chunks):
                answer = no_retrieval_answer()
                sources = []
            else:
                history = get_history(session_id)
                messages = build_messages(body.query, chunks, history)
                answer = await safe_answer(messages, ask)
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
        searcher = get_optional_searcher(request)
        if searcher is None:
            async def not_ready_gen():
                msg = service_not_ready_answer()
                yield f"data: {msg}\n\n"
                yield "data: [DONE]\n\n"
                append_history(session_id, "user", query)
                append_history(session_id, "assistant", msg)
            return StreamingResponse(not_ready_gen(), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
        chunks = searcher.search(query)
        if not has_usable_retrieval(chunks):
            async def no_retrieval_gen():
                msg = no_retrieval_answer()
                yield f"data: {msg}\n\n"
                yield "data: [DONE]\n\n"
                append_history(session_id, "user", query)
                append_history(session_id, "assistant", msg)
            return StreamingResponse(no_retrieval_gen(), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
        messages = build_messages(query, chunks, history)

    collected = []

    async def event_generator():
        try:
            async for token in ask_stream(messages):
                collected.append(token)
                safe_token = token.replace("\n", "\\n")
                yield f"data: {safe_token}\n\n"
        except Exception:
            logger.exception("stream LLM 调用失败，触发兜底响应")
            msg = llm_unavailable_answer()
            collected.clear()
            collected.append(msg)
            yield f"data: {msg}\n\n"
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
    affected = clear_history(session_id)
    if affected:
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


@router.post("/agent/ask", response_model=AgentResponse)
async def agent_ask_endpoint(request: Request, body: AskRequest):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    session_id = body.session_id
    history = get_history(session_id)
    result = await run_agent(
        query=body.query,
        history=history,
        tool_registry=tool_registry,
        tool_context=build_tool_context(request),
    )

    append_history(session_id, "user", body.query)
    append_history(session_id, "assistant", result["answer"])

    return AgentResponse(**result)
