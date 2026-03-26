import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from config import settings
from models.models import ConversationMessage, ConversationSummary, VerificationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def _use_postgres() -> bool:
    url = (settings.database_url or "").strip()
    return bool(url) and url.startswith(("postgres://", "postgresql://"))


def _sql(template: str) -> str:
    """Swap SQLite '?' placeholders for PostgreSQL '%s' when needed."""
    return template.replace("?", "%s") if _use_postgres() else template


# ---------------------------------------------------------------------------
# SQLite path helper (only used when not on Postgres)
# ---------------------------------------------------------------------------

def _sqlite_path() -> str:
    path = (settings.sqlite_db_path or "").strip()
    if not path:
        path = os.path.join(settings.data_dir, "verimed.sqlite3")
    elif not os.path.isabs(path):
        normalized = os.path.normpath(path)
        path = normalized if os.path.dirname(normalized) else os.path.join(settings.data_dir, normalized)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Connection context manager
# ---------------------------------------------------------------------------

@contextmanager
def _db_conn():
    """Open a DB connection, commit on success, rollback + close on any error."""
    if _use_postgres():
        import psycopg2
        conn = psycopg2.connect(settings.database_url)
    else:
        conn = sqlite3.connect(_sqlite_path())
        conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Query helpers — return plain dicts so callers work the same for both DBs
# ---------------------------------------------------------------------------

def _execute(conn, sql: str, params=()) -> None:
    if _use_postgres():
        with conn.cursor() as cur:
            cur.execute(sql, params)
    else:
        conn.execute(sql, params)


def _fetchone(conn, sql: str, params=()) -> dict | None:
    if _use_postgres():
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
    else:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def _fetchall(conn, sql: str, params=()) -> list[dict]:
    if _use_postgres():
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    else:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    with _db_conn() as conn:
        _execute(conn, """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                verification_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        _execute(conn, """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
        """)
        _execute(conn, """
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_created
            ON conversation_messages(conversation_id, created_at)
        """)
    logger.info("Database initialised (backend: %s)", "postgres" if _use_postgres() else "sqlite")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_conversation(verification: VerificationResult) -> tuple[str, str, str]:
    conversation_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    with _db_conn() as conn:
        _execute(conn, _sql(
            "INSERT INTO conversations(id, request_id, verification_json, created_at) VALUES (?, ?, ?, ?)"
        ), (conversation_id, verification.request_id, verification.model_dump_json(), created_at))
    return conversation_id, verification.request_id, created_at


def get_conversation(conversation_id: str) -> dict | None:
    with _db_conn() as conn:
        return _fetchone(conn, _sql(
            "SELECT id, request_id, verification_json, created_at FROM conversations WHERE id = ?"
        ), (conversation_id,))


def load_verification(conversation_id: str) -> VerificationResult | None:
    row = get_conversation(conversation_id)
    if not row:
        return None
    try:
        return VerificationResult.model_validate(json.loads(row["verification_json"]))
    except Exception as exc:
        logger.error("Failed to parse verification snapshot for conversation %s: %s", conversation_id, exc)
        return None


def list_conversations(limit: int = 100) -> list[ConversationSummary]:
    with _db_conn() as conn:
        rows = _fetchall(conn, _sql(
            "SELECT id, request_id, verification_json, created_at FROM conversations ORDER BY created_at DESC LIMIT ?"
        ), (limit,))

    result: list[ConversationSummary] = []
    for row in rows:
        identified_product = None
        classification = "cannot_verify"
        risk_score = 0
        try:
            payload = json.loads(row["verification_json"])
            identified_product = payload.get("identified_product")
            classification = payload.get("classification", "cannot_verify")
            risk_score = int(payload.get("risk_score", 0))
        except Exception as exc:
            logger.warning("Could not parse conversation summary for %s: %s", row["id"], exc)
        result.append(ConversationSummary(
            conversation_id=row["id"],
            request_id=row["request_id"],
            created_at=row["created_at"],
            identified_product=identified_product,
            classification=classification,
            risk_score=risk_score,
        ))
    return result


def add_message(conversation_id: str, role: str, content: str) -> ConversationMessage:
    message = ConversationMessage(
        id=str(uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with _db_conn() as conn:
        _execute(conn, _sql(
            "INSERT INTO conversation_messages(id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)"
        ), (message.id, message.conversation_id, message.role, message.content, message.created_at))
    return message


def list_messages(conversation_id: str) -> list[ConversationMessage]:
    with _db_conn() as conn:
        rows = _fetchall(conn, _sql(
            "SELECT id, conversation_id, role, content, created_at FROM conversation_messages WHERE conversation_id = ? ORDER BY created_at ASC"
        ), (conversation_id,))
    return [
        ConversationMessage(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def clear_all_history() -> None:
    with _db_conn() as conn:
        _execute(conn, "DELETE FROM conversation_messages")
        _execute(conn, "DELETE FROM conversations")
    logger.info("All conversation history cleared.")
