"""
intent.py - 意图识别
规则优先 + LLM 兜底两阶段
  rag_query    -> PHP 生产技术问题
  chitchat     -> 闲聊
  out_of_scope -> 完全无关话题
"""
import re
from app.core.llm import ask

_PHP_KEYWORDS = [
    "php", "mysql", "pdo", "nginx", "session", "内存", "超时", "502",
    "500", "错误", "报错", "异常", "连接", "慢查询", "索引", "缓存",
    "redis", "opcache", "fpm", "php-fpm", "curl", "composer", "laravel",
    "symfony", "thinkphp", "yii", "sql", "数据库", "配置", "日志",
    "排查", "优化", "性能", "内存溢出", "oom", "死锁", "连接池",
    "connection", "timeout", "error", "exception", "warning", "fatal",
]

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

_OOS_KEYWORDS = [
    "股票", "基金", "天气", "彩票", "星座", "算命", "食谱", "菜谱",
    "写诗", "写首诗", "写歌", "小说", "电影", "音乐", "体育", "足球", "篮球",
    "政治", "新闻", "地图", "导航", "翻译成英文", "翻译成日文",
]

def _rule_detect(query: str) -> str | None:
    q = query.strip().lower()
    has_php = any(kw in q for kw in _PHP_KEYWORDS)
    if not has_php:
        if any(kw in q for kw in _OOS_KEYWORDS):
            return "out_of_scope"
    if len(q) <= 20:
        for pat in _CHITCHAT_PATTERNS:
            if re.match(pat, q):
                return "chitchat"
    if has_php:
        return "rag_query"
    return None


_INTENT_SYSTEM = """你是一个意图分类器，只需输出一个单词，不要解释。
分类规则：
- rag_query：用户在问 PHP/MySQL/Nginx/Redis/Session/性能/部署相关的技术问题
- chitchat：用户在闲聊，比如打招呼、问你是谁、表达感谢
- out_of_scope：与 PHP 技术完全无关的话题
只输出以下三个词之一：rag_query / chitchat / out_of_scope
"""


async def detect_intent(query: str) -> str:
    result = _rule_detect(query)
    if result:
        return result
    messages = [
        {"role": "system", "content": _INTENT_SYSTEM},
        {"role": "user",   "content": query},
    ]
    raw = await ask(messages)
    raw = raw.strip().lower()
    for intent in ("rag_query", "chitchat", "out_of_scope"):
        if intent in raw:
            return intent
    return "rag_query"
