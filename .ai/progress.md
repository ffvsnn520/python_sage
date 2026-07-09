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
- 从 Day7 开始增加“知识债记录”规则：当前阶段只学最小可用版本时，必须把未展开的主流进阶内容记录下来，并标注建议补学时机。
- 后续每个学习日都要区分当前必学和暂缓进阶，避免只完成基础功能后遗漏完整知识体系。

## Day7 学习计划：评估指标量化

### 当前阶段先学
- 评估集：固定测试问题 + 期望命中文档，用来让检索效果可重复验证。
- Hit@K：前 K 个检索结果里是否包含正确文档。
- MRR：正确文档排得越靠前，分数越高。
- 最小检索评估：先评估 searcher.search() 返回的 sources，不先评估 LLM 答案。

### Day7 最小评估集
- PHP 连接 MySQL 超时怎么排查？ → pdo-connection-timeout.md
- SQLSTATE HY000 2002 Connection timed out 是什么问题？ → pdo-connection-timeout.md
- Nginx 502 Bad Gateway 怎么解决？ → nginx-php-502.md
- PHP-FPM 没启动导致 502 怎么查？ → nginx-php-502.md
- PHP session 登录后突然失效怎么办？ → session-not-working.md
- 多台服务器 session 丢失怎么解决？ → session-not-working.md
- PHP 导出 Excel 内存溢出怎么办？ → memory-exhausted-export.md
- Allowed memory size exhausted 怎么处理？ → memory-exhausted-export.md
- MySQL 慢查询怎么优化？ → mysql-slow-query.md
- 接口查询超时，SQL 很慢怎么排查？ → mysql-slow-query.md

### Day7 暂缓进阶，后续补齐
- Recall@K / Precision@K：更完整地评估召回覆盖率和结果纯度。
- nDCG：适合多等级相关性的排序质量评估。
- Answer Correctness：评估最终答案是否正确。
- Faithfulness / Groundedness：评估答案是否忠于知识库上下文，是否幻觉。
- Context Relevance：评估召回内容是否真的和问题相关。
- LLM-as-a-Judge：用大模型辅助批量评价答案。
- RAGAS / DeepEval / LangSmith Evaluation / LlamaIndex Eval：成熟 RAG 评估框架。

### 建议补学时机
- Day11 冷启动 + 兜底策略：补 Context Relevance、无答案/低置信度场景评估。
- Day12 性能优化：补 Precision@K、nDCG，用指标比较 chunk、top_k、rerank threshold。
- Day14 监控 + 反馈闭环：补 Answer Correctness、Faithfulness、LLM-as-a-Judge、RAGAS/DeepEval 等框架。

### Day7 当前进度
- [x] 新增 scripts/test_day7_eval.py，复用现有 load_docs、load_existing_index、Searcher。
- [x] 构造 10 条最小检索评估集，每条包含 query 和 expected_source。
- [x] 实现 find_rank()：查找期望文档在 sources 中的排名，使用 1-based rank。
- [x] 实现 hit_at_k()：rank <= k 记为 1，否则记为 0。
- [x] 实现 reciprocal_rank()：命中第 n 名得 1/n，未命中得 0。
- [x] 跑通当前基准：cases=10，Hit@1=1.0000，Hit@3=1.0000，MRR=1.0000。
- [x] 已解释：sources 里可能出现同一文档多次，因为检索返回的是 chunk，不是文档；当前脚本按第一次出现的位置计算文档 rank。

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

## Day8 学习计划：Tool Call 链路

### 当前阶段先学
- Tool schema：工具名称、描述、参数、返回结构和风险等级。
- Tool registry：统一注册工具，并通过工具名查找执行。
- 参数校验：必填、类型、长度/范围、未知参数。
- 工具调用结果：统一返回 success、tool、error、data。
- API 调试入口：GET /tools 查看工具，POST /tools/call 手动调用工具。

