"""
prompt.py - Prompt 构建模块

Day4 升级：支持多轮对话历史（history 参数）
  - build_messages()：RAG 问答 prompt，注入 history + chunks
  - build_chitchat_messages()：闲聊 prompt，注入 history

Prompt 设计原则（Day3 总结，Day4 扩展）：
  1. Role（角色）      → 锚定回答风格和专业领域
  2. Task（任务）      → 明确要做什么，减少 LLM 乱发挥
  3. Context（上下文） → 把检索到的知识塞进来，RAG 核心
  4. Guard（约束）     → 没找到时说不知道，防幻觉
  5. History（历史）   → 多轮对话，放在 user/assistant 交替消息里
  6. Query（问题）     → 放最后，注意力权重更高

多轮对话设计要点（Day4 新学）：
  - history 以 [user, assistant, user, assistant, ...] 交替方式注入 messages
  - 不用把 history 全塞进 system，OpenAI 格式原生支持多轮
  - 控制 history 长度（MAX_HISTORY），避免 context 超限
  - 每轮 RAG 都重新检索，不依赖上轮的 chunks（上下文漂移问题）
"""


SYSTEM_PROMPT = """\
你是一位专注于 PHP 生产环境问题的技术专家，擅长数据库连接、内存溢出、Session 异常、性能瓶颈等问题的排查和解决。

回答规则：
1. 只根据【参考资料】中的内容作答，不要凭空捏造。
2. 如果参考资料中没有相关信息，直接回答"根据现有知识库，暂无该问题的参考资料"。
3. 回答要结构清晰：先说原因，再给排查步骤，最后给解决方案。
4. 如果用户在追问上一轮的问题，结合历史对话理解用户意图。
5. 使用中文回答。
"""

CHITCHAT_SYSTEM = """\
你是 PHP-Sage，一个专注于 PHP 生产问题的技术助手。
用户在和你闲聊，请友好地回应，可以介绍自己的能力，但不要回答和 PHP 技术无关的实质性问题。
回答简洁，不超过 3 句话。
"""


def build_messages(
    query: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> list[dict]:
    """
    构建 RAG 问答的 messages。

    参数:
        query:   用户当前问题
        chunks:  searcher 返回的召回 chunk 列表
                 每项：{"content": str, "source": str, "score": float}
        history: 历史对话列表，每项 {"role": "user"/"assistant", "content": str}
    """
    # 把 chunks 拼成带编号的上下文段落
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"【资料{i}】（来源：{chunk['source']}）\n{chunk['content']}"
        )
    context_text = "\n\n".join(context_parts) if context_parts else "（未检索到相关资料）"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 注入历史对话（多轮核心）
    # OpenAI messages 格式天然支持多轮，直接追加 user/assistant 交替消息
    if history:
        for item in history:
            messages.append({"role": item["role"], "content": item["content"]})

    # 当前问题：上下文 + query
    user_content = f"""\
以下是从知识库中检索到的参考资料：

{context_text}

---

请根据以上参考资料，回答下面的问题：
{query}
"""
    messages.append({"role": "user", "content": user_content})
    return messages


def build_chitchat_messages(
    query: str,
    history: list[dict] | None = None,
) -> list[dict]:
    """
    构建闲聊的 messages（不注入 RAG chunks）。
    """
    messages = [{"role": "system", "content": CHITCHAT_SYSTEM}]

    if history:
        for item in history:
            messages.append({"role": item["role"], "content": item["content"]})

    messages.append({"role": "user", "content": query})
    return messages
