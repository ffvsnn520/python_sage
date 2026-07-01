# PHP-Sage 两周学习计划

## Week1

| Day | 主题 | 状态 |
|-----|------|------|
| Day1 | LangGraph + RAG 链路跑通 | ✅ 完成 |
| Day2 | 文档摄入 + 召回验证 | ✅ 完成 |
| Day3 | 接LLM，完整问答链路 | ✅ 完成 |
| Day4 | 多轮对话 + 意图识别 | ✅ 完成 |
| Day5 | FastAPI 服务化（错误处理/日志/健康检查） | ✅ 完成 |
| Day6 | 文档更新机制 + 增量摄入 | 🔲 待开始 |
| Day7 | 评估指标量化 | 🔲 待开始 |

## Week2

| Day | 主题 | 状态 |
|-----|------|------|
| Day8  | Tool Call 链路 | 🔲 待开始 |
| Day9  | Agent 编排 | 🔲 待开始 |
| Day10 | 对话历史管理（升级为持久化） | 🔲 待开始 |
| Day11 | 冷启动 + 兜底策略 | 🔲 待开始 |
| Day12 | 性能优化 | 🔲 待开始 |
| Day13 | 部署上线 | 🔲 待开始 |
| Day14 | 监控 + 反馈闭环 | 🔲 待开始 |

## 目标节奏
- 两周内完成初级，具备独立交付垂直 RAG 服务的能力
- 之后 1-2 个月进入中级：Agent编排、评估体系、召回优化、生产化

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
