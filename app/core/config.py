import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 文档目录
DOCS_DIR = BASE_DIR / "docs"

# Qdrant 本地存储路径
QDRANT_PATH = str(BASE_DIR / "data" / "qdrant")
QDRANT_COLLECTION = "php_sage"

# 复用 langgraph_agent 已下载的模型，避免重复下载
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
RERANKER_MODEL = "BAAI/bge-reranker-base"

# 切块参数
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 检索参数
RETRIEVAL_TOP_K = 5   # 向量+BM25 各取5个候选
RERANK_TOP_K = 3      # rerank后返回3个
RERANK_THRESHOLD = 0.1

# ── LLM 配置（复用 langgraph_agent 的阿里云 DashScope）──────────────
# 优先读环境变量，fallback 到 langgraph_agent/.env 的值
LLM_API_KEY  = os.getenv("API_KEY",   "sk-721a501372a344a395c26e0369c9c84c")
LLM_BASE_URL = os.getenv("BASE_URL",  "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL    = os.getenv("MODEL",     "qwen-plus")

# LLM 生成参数
LLM_MAX_TOKENS   = 1024
LLM_TEMPERATURE  = 0.3   # 偏低，让回答更严谨不乱编
