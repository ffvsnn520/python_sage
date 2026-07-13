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
| Day11 | 冷启动 + 兜底策略 | ✅ 已完成 |
| Day12 | 性能优化 | ✅ 已完成 |
| Day13 | 部署上线 | ✅ 已完成 |
| Day14 | 监控 + 反馈闭环 | 🔄 进行中 |

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

## 中级路线图（Day14 之后）

### 定位
- 初级两周计划目标：跑通一个可面试表达的垂直 RAG/Agent 服务闭环。
- 中级路线图目标：从“能看懂和改造 demo”升级到“能独立设计并实现一个小型生产化 AI Agent 服务”。
- 中级阶段开始后，学习方式要从“跟着实现”逐步变成“先自己写 30%-50%，再 review、修正、补工程边界”。

### 中级学习约束
- 中级阶段必须以学习者亲自编码为主，不能再由 AI 一次性自动写完整模块。
- 每个任务先给目标、接口约定、关键提示和验收标准，学习者先完成 30%-70% 代码量。
- AI 的职责转为全程引导、代码 review、指出 bug、补工程边界、解释取舍和给最小必要示例。
- 只有在卡住、需要示范复杂边界、或进入最终整理时，AI 才补充局部代码。
- 每个阶段必须保留足够多的手写代码量，并通过测试、复盘和重构巩固。

### 阶段0：Python/MySQL 工程补强（1-2 周）
- pymysql 基础：connect、cursor、execute、fetchall、insert/update/delete、参数化 SQL。
- 数据库工程：事务、连接池、配置管理、store/repository 分层。
- 生产常用工具：SQLAlchemy 基础、alembic 迁移、pytest、logging。
- 目标产出：能独立写 FastAPI + MySQL 小模块，能自己实现 get_history、append_message、clear_session。

### 阶段1：RAG 深化（1 周）
- chunk 策略、chunk size/overlap 对比。
- BM25 + 向量混合召回、rerank 参数调优、多路召回基础。
- query rewrite、无答案判断、Context Relevance。
- Precision@K、Recall@K、nDCG。
- 目标产出：召回实验脚本和参数对比报告，能判断失败来自召回还是生成。

### 阶段2：Agent Loop 与 Planner（1 周）
- Agent loop、Planner、Executor、Observation、Reflection、Stop condition。
- 多步任务规划、LLM Planner、规则 Planner 与 LLM Planner 取舍。
- 循环检测、最大步数控制、失败停止。
- 目标产出：多步 run_agent、trace 记录、max_steps 防死循环。

### 阶段3：Tool Calling 工程化（1 周）
- tool schema、参数校验、只读/写入/高风险工具分级。
- 幂等 key、超时、重试、失败降级、审计日志。
- human confirmation 高风险确认流程。
- 目标产出：工具调用日志表、高风险工具确认 demo、幂等调用 demo。

### 阶段4：Memory 体系（1 周）
- conversation_messages、conversation_summaries、user_profiles、task_states。
- memory policy：写入、召回、更新、纠错、删除。
- checkpoint 与 business memory 边界。
- 目标产出：summary/profile/task_state 表，从 MySQL 组装 Agent state。

### 阶段5：冷启动、降级和可靠性（3-5 天）
- 知识库未就绪、检索为空、低置信度、LLM 超时、Tool 失败。
- retry、fallback、熔断、人工介入、统一错误响应。
- 目标产出：统一 fallback 策略、低置信度判断、工具失败恢复。

### 阶段6：评估和多轮回测（1 周）
- RAG eval、Agent eval、任务完成率、工具调用成功率、失败恢复率。
- 平均步数、latency、token cost、LLM-as-judge。
- 多轮对话测试集、回归测试集。
- 目标产出：eval_cases、eval_runs、多轮回测脚本、prompt/model 变更对比。

### 阶段7：线上监控和反馈闭环（1 周）
- request_id、turn_id、trace、sources、latency、token usage。
- error rate、empty retrieval rate、user feedback、人工标注、失败归因。
- 目标产出：trace 表、feedback 表、失败样本收集和回流 eval dataset。

### 阶段8：自动化工作流和简单多 Agent（1 周）
- 任务拆解、工作流节点、条件分支、人工确认节点。
- planner + executor + reviewer。
- router agent、specialist agent、critic/reviewer agent。
- 目标产出：一个运维排查工作流，一个简单多 Agent 分工 demo。

### 阶段9：微调和模型策略（了解为主，3-5 天）
- RAG vs fine-tuning，什么时候需要微调。
- SFT/LoRA 概念、微调数据格式、评估和回滚。
- 模型选择、成本、延迟。
- 目标产出：能判断问题应该用 RAG、prompt、工具、记忆还是微调。

### 中级完成后的能力目标
- 能独立设计一个中小型垂直 Agent 服务。
- 能自己写核心模块，并解释每个模块为什么存在。
- 能做召回优化、Agent 编排、工具调用、记忆、评估、监控和基础工作流。
- 能在面试中讲清生产化 Agent 的系统设计、失败处理、评估优化和上线监控。
- 暂不定位为复杂多 Agent 平台架构师或模型训练专家。

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

## Day13 学习范围

### 当前必学
- 环境变量管理：API Key、数据库密码、模型配置不能硬编码进代码。
- 镜像构建：用 Dockerfile 固定 Python 依赖、工作目录和启动命令。
- 服务编排：用 docker-compose 启动 FastAPI 服务和 MySQL，并挂载 data/docs。
- 离线初始化：上线前先运行 scripts/ingest.py，生成 Qdrant 本地索引。
- 健康检查：用 /health 判断服务是否 ready，而不是只看进程是否启动。

### 暂缓进阶
- Nginx 反向代理、HTTPS、域名和证书续期。
- CI/CD 自动构建、测试、发布和回滚。
- 多副本、滚动发布、蓝绿发布和灰度发布。
- 云厂商 Secret Manager、镜像仓库和正式生产权限收敛。
- Qdrant Server 模式、独立向量数据库、备份和恢复。

### 建议补学时机
- Day14 监控 + 反馈闭环：补日志、trace、latency、错误率和用户反馈。
- 中级可靠性阶段：补 Nginx、HTTPS、熔断、重试、容量规划和发布策略。
- 中级数据库阶段：补 MySQL 连接池、迁移、备份恢复和权限收敛。
