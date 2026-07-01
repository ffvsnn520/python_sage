#!/usr/bin/env python3
"""
test_day4.py - Day4 多轮对话 + 意图识别 验证脚本
用法：先启动服务 python main.py，再运行 python scripts/test_day4.py
"""
import requests

BASE = "http://localhost:8000"


def ask(query: str, session_id: str = "test") -> dict:
    r = requests.post(f"{BASE}/ask", json={"query": query, "session_id": session_id})
    data = r.json()
    print(f"\n[Q] {query}")
    print(f"[Intent] {data.get('intent')}")
    print(f"[A] {data.get('answer', '')[:200]}")
    if data.get("sources"):
        print(f"[Sources] {data['sources']}")
    return data


def get_history(session_id: str):
    r = requests.get(f"{BASE}/session/{session_id}/history")
    data = r.json()
    print(f"\n[History for {session_id!r}] {len(data['history'])} 条")
    for item in data["history"]:
        print(f"  {item['role']}: {item['content'][:60]}...")
    return data


def clear_session(session_id: str):
    r = requests.delete(f"{BASE}/session/{session_id}")
    print(f"\n[Clear] {r.json()}")


def stream_ask(query: str, session_id: str = "test_stream"):
    print(f"\n[Stream Q] {query}")
    r = requests.get(f"{BASE}/ask/stream",
                     params={"query": query, "session_id": session_id},
                     stream=True)
    print("[Stream A] ", end="", flush=True)
    for line in r.iter_lines():
        if line:
            line = line.decode()
            if line.startswith("data: "):
                token = line[6:]
                if token == "[DONE]":
                    break
                print(token.replace("\\n", "\n"), end="", flush=True)
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Day4 测试：意图识别 + 多轮对话")
    print("=" * 60)

    print("\n── 测试1：意图识别三分类 ──")
    ask("PHP 连接 MySQL 超时怎么排查？", "s1")   # 期望：rag_query
    ask("你好！", "s1")                          # 期望：chitchat
    ask("你是谁？", "s1")                        # 期望：chitchat
    ask("今天天气怎么样？", "s1")                # 期望：out_of_scope
    ask("帮我写首诗", "s1")                      # 期望：out_of_scope

    print("\n── 测试2：多轮对话 ──")
    ask("PHP 内存溢出怎么处理？", "s2")
    ask("刚才说的第一步是什么？", "s2")          # 依赖上轮答案
    ask("如果是 PHP-FPM 配置导致的呢？", "s2")   # 追问

    print("\n── 测试3：查看 session 历史 ──")
    get_history("s2")

    print("\n── 测试4：session 隔离 ──")
    ask("刚才说的第一步是什么？", "s3")          # s3 无历史，应答不知道

    print("\n── 测试5：清除 session ──")
    clear_session("s2")
    get_history("s2")                            # 应该为空

    print("\n── 测试6：流式接口 ──")
    stream_ask("Nginx 502 错误怎么排查？", "s_stream")

    print("\n" + "=" * 60)
    print("Day4 测试完成")
    print("=" * 60)
