from __future__ import annotations

import sqlite3

from backend.chat.schemas import ChatSession
from backend.storage.database import connect, initialize_database


CHAT_SESSION_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    context_id TEXT,
    ticket_id TEXT,
    created_by TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at
    ON chat_sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_context_id
    ON chat_sessions(context_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_ticket_id
    ON chat_sessions(ticket_id);
"""


def _initialize_chat_table() -> None:
    initialize_database()
    with connect() as connection:
        connection.executescript(CHAT_SESSION_SCHEMA_SQL)


def save_chat_session(session: ChatSession) -> ChatSession:
    _initialize_chat_table()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO chat_sessions (
                session_id,
                payload_json,
                context_id,
                ticket_id,
                created_by,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                payload_json = excluded.payload_json,
                context_id = excluded.context_id,
                ticket_id = excluded.ticket_id,
                created_by = excluded.created_by,
                title = excluded.title,
                updated_at = excluded.updated_at
            """,
            (
                session.session_id,
                session.model_dump_json(),
                session.context_id,
                session.ticket_id,
                session.created_by,
                session.title,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
            ),
        )
    return session


def load_chat_session(session_id: str) -> ChatSession | None:
    _initialize_chat_table()
    with connect() as connection:
        row = connection.execute(
            "SELECT payload_json FROM chat_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if row is None:
        return None
    return ChatSession.model_validate_json(row["payload_json"])


def list_chat_sessions(*, limit: int = 50) -> list[ChatSession]:
    _initialize_chat_table()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM chat_sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    sessions: list[ChatSession] = []
    for row in rows:
        try:
            sessions.append(ChatSession.model_validate_json(row["payload_json"]))
        except ValueError:
            continue
    return sessions
