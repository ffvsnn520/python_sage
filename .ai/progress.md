# PHP-Sage 项目进度

## 项目定位
独立 RAG 问答系统，针对 PHP 生产问题知识库。
复用 langgraph_agent 的 venv311 环境（模型已下载）。

## 项目路径
/home/fanyl/www/case/php-sage

## 技术栈
- Python 3.10 + venv311（路径：/home/fanyl/www/case/agent/langgraph_agent/venv311）
- Qdrant（本地文件模式，路径：data/qdrant/）
- Embedding：BAAI/bge-small-zh-v1.5（512维）
- Reranker：BAAI/bge-reranker-base（CrossEncoder）
- BM25：rank-bm25 + jieba 中文分词
- FastAPI + uvicorn
- LLM：阿里云 DashScope / qwen-plus（OpenAI 兼容接口）

## 项目结构
```
php-sage/
├── app/
│   ├── core/
│   │   ├── config.py        # 配置（路径、模型、chunk参数、LLM配置）
│   │   ├── llm.py           # LLM 封装（ask普通 / ask_stream流式）
│   │   ├── prompt.py        # Prompt 构建（RAG上下文拼装 + 多轮历史）
│   │   ├── intent.py        # 意图识别（规则+LLM两阶段）[Day4新增]
│   │   └── logging.py       # 日志配置 [Day5新增]
│   ├── ingestion/
│   │   ├── loader.py        # 读取 docs/ 下所有 .md 文件
│   │   └── indexer.py       # 切块 + 写入 Qdrant
│   ├── retrieval/
│   │   └── searcher.py      # 向量+BM25+Rerank 混合检索
│   └── api/
│       └── router.py        # POST /ask + GET /ask/stream + session管理接口
├── docs/                    # 5个PHP生产问题md文档
├── scripts/
│   ├── ingest.py            # 一键摄入脚本
│   ├── test_search.py       # 召回效果测试脚本
│   ├── test_day4.py         # Day4 多轮+意图测试脚本 [Day4新增]
│   └── test_day5.py         # Day5 服务化测试脚本 [Day5新增]
├── data/qdrant/             # Qdrant 本地存储
└── main.py                  # FastAPI 启动入口
```

## 当前配置（app/core/config.py）
- CHUNK_SIZE = 500
- CHUNK_OVERLAP = 50
- RETRIEVAL_TOP_K = 5
- RERANK_TOP_K = 3
- RERANK_THRESHOLD = 0.1
- LLM_MODEL = qwen-plus
- LLM_TEMPERATURE = 0.3
- LLM_MAX_TOKENS = 1024

## 已完成（Day1）
- [x] LangGraph + RAG 链路跑通

## 已完成（Day2）
- [x] 项目结构搭建
- [x] 5个docs文档摄入Qdrant
- [x] 召回效果验证（5个问题全部命中正确文档）
- [x] FastAPI POST /ask 接口（返回chunks）
- [x] 逐行打印理解了完整链路：loader→indexer→searcher→router

## 已完成（Day3）
- [x] config.py 增加 LLM 配置（复用 langgraph_agent 的阿里云 DashScope）
- [x] app/core/llm.py：ask()普通调用 + ask_stream()流式调用
- [x] app/core/prompt.py：build_messages() 构建RAG prompt
- [x] POST /ask 升级：chunk → prompt → LLM → 返回真实 answer + sources
- [x] GET /ask/stream：SSE流式接口，打字机效果，逐token推送
- [x] curl 端到端验证（普通接口 + SSE流式接口均通过）

## 已完成（Day4）
- [x] app/core/intent.py：意图识别，规则优先+LLM兜底两阶段
  - rag_query：PHP技术问题 → 走RAG链路
  - chitchat：闲聊 → 直接LLM友好回复
  - out_of_scope：越界话题 → 礼貌拒绝
