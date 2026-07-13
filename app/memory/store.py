"""Conversation memory storage.

Day10 focuses on business memory, not LangGraph checkpointing:
- MySQL keeps the durable conversation history.
- The prompt only loads the latest MAX_HISTORY messages.
"""
from __future__ import annotations

import logging
from typing import Protocol

from app.core import config


logger = logging.getLogger("php_sage.memory")
MAX_HISTORY = 6


class MemoryStore(Protocol):
    def init_schema(self) -> None:
        ...

    def get_history(self, session_id: str, limit: int = MAX_HISTORY) -> list[dict]:
        ...

    def append_message(self, session_id: str, role: str, content: str) -> None:
        ...

    def clear_session(self, session_id: str) -> int:
        ...


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}

    def init_schema(self) -> None:
        return None

    def get_history(self, session_id: str, limit: int = MAX_HISTORY) -> list[dict]:
        return self._sessions.get(session_id, [])[-limit:]

    def append_message(self, session_id: str, role: str, content: str) -> None:
        self._sessions.setdefault(session_id, []).append({"role": role, "content": content})
        if len(self._sessions[session_id]) > MAX_HISTORY:
            self._sessions[session_id] = self._sessions[session_id][-MAX_HISTORY:]

    def clear_session(self, session_id: str) -> int:
        existed = session_id in self._sessions
        self._sessions.pop(session_id, None)
        return 1 if existed else 0


class MySQLMemoryStore:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        charset: str = "utf8mb4",
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset

    def _connect(self, *, with_database: bool = True):
        import pymysql

        kwargs = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "charset": self.charset,
            "autocommit": True,
            "cursorclass": pymysql.cursors.DictCursor,
        }
        if with_database:
            kwargs["database"] = self.database
        return pymysql.connect(**kwargs)

    def init_schema(self) -> None:
        with self._connect(with_database=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )

        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(64) NULL,
                        session_id VARCHAR(128) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        content TEXT NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        deleted_at DATETIME NULL,
                        INDEX idx_session_id_id (session_id, id),
                        INDEX idx_user_id_session_id (user_id, session_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )

    def get_history(self, session_id: str, limit: int = MAX_HISTORY) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT role, content
                    FROM conversation_messages
                    WHERE session_id = %s AND deleted_at IS NULL
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (session_id, limit),
                )
                rows = list(cursor.fetchall())

        rows.reverse()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    def append_message(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO conversation_messages (session_id, role, content)
                    VALUES (%s, %s, %s)
                    """,
                    (session_id, role, content),
                )

    def clear_session(self, session_id: str) -> int:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                affected = cursor.execute(
                    """
                    UPDATE conversation_messages
                    SET deleted_at = NOW()
                    WHERE session_id = %s AND deleted_at IS NULL
                    """,
                    (session_id,),
                )
        return affected


def build_memory_store() -> MemoryStore:
    backend = config.MEMORY_BACKEND.lower()
    if backend == "mysql":
        return MySQLMemoryStore(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset=config.MYSQL_CHARSET,
        )
    if backend == "memory":
        return InMemoryMemoryStore()
    raise ValueError(f"不支持的 MEMORY_BACKEND: {config.MEMORY_BACKEND}")


memory_store = build_memory_store()


def init_memory_store() -> None:
    memory_store.init_schema()
    logger.info("memory store initialized backend=%s", config.MEMORY_BACKEND)


def get_history(session_id: str) -> list[dict]:
    return memory_store.get_history(session_id, MAX_HISTORY)


def append_history(session_id: str, role: str, content: str) -> None:
    memory_store.append_message(session_id, role, content)


def clear_history(session_id: str) -> int:
    return memory_store.clear_session(session_id)
