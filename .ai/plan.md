# PHP-Sage 两周学习计划

## Week1

| Day | 主题 | 状态 |
|-----|------|------|
| Day1 | LangGraph + RAG 链路跑通 | ✅ 完成 |
| Day2 | 文档摄入 + 召回验证 | ✅ 完成 |
| Day3 | 接LLM，完整问答链路 | ✅ 完成 |
| Day4 | 多轮对话 + 意图识别 | ✅ 完成 |
| Day5 | FastAPI 服务化（错误处理/日志/健康检查） | ✅ 完成 |
| Day6 | 文档更新机制 + 增量摄入 | ✅ 完成 |
| Day7 | 评估指标量化（先学 Hit@K + MRR，记录进阶评估） | ✅ 完成 |

## Week2

| Day | 主题 | 状态 |
|-----|------|------|
| Day8  | Tool Call 链路 | 🔄 进行中 |
| Day9  | Agent 编排 | ✅ 已完成 |
| Day10 | 对话历史管理（升级为持久化） | ✅ 已完成 |
| Day11 | 冷启动 + 兜底策略 | 🔲 待开始 |
| Day12 | 性能优化 | 🔲 待开始 |
| Day13 | 部署上线 | 🔲 待开始 |
| Day14 | 监控 + 反馈闭环 | 🔲 待开始 |

## 目标节奏
- 两周内完成初级，具备独立交付垂直 RAG 服务的能力
- 之后 1-2 个月进入中级：Agent编排、评估体系、召回优化、生产化

## 学习记录规则
- 每天只学习当前阶段必要内容，但必须记录本主题未展开的进阶内容。
- 进阶内容不强行当天完成，按项目进度在合适阶段补齐。
- 后续每个 Day 的计划都要区分：当前必学、暂缓进阶、建议补学时机。
- 如果某个主题只实现最小版本，剩余能力要进入“待补充清单”，避免学完基础后遗忘。

## Day7 学习范围

### 当前必学
- 评估集：用固定问题 + 期望文档建立可重复测试样本。
- Hit@K：判断前 K 个检索结果里是否包含正确文档。
- MRR：判断正确文档是否排得足够靠前。
- 最小评估脚本：先评估 searcher.search() 的检索效果，不急着评估 LLM 最终回答。

### 暂缓进阶
- Recall@K / Precision@K：更细地衡量召回完整性和结果纯度。
- nDCG：考虑排序位置和相关性等级，适合多文档、多等级相关性评估。
- Answer Correctness：判断最终答案是否正确。
- Faithfulness / Groundedness：判断答案是否忠于检索上下文，是否幻觉。
- Context Relevance：判断召回上下文是否真的有助于回答问题。
- LLM-as-a-Judge：用大模型辅助评估答案质量。
- RAGAS / DeepEval / LangSmith Evaluation / LlamaIndex Eval：成熟评估框架。

### 建议补学时机
- Day11 冷启动 + 兜底策略：补 Context Relevance、无答案场景评估。
- Day12 性能优化：补 Precision@K、nDCG，用于比较 chunk/top_k/rerank 参数。
- Day14 监控 + 反馈闭环：补 Answer Correctness、Faithfulness、LLM-as-a-Judge 和评估框架。

## Day10 后续补齐安排

### 当前已完成
- 最小持久化 memory：conversation_messages 表 + 最近 MAX_HISTORY 条上下文召回。
- 业务 memory 与 LangGraph checkpoint 的概念边界。

### 暂缓进阶
- conversation_summaries：长历史压缩摘要。
- user_profiles：用户长期偏好、技术背景、常用技术栈。
- task_states：跨轮任务状态和中间结果。
- turn_id/request_id/sources/trace/feedback：把一轮问答、检索来源、工具调用、耗时和用户反馈关联起来。
- memory policy：写入、召回、更新、纠错、删除和保留周期。

### 建议补学时机
- Day12 性能优化：补 conversation_summaries 和 token 控制。
- Day14 监控 + 反馈闭环：补 trace、feedback、sources、latency 和 request_id/turn_id。
- Day14 之后或中级阶段：补 user_profiles、task_states、memory policy，以及复杂 Agent 下的 checkpoint 存储方案。

## Day14 后 Python/MySQL 补强点

### 暂缓原因
- 当前两周主线优先完成 RAG/Agent 服务闭环。
- Day10 只要求能读懂最小 MySQL memory 改造，不要求马上掌握完整数据库工程。

### 补强范围
- Python 常用包地图：fastapi、pydantic、uvicorn、pymysql、SQLAlchemy、alembic、httpx、pytest、logging。
- MySQL 基础连接：pymysql 连接、参数化 SQL、查询/插入/更新/软删除。
- 工程封装：配置管理、store/repository 分层、连接池、异常处理。
- 进阶方向：异步 DB、ORM、数据库迁移、事务和并发一致性。

## Day4 核心收获
- 意图识别两阶段：规则优先（0延迟）+ LLM兜底（处理模糊边界）
- 多轮对话：history 以 user/assistant 交替格式注入 messages，不塞进 system
- Session 存储：user 问题 + assistant 回复都存，先读后写，MAX_HISTORY=6 滑动窗口
- system prompt 每次请求重新注入，不需要存进 session

## Day5 核心收获
- FastAPI 服务化三件套：健康检查、结构化日志、统一错误响应
- lifespan 负责启动初始化，middleware 负责记录请求耗时，exception handler 负责兜住异常
- 业务错误用 HTTPException 明确返回，例如 400 空问题、503 知识库未就绪
- 参数错误统一返回 422，格式固定为 success=false + error，方便前端和调用方处理

## Day6 核心收获
- 文档更新机制分两层：manifest 判断哪些 md 变化，indexer 负责把变化写入 Qdrant
- 初始化和服务启动解耦：scripts/ingest.py 离线全量建库，main.py 启动时只加载已有 Qdrant
- 增量摄入流程：load_manifest → get_changed_docs → load_docs_by_paths → update_index → save_manifest
- Qdrant 删除旧 chunk 靠 metadata.source，不按文件 hash 删除；hash 只负责判断文档是否变化

## Day7 核心目标
- 先把 RAG 评估拆成两层：检索评估和生成评估。
- 当前阶段优先做检索评估，因为检索没命中正确资料时，LLM 很难稳定答对。
- 用 5 篇 PHP 故障文档构造最小评估集，每篇至少 2 个问题。
- 第一版指标只实现 Hit@K 和 MRR，进阶指标进入待补充清单。
