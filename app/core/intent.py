"""
intent.py - 意图识别

把用户输入分为三类：
  rag_query    → PHP 生产技术问题，走 RAG 链路
  chitchat     → 闲聊（你好、谢谢、介绍自己等），直接 LLM 回复
  out_of_scope → 完全无关话题（股票、天气、写诗等），礼貌拒绝

实现策略：
  先用规则快速过滤（低延迟，省 token），命中则直接返回；
  规则未命中的模糊情况再调 LLM 判断（更准确）。

为什么先规则后 LLM：
  - 规则覆盖 80% 常见情况，0 延迟 0 成本
  - LLM 兜底处理模糊边界，避免规则漏判
"""
import re
from app.core.llm import ask

# ── 规则库 ────────────────────────────────────────────────────────────

# PHP 技术关键词 → rag_query
_PHP_KEYWORDS = [
    "php", "mysql", "pdo", "nginx", "session", "内存", "超时", "502",
    "500", "错误", "报错", "异常", "连接", "慢查询", "索引", "缓存",
    "redis", "opcache", "fpm", "php-fpm", "curl", "composer", "laravel",
    "symfony", "thinkphp", "yii", "sql", "数据库", "配置", "日志",
    "排查", "优化", "性能", "内存溢出", "oom", "死锁", "连接池",
    "connection", "timeout", "error", "exception", "warning", "fatal",
]

# 闲聊关键词 → chitchat（需全词匹配，避免误杀）
_CHITCHAT_PATTERNS = [
    r"^(你好|hi|hello|嗨|哈喽)[\s!！。]*$",
    r"^谢谢(你|您)?[\s!！。]*$",
    r"^(thanks|thank you)[\s!！.]*$",
    r"^你是(谁|什么|哪个)?[\s？?。]*$",
    r"^介绍.*(自己|一下)[\s。？?]*$",
    r"^你叫什么[\s？?名字。]*$",
    r"^(好的|ok|好|明白|了解|收到)[\s!！。]*$",
    r"^再见[\s!！。]*$",
]

# 明确越界词 → out_of_scope
_OOS_KEYWORDS = [
    "股票", "基金", "天气", "彩票", "星座", "算命", "食谱", "菜谱",
    "写诗", "写首诗", "写歌", "小说", "电影", "音乐", "体育", "足球", "篮球",
    "政治", "新闻", "地图", "导航", "翻译成英文", "翻译成日文",
]


def _rule_detect(query: str) -> str | None:
    """
    规则快速判断，返回意图字符串或 None（表示规则未命中，需 LLM）
    """
    q = query.strip().lower()

    # 越界关键词优先（避免"写个 PHP 写诗的脚本"被误杀）
    # 只有 query 里没有 PHP 技术词，才判越界
    has_php = any(kw in q for kw in _PHP_KEYWORDS)
    if not has_php:
        if any(kw in q for kw in _OOS_KEYWORDS):
            return "out_of_scope"

    # 闲聊模式匹配（短句，精确匹配）
    if len(q) <= 20:
        for pat in _CHITCHAT_PATTERNS:
            if re.match(pat, q):
                return "chitchat"

    # 明确含 PHP 技术词 → rag_query
    if has_php:
        return "rag_query"

    # 规则未命中
    return None


_INTENT_SYSTEM = """\
你是一个意图分类器，只需输出一个单词，不要解释。

分类规则：
- rag_query：用户在问 PHP/MySQL/Nginx/Redis/Session/性能/部署相关的技术问题
- chitchat：用户在闲聊，比如打招呼、问你是谁、表达感谢
- out_of_scope：与 PHP 技术完全无关的话题

只输出以下三个词之一：rag_query / chitchat / out_of_scope
"""


async def detect_intent(query: str) -> str:
    """
    意图识别主函数
    先用规则，命中则直接返回；否则调 LLM 判断
    """
    # 第一步：规则
    result = _rule_detect(query)
    if result:
        return result

    # 第二步：LLM 兜底（规则未命中的模糊情况）
    messages = [
        {"role": "system", "content": _INTENT_SYSTEM},
        {"role": "user",   "content": query},
    ]
    raw = await ask(messages)
    raw = raw.strip().lower()

    # 防止 LLM 多输出文字，只取第一个词
    for intent in ("rag_query", "chitchat", "out_of_scope"):
        if intent in raw:
            return intent

    # LLM 也没给出有效答案，兜底 rag_query（宁可进 RAG 也别拒绝用户）
    return "rag_query"
