"""Day10 memory store smoke test.

This test uses the default MEMORY_BACKEND=memory so it can run without MySQL.
When MEMORY_BACKEND=mysql is configured, the same router functions use MySQL.
"""
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.memory.store import append_history, clear_history, get_history


def main():
    session_id = "day10_test"
    clear_history(session_id)

    for i in range(1, 5):
        append_history(session_id, "user", f"问题{i}")
        append_history(session_id, "assistant", f"回答{i}")

    history = get_history(session_id)
    assert len(history) == 6
    assert history[0] == {"role": "user", "content": "问题2"}
    assert history[-1] == {"role": "assistant", "content": "回答4"}

    affected = clear_history(session_id)
    assert affected == 1
    assert get_history(session_id) == []

    print("Day10 memory store test passed")


if __name__ == "__main__":
    main()