- [x] prompt.py 升级：build_messages() 支持 history 参数（多轮历史注入）
- [x] prompt.py 新增：build_chitchat_messages()（闲聊专用prompt）
- [x] router.py 升级：
  - 修复 Day3 遗留 bug（return None, None）
  - 接入意图识别分流（三路分发）
  - 内存级 session store（MAX_HISTORY=6条）
  - POST /ask 支持 session_id + history 字段
  - GET /ask/stream 支持 session_id，流结束后写入历史
  - DELETE /session/{id}：清除session
  - GET /session/{id}/history：查看历史（调试用）
- [x] llm.py 清理调试print，保持干净
- [x] scripts/test_day4.py：6组测试验证意图分类和多轮对话

## 已完成（Day5）
- [x] app/core/logging.py：新增统一日志配置，输出时间、级别、模块名、消息
- [x] main.py：启动初始化日志从 print 升级为 logger.info
- [x] main.py：新增请求日志 middleware，记录 method、path、status_code、耗时
- [x] main.py：新增全局 HTTPException 处理，统一返回 success=false + error
- [x] main.py：新增 RequestValidationError 处理，参数错误统一返回 422
- [x] main.py：新增 Exception 兜底处理，未知异常返回 500 并记录堆栈
- [x] main.py：新增 GET /health 健康检查，返回服务名、版本、ready 状态
- [x] router.py：意图识别 print 改为 logger.info
- [x] router.py：RAG 链路增加知识库未就绪保护，返回 503
- [x] router.py：AskRequest.history 改为 Field(default_factory=list)
- [x] app/core/intent.py：清理误混入的邮箱文本，修复启动导入时报 NameError 的问题
- [x] scripts/test_day5.py：验证 /health、空 query 400、参数错误 422、session history

## Day4 核心概念理解
### 意图识别两阶段设计
```
query
  ↓
规则快速判断（0延迟，覆盖80%）
  ↓ 命中 → 直接返回
  ↓ 未命中
LLM分类（精准，处理模糊边界）
  ↓
intent: rag_query / chitchat / out_of_scope
```

### 多轮对话 messages 结构
```python
[
  {"role": "system",    "content": SYSTEM_PROMPT},
  {"role": "user",      "content": "上轮问题"},      # history[0]
  {"role": "assistant", "content": "上轮回答"},      # history[1]
  {"role": "user",      "content": "RAG上下文+当前问题"},  # 当前轮
]
```

### Session 管理要点
- 内存级 dict，key=session_id，value=最近MAX_HISTORY条消息
- 流式接口：generator 结束后才写入 session（避免写入时序问题）
- 每轮 RAG 重新检索（不复用上轮chunks），防上下文漂移

## Day5 核心概念理解
### FastAPI 服务化分层
```
请求进入
  ↓
middleware：记录请求耗时
  ↓
router：执行业务逻辑
  ↓
exception handler：把错误统一变成 JSON
  ↓
返回响应
```

### 错误类型
- 400：业务参数不合法，例如 query 为空
- 422：请求结构不合法，例如缺少 query 字段
- 503：服务暂时不可用，例如知识库尚未初始化完成
- 500：未知异常，服务端记录堆栈，对用户返回统一提示

### 健康检查
```bash
curl http://localhost:8000/health
```
返回 ready=true 表示知识库已经加载，服务可以接收问答请求。

## 后续学习方式
- 从 Day6 开始采用“半独立练习”节奏：先讲业务目标，再写 5-10 行核心代码，逐行解释 Python 语法和业务作用。
- 每遇到不熟的 Python 写法，都回答三个问题：这是 Python 自带的吗？输入输出是什么？当前代码里为什么要用？
- 优先补项目够用型 Python：字符串方法、列表、字典、Path 文件操作、函数、异常。
- 学习任务不追求一次独立写完整模块，先做到能读懂、能解释、能修改已有函数、能自己写 10-20 行小函数。
- Day6 建议让学习者亲自参与的小函数：calculate_file_hash(path)、load_manifest()、save_manifest(data)、is_doc_changed(path, manifest)。

