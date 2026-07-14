"""
main.py - FastAPI 启动入口

启动命令：
  python main.py
  或
  uvicorn main:app --reload --port 8000
"""
from contextlib import asynccontextmanager
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.ingestion.loader import load_docs
from app.ingestion.indexer import load_existing_index
from app.retrieval.searcher import Searcher
from app.api.router import router
from app.core.logging import setup_logging
from app.memory.store import init_memory_store


setup_logging()
logger = logging.getLogger("php_sage.main")


# lifespan：应用启动时初始化，关闭时清理
# 替代旧版的 @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("正在初始化对话历史存储...")
    init_memory_store()

    logger.info("正在加载已有知识库...")
    docs = load_docs()
    vectorstore, chunks = load_existing_index(docs)

    searcher = Searcher(vectorstore, chunks)

    # 把 searcher 挂到 app.state，路由里可以取到
    app.state.searcher = searcher
    app.state.chunk_count = len(chunks)
    app.state.ready = True
    logger.info("知识库加载完成，服务就绪，文档块数量=%s", len(chunks))

    yield  # 服务运行中

    # 关闭时执行（清理资源）
    app.state.ready = False
    logger.info("服务关闭")


app = FastAPI(
    title="PHP-Sage",
    description="PHP生产问题知识库问答服务",
    version="0.1.0",
    lifespan=lifespan,
)

def get_request_id(request: Request):
    return getattr(request.state, "request_id", "-")

# 记录每个请求的状态码和耗时，排查线上问题时优先看这里。
@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    cost_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s %s %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        get_request_id(request),
        cost_ms,
    )
    return response


# 把 searcher 从 app.state 注入到路由
# 每个请求进来时自动执行
@app.middleware("http")
async def inject_searcher(request: Request, call_next):
    request.state.searcher = getattr(request.app.state, "searcher", None)
    request.state.ready = getattr(request.app.state, "ready", False)
    request.state.chunk_count = getattr(request.app.state, "chunk_count", 0)
    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP错误: %s %s -> %s %s %s", request.method, request.url.path, exc.status_code, get_request_id(request), exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.status_code, "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("参数校验失败: %s %s -> %s %s", request.method, request.url.path, get_request_id(request), exc.errors())
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": {"code": 422, "message": "请求参数不合法", "details": exc.errors()}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常: %s %s -> %s", request.method, request.url.path, get_request_id(request))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": 500, "message": "服务内部错误，请稍后重试"}},
    )


@app.get("/health")
async def health_check():
    ready = bool(getattr(app.state, "ready", False)) and getattr(app.state, "searcher", None) is not None
    return {
        "status": "ok" if ready else "not_ready",
        "service": "PHP-Sage",
        "version": app.version,
        "ready": ready,
    }


@app.get("/metrics")
async def metrics():
    return {
        "status": "ok",
        "service": "PHP-Sage",
        "version": app.version,
        "ready": bool(getattr(app.state, "ready", False)),
        "chunk_count": getattr(app.state, "chunk_count", 0),
        "searcher_loaded": getattr(app.state, "searcher", None) is not None,
    }

# 注册路由
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