### Day8 当前进度
- [x] 新增 app/tools/registry.py，实现 Tool、ToolRegistry、参数校验和统一执行结果。
- [x] 新增 app/tools/php_tools.py，注册 search_knowledge_base 和 get_service_status 两个只读工具。
- [x] 新增 GET /tools 和 POST /tools/call，用于查看 schema 和手动调用工具。
- [x] 新增 scripts/test_day8_tools.py，验证 schema、正常调用和参数校验失败。
- [x] 修复 Day7 评估集中 memory-exhausted-export.md 的 expected_source 笔误。
- [x] 已解释：Tool Call 的难点不只是函数调用，而是 schema、校验、权限、失败恢复和幂等性。

## Day9 学习计划：Agent 编排

### 当前阶段先学
- Planner：判断用户目标，决定下一步动作、选择工具、准备参数。
- Executor：执行 Planner 选中的工具调用，不负责思考。
- Observation：接收工具返回结果，作为 Agent 的中间观察数据。
- Reflection：判断工具结果是否足够、是否失败、是否需要继续。
- Stop condition：明确什么时候停止，避免无限循环或重复调用。

### Day9 当前进度
- [x] 新增 app/agent/orchestrator.py，实现最小 Agent 编排循环。
- [x] 新增 POST /agent/ask，用 Agent 路径处理问题。
- [x] Planner 当前为最小规则版：状态类问题走 get_service_status，普通 PHP 问题走 search_knowledge_base。
- [x] Executor 通过 ToolRegistry.execute() 调用 Day8 已注册工具。
- [x] Observation 记录工具统一返回结果 success/tool/error/data。
- [x] Reflection 判断工具是否成功、搜索结果是否为空、是否足够生成答案。
- [x] Stop condition 支持 out_of_scope、chitchat、tool_failed、no_search_results、enough_to_answer、max_steps_reached。
- [x] 新增 scripts/test_day9_agent.py，验证服务状态查询和知识库查询两条 Agent 路径。

### Day9 后续补学清单
- 更强的 Planner：不只靠规则判断，而是支持任务拆解、多步计划和 LLM Planner。
- 多步 Agent：一次任务可能调用多个工具，并基于前一步 observation 决定下一步。
- 失败恢复：工具失败后重试、换工具、降级或提示用户补充信息。
- 循环控制：记录已执行步骤，避免重复调用同一个工具或陷入无限循环。
- 权限控制：写操作、高风险操作需要用户确认、审计日志和最小权限。
- Agent 评估：补充任务完成率、工具调用成功率、失败恢复率、平均步数、成本和延迟。
- MCP：作为后续外部工具和系统的标准接入方式补学。
- Skills：作为后续复杂任务流程和可复用能力沉淀方式补学。

## Day10 学习计划：对话历史管理（持久化）

### 当前阶段先学
- 区分业务 memory 和 LangGraph checkpoint：memory 保存对话、摘要、画像、任务状态；checkpoint 保存 graph 执行现场快照。
- 当前 PHP-Sage 不使用 LangGraph checkpoint，先由业务侧自己实现 MySQL memory。
- MySQL 保存完整 conversation_messages，但 prompt 只读取最近 MAX_HISTORY 条，避免上下文过长。
- 对话历史写入顺序仍然是先读历史、生成回答、再写入 user 和 assistant。
- 删除 session 当前采用软删除 deleted_at，方便后续审计和误删恢复。

### Day10 当前进度
- [x] 新增 app/memory/store.py，抽象 MemoryStore，并实现 InMemoryMemoryStore 与 MySQLMemoryStore。
- [x] 新增 conversation_messages 表结构：session_id、role、content、created_at、deleted_at，并建立 session 查询索引。
- [x] router.py 去掉内存级 _sessions，改为调用 get_history、append_history、clear_history。
- [x] main.py 启动时初始化 memory store；MEMORY_BACKEND=mysql 时自动创建数据库和 conversation_messages 表。
- [x] requirements.txt 新增 pymysql。
- [x] 新增 scripts/test_day10_memory.py，验证最近 6 条历史、顺序和清除逻辑。

### Day10 核心理解
- MySQL conversation_messages 是业务事实来源，用于完整对话流水、后台展示、审计和后续摘要生成。
- session memory 是 prompt 里使用的短期上下文，当前只取最近 6 条消息。
- checkpoint 不是长期 memory 主库；它保存的是某个 thread 的 graph state 快照，用于中断恢复、human-in-the-loop、调试和 time travel。
- 不启用 checkpoint 时，memory 层需要业务侧自己实现；启用 checkpoint 后，业务长期 memory 仍然建议独立存 MySQL。