## 启动方式
```bash
cd /home/fanyl/www/case/php-sage
/home/fanyl/www/case/agent/langgraph_agent/venv311/bin/python main.py
```

## 接口说明

### POST /ask（普通，多轮，含意图识别）
```bash
# 第一轮
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "PHP连接MySQL超时怎么排查？", "session_id": "user_001"}'

# 第二轮（服务端自动读取 user_001 的历史）
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "刚才说的第一步是什么？", "session_id": "user_001"}'
```

### GET /ask/stream（SSE流式，支持session）
```bash
curl -N --get http://localhost:8000/ask/stream \
  --data-urlencode "query=PHP内存溢出如何处理" \
  --data-urlencode "session_id=user_001"
```

### 会话管理
```bash
# 查看历史
curl http://localhost:8000/session/user_001/history

# 清除历史
curl -X DELETE http://localhost:8000/session/user_001
```

### 健康检查（Day5新增）
```bash
curl http://localhost:8000/health
```

### Day5 服务化测试
```bash
/home/fanyl/www/case/agent/langgraph_agent/venv311/bin/python scripts/test_day5.py
```

### Day6 增量摄入测试
```bash
# 检查 manifest 变化判断
/home/fanyl/www/case/agent/langgraph_agent/venv311/bin/python scripts/test_manifest.py

# 第一次初始化：全量写入 Qdrant，并保存 manifest
/home/fanyl/www/case/agent/langgraph_agent/venv311/bin/python scripts/ingest.py

# 后续更新：只处理变化过的 md 文件
/home/fanyl/www/case/agent/langgraph_agent/venv311/bin/python scripts/ingest_incremental.py
```

## Day6 核心概念理解
### 职责拆分
- app/ingestion/manifest.py：只负责文档指纹、manifest 读写、判断哪些文档变化
- app/ingestion/loader.py：只负责把 md 文件读取成 {"filename", "content"} 结构
- app/ingestion/indexer.py：只负责切块、连接 Qdrant、全量写入、增量更新、加载已有索引
- scripts/ingest.py：第一次初始化入口，会清空并重建 Qdrant，然后保存 manifest
- scripts/ingest_incremental.py：后续增量入口，只替换变化文档对应的 chunks
- main.py：服务启动入口，只加载已有 Qdrant，不再调用 build_index 重建

### 初始化和启动分离
```
第一次上线/重建
  ↓
scripts/ingest.py
  ↓
全量写 Qdrant + 保存 manifest

服务启动
  ↓
main.py
  ↓
load_existing_index()
  ↓
只加载已有 Qdrant + 为 BM25 切 docs 内存 chunks

文档更新
  ↓
scripts/ingest_incremental.py
  ↓
只删除并重写变化文档的 chunks + 更新 manifest
```

### 为什么 main.py 不再 build_index
- build_index 会删除整个 Qdrant collection，适合离线初始化，不适合服务每次启动
- 服务启动应该快、稳定、无副作用，所以只连接已有 Qdrant
- Searcher 仍然需要 all_chunks 给 BM25，因此 load_existing_index 会读取 docs 并切块，但不写入 Qdrant

### Qdrant 增量删除条件
```python
FieldCondition(
    key="metadata.source",
    match=MatchValue(value=filename),
)
```
含义：删除 payload 里 metadata.source 等于当前文件名的所有旧 chunks。

## RAG 完整链路（Day4 最终版）
```
用户问题 query + session_id
    ↓
intent.detect_intent()
  规则判断 → 命中直接分流
  LLM判断  → 模糊情况
    ↓
┌─────────────────┬──────────────────┬──────────────────┐
│  rag_query      │  chitchat        │  out_of_scope    │
│  召回chunks     │  直接LLM         │  固定拒绝回复    │
│  +session历史   │  +session历史    │                  │
│  → build_msg    │  → build_chitchat│                  │
│  → ask()/stream │  → ask()/stream  │                  │
└─────────────────┴──────────────────┴──────────────────┘
    ↓
更新 session 历史
    ↓
返回 {query, answer, sources, intent}
```
