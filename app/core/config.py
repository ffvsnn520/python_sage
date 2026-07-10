import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

# 文档目录
DOCS_DIR = BASE_DIR / "docs"

# Qdrant 本地存储路径
QDRANT_PATH = str(BASE_DIR / "data" / "qdrant")
QDRANT_COLLECTION = "php_sage"

# 文档指纹文件，用来记录每个 md 文件上次摄入时的 hash
MANIFEST_PATH = BASE_DIR / "data" / "manifest.json"

# 复用 langgraph_agent 已下载的模型，避免重复下载
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
RERANKER_MODEL = "BAAI/bge-reranker-base"

# 切块参数
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 检索参数
RETRIEVAL_TOP_K = 5   # 向量+BM25 各取5个候选
RERANK_CANDIDATE_TOP_K = 4  # 只把合并后的前4个候选交给 reranker，降低精排耗时
RERANK_TOP_K = 3      # rerank后返回3个
RERANK_THRESHOLD = 0.1

# ── LLM 配置（部署时必须由环境变量或 .env 注入）──────────────
LLM_API_KEY  = os.getenv("API_KEY", "")
LLM_BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL    = os.getenv("MODEL", "qwen-plus")

# LLM 生成参数
LLM_MAX_TOKENS   = 1024
LLM_TEMPERATURE  = 0.3   # 偏低，让回答更严谨不乱编

# ── Day10 对话历史持久化配置 ───────────────────────────────
# 本地没有 MySQL 时可设为 memory；线上建议设为 mysql。
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "memory")

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "php_sage")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")
