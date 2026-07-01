"""
Day5 service checks.

Run after starting the API service:
  python scripts/test_day5.py
"""
import json
from urllib import error, request


BASE_URL = "http://127.0.0.1:8000"


def call(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def assert_status(name: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected}, got {actual}")
    print(f"[PASS] {name}: {actual}")


def main() -> None:
    status, data = call("GET", "/health")
    assert_status("health check", status, 200)
    assert data["ready"] is True
    assert data["status"] == "ok"

    status, data = call("POST", "/ask", {"query": "   "})
    assert_status("empty query", status, 400)
    assert data["success"] is False
    assert data["error"]["message"] == "query 不能为空"

    status, data = call("POST", "/ask", {})
    assert_status("validation error", status, 422)
    assert data["success"] is False
    assert data["error"]["message"] == "请求参数不合法"

    status, data = call("GET", "/session/day5/history")
    assert_status("session history", status, 200)
    assert data["session_id"] == "day5"
    assert isinstance(data["history"], list)

    print("Day5 service checks passed.")


if __name__ == "__main__":
    main()
