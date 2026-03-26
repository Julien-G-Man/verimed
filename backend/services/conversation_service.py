import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from config import settings
from models.models import ConversationMessage, ConversationSummary, VerificationResult

logger = logging.getLogger(__name__)


def _db_path() -> str:
    path = (settings.sqlite_db_path or "").strip()

    if not path:
        path = os.path.join(settings.data_dir, "verimed.sqlite3")
    elif not os.path.isabs(path):
        normalized = os.path.normpath(path)
        if os.path.dirname(normalized):
            path = normalized
        else:
            path = os.path.join(settings.data_dir, normalized)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                verification_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_created
            ON conversation_messages(conversation_id, created_at)
            """
        )
        conn.commit()


def create_conversation(verification: VerificationResult) -> tuple[str, str, str]:
    conversation_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO conversations(id, request_id, verification_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, verification.request_id, verification.model_dump_json(), created_at),
        )
        conn.commit()

    return conversation_id, verification.request_id, created_at


def get_conversation(conversation_id: str) -> sqlite3.Row | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, request_id, verification_json, created_at FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
    return row


def load_verification(conversation_id: str) -> VerificationResult | None:
    row = get_conversation(conversation_id)
    if not row:
        return None
    try:
        payload = json.loads(row["verification_json"])
        return VerificationResult.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to parse verification snapshot for conversation %s: %s", conversation_id, exc)
        return None


def list_conversations(limit: int = 100) -> list[ConversationSummary]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT id, request_id, verification_json, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    conversations: list[ConversationSummary] = []
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

        conversations.append(
            ConversationSummary(
                conversation_id=row["id"],
                request_id=row["request_id"],
                created_at=row["created_at"],
                identified_product=identified_product,
                classification=classification,
                risk_score=risk_score,
            )
        )

    return conversations


def add_message(conversation_id: str, role: str, content: str) -> ConversationMessage:
    message = ConversationMessage(
        id=str(uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO conversation_messages(id, conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message.id, message.conversation_id, message.role, message.content, message.created_at),
        )
        conn.commit()

    return message


def list_messages(conversation_id: str) -> list[ConversationMessage]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ).fetchall()

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
    with _conn() as conn:
        conn.execute("DELETE FROM conversation_messages")
        conn.execute("DELETE FROM conversations")
        conn.commit()