### MySQL 启用方式
```bash
export MEMORY_BACKEND=mysql
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=你的密码
export MYSQL_DATABASE=php_sage
/home/fanyl/www/case/agent/langgraph_agent/venv311/bin/python main.py
```

### Day10 后续补学清单
- conversation_summaries：按 session 生成压缩摘要，减少 prompt token。
- user_profiles：沉淀用户稳定偏好、技术栈和背景。
- task_states：记录跨轮任务进度，不和聊天流水混在一起。
- memory policy：什么内容写入、什么时候更新、如何纠错、如何删除。
- 如果后续引入 LangGraph checkpoint，再区分 MySQL 业务 memory 和 checkpoint 执行快照。

### Day10 后续补齐时机
- Day12 性能优化：补 conversation_summaries，用摘要压缩长历史，控制 prompt token 和延迟。
- Day14 监控 + 反馈闭环：补 request_id/turn_id、sources、trace、latency、feedback 字段，把一轮问答、检索来源、Agent 工具调用和用户反馈关联起来。
- Day14 之后或中级阶段：补 user_profiles、task_states 和 memory policy，区分长期用户画像、跨轮任务状态、错误记忆纠正和数据删除策略。
- 引入复杂 LangGraph Agent 时：再评估 checkpoint 存储方案，明确 MySQL 业务 memory 与 checkpoint 执行快照的边界。

## Day11 学习计划：冷启动 + 兜底策略

### 当前阶段先学
- 冷启动：知识库尚未初始化、searcher 不存在、服务刚启动但还不能稳定回答。
- 召回为空：检索没有拿到可用 chunks 时，不把空上下文交给 LLM 硬编答案。
- LLM 失败：模型超时或异常时返回受控提示，不让接口变成 500。
- Tool 失败：工具失败后停止当前轮，不盲目重复调用。
- Agent 兜底：Observation 失败或无结果时，由 Reflection 明确 stop reason，并给用户可解释的下一步建议。

### Day11 当前进度
- [x] 新增 app/core/fallback.py，集中管理 service_not_ready、no_retrieval、llm_unavailable、tool_failed 等兜底文案和 safe_answer()。
- [x] POST /ask 接入冷启动兜底：知识库未就绪时直接返回可控说明，不再抛 503 给普通问答用户。
- [x] POST /ask 接入召回为空兜底：searcher.search() 无结果时提示用户补充错误信息、日志关键字或组件名称，不调用 LLM 编造答案。
- [x] POST /ask 和闲聊路径接入 safe_answer()，LLM 调用失败时返回模型不可用提示。
- [x] GET /ask/stream 接入知识库未就绪、召回为空和流式 LLM 异常兜底，并在兜底响应后写入 session 历史。
- [x] Agent 编排接入统一兜底：工具失败、知识库未初始化、无检索结果、LLM 失败都会给出明确答案和 trace stop reason。
- [x] 新增 scripts/test_day11_fallback.py，验证冷启动、召回为空、LLM 失败三类核心降级路径。

### Day11 核心理解
- 兜底不是一句“出错了”，而是根据失败类型给出不同策略：未初始化提示稍后重试，召回为空提示补充信息，LLM 失败提示模型暂不可用，工具失败停止继续重试。
- 确定性错误不适合重试，例如参数错误、知识库未初始化、召回为空；临时错误才考虑重试，例如网络抖动或模型超时。
- RAG 无召回时不应该让 LLM 自由发挥，因为这会把“无资料”变成“看起来很像答案的幻觉”。
- Agent 的失败也要进入 trace：Planner/Executor/Observation/Reflection/Stop condition 需要能说明为什么停下。

### Day11 后续补学清单
- Context Relevance：不仅判断有没有 chunks，还要判断 chunk 是否真的能回答问题。
- 低置信度策略：结合 rerank score、来源数量、命中关键词设计更细的置信度分层。
- 重试与熔断：为 LLM、外部工具增加有限重试、超时、连续失败熔断。
- human-in-the-loop：高风险写操作、低置信度排障建议、生产变更建议需要人工确认。

