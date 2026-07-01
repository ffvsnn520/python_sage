"""
prompt.py - Prompt 构建模块（Day4 升级：支持多轮历史）
"""

SYSTEM_PROMPT = """你是一位专注于 PHP 生产环境问题的技术专家，擅长数据库连接、内存溢出、Session 异常、性能瓶颈等问题的排查和解决。

回答规则：
1. 只根据【参考资料】中的内容作答，不要凭空捏造。
2. 如果参考资料中没有相关信息，直接回答"根据现有知识库，暂无该问题的参考资料"。
3. 回答要结构清晰：先说原因，再给排查步骤，最后给解决方案。
4. 如果用户在追问上一轮的问题，结合历史对话理解用户意图。
5. 使用中文回答。
"""

CHITCHAT_SYSTEM = """你是 PHP-Sage，一个专注于 PHP 生产问题的技术助手。
用户在和你闲聊，请友好地回应，可以介绍自己的能力，但不要回答和 PHP 技术无关的实质性问题。
回答简洁，不超过 3 句话。
"""


def build_messages(
    query: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> list[dict]:
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"【资料{i}】（来源：{chunk['source']}）\n{chunk['content']}"
        )
    context_text = "\n\n".join(context_parts) if context_parts else "（未检索到相关资料）"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for item in history:
            messages.append({"role": item["role"], "content": item["content"]})

    user_content = f"以下是从知识库中检索到的参考资料：\n\n{context_text}\n\n---\n\n请根据以上参考资料，回答下面的问题：\n{query}"
    messages.append({"role": "user", "content": user_content})
    return messages


def build_chitchat_messages(
    query: str,
    history: list[dict] | None = None,
) -> list[dict]:
    messages = [{"role": "system", "content": CHITCHAT_SYSTEM}]
    if history:
        for item in history:
            messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": query})
    return messages
