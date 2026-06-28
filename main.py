"""
main.py - FastAPI 启动入口

启动命令：
  python main.py
  或
  uvicorn main:app --reload --port 8000
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.ingestion.loader import load_docs
from app.ingestion.indexer import build_index
from app.retrieval.searcher import Searcher
from app.api.router import router


# lifespan：应用启动时初始化，关闭时清理
# 替代旧版的 @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("正在初始化知识库...")
    docs = load_docs()
    vectorstore, chunks = build_index(docs)
    searcher = Searcher(vectorstore, chunks)

    # 把 searcher 挂到 app.state，路由里可以取到
    app.state.searcher = searcher
    print("知识库初始化完成，服务就绪")

    yield  # 服务运行中

    # 关闭时执行（清理资源）
    print("服务关闭")


app = FastAPI(
    title="PHP-Sage",
    description="PHP生产问题知识库问答服务",
    version="0.1.0",
    lifespan=lifespan,
)


# 把 searcher 从 app.state 注入到路由
# 每个请求进来时自动执行
@app.middleware("http")
async def inject_searcher(request: Request, call_next):
    request.state.searcher = request.app.state.searcher
    return await call_next(request)


# 注册路由
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