### Day11 后续补齐时机
- Day12 性能优化：补超时、重试成本、缓存和 fallback 对延迟的影响。
- Day14 监控 + 反馈闭环：补 no_retrieval_rate、tool_failed_rate、llm_failed_rate、fallback_rate 等指标。
- 中级阶段：补置信度模型、人工接管策略和更完整的降级矩阵。

### Day11 当前掌握状态
- 当前目标不是独立设计完整线上兜底体系，而是能看懂每个关键环节为什么要有失败返回、为什么不能无召回时硬让 LLM 编答案。
- 未展开内容已经进入后续补齐安排，Day12/Day14 会按主线继续补，不需要今天一次吃完。

## Day14 后补强点：Python/MySQL 工程基础

### 暂不抢 Day11-Day14 主线
- 当前先继续完成性能优化、部署、监控反馈闭环。
- MySQL 连接、Python 常用包、连接池、ORM、迁移工具等不在 Day10 当天展开，避免打乱两周主线。

### 建议补强内容
- pymysql 基础：connect、cursor、execute、fetchall、insert/update/delete、参数化 SQL。
- 项目封装：config.py 管理数据库配置，db.py 或 store/repository 隔离数据库细节。
- 连接池：理解为什么生产环境不应该每次请求新建连接。
- SQLAlchemy 基础：了解 ORM/SQL 构造器在生产项目中的常见用法。
- alembic：了解数据库表结构迁移，不手工到处改表。
- FastAPI + DB：启动时初始化连接池，请求中读写数据库，异常处理和测试。

### 当前阶段够用标准
- 能解释 MemoryStore 为什么要存在。
- 能看懂 get_history、append_history、clear_history 的职责。
- 能知道 MySQL 连接参数从环境变量读取。
- 能读懂 conversation_messages 的基本 SQL。
- 暂时不要求独立写出连接池、异步 DB、ORM 和复杂事务。

## Day12 学习计划：性能优化

### 当前阶段先学
- 性能基线：使用固定问题记录检索耗时，避免凭感觉优化。
- 分段耗时：区分向量召回、BM25、rerank、Memory 和 LLM，定位真正瓶颈。
- 检索参数对比：比较候选数量与 rerank 数量对延迟、Hit@K、MRR 的影响。
- 低风险优化：优先减少不必要计算，同时保证检索质量不退化。
- LLM 超时意识：理解超时、有限重试、流式首 token 时间与总耗时的区别。

### Day12 当前进度
- [x] 读取当前问答、检索、LLM 和 Memory 实现，完成初步性能审计。
- [ ] 新增可重复运行的性能基线脚本。
- [ ] 为检索链路增加分段计时。
- [ ] 使用固定评估集记录优化前结果。
- [ ] 完成一项低风险优化并复测质量与耗时。

### 暂缓进阶
- conversation_summaries：长对话摘要与 token 预算管理。
- MySQL 连接池、异步数据库驱动与并发压测。
- 多级缓存、分布式缓存、缓存一致性和失效策略。
- Precision@K、nDCG 与更完整的参数实验报告。
- LLM 并发限制、熔断、自适应重试和成本治理。

### 建议补学时机
- Day14：结合 trace、latency、token usage 建立线上性能监控。
- Python/MySQL 工程补强阶段：实现连接池和数据库并发优化。
- RAG 深化阶段：补 Precision@K、nDCG 和完整检索参数实验。

## 中级路线图记录

- 已在 .ai/plan.md 中新增“中级路线图（Day14 之后）”，不改动当前 Day1-Day14 初级主线。
- 中级阶段定位：从能看懂和改造 demo，升级到能独立设计并实现一个小型生产化 AI Agent 服务。
- 中级学习方式：逐步改为学习者先写 30%-50%，再 review、修正、补工程边界。
- 中级阶段包含：Python/MySQL 工程补强、RAG 深化、Agent Loop 与 Planner、Tool Calling 工程化、Memory 体系、可靠性、评估回测、线上监控反馈、自动化工作流和简单多 Agent、微调和模型策略入门。
