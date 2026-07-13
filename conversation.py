from datetime import datetime
from typing import List, Optional, Dict, Any
from database import get_connection


def normalize_phone(phone: str) -> str:
    return phone.replace("+", "").replace(" ", "").replace("-", "")


def get_or_create_user(phone: str, default_model: str = "kimi-k2.5", default_thinking: bool = False) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE phone = ?", (normalize_phone(phone),))
    user = cursor.fetchone()

    if user is None:
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO users (phone, created_at, default_model, default_thinking) VALUES (?, ?, ?, ?)",
            (normalize_phone(phone), now, default_model, int(default_thinking))
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE phone = ?", (normalize_phone(phone),))
        user = cursor.fetchone()

    conn.close()
    return dict(user)


def create_conversation(user_id: int, model: str, thinking: bool, title: str = "שיחה חדשה", personality: str = "kimi") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("UPDATE conversations SET active = 0 WHERE user_id = ? AND personality = ?", (user_id, personality))

    cursor.execute(
        """
        INSERT INTO conversations (user_id, title, model, personality, thinking, active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, model, personality, int(thinking), 1, now, now)
    )
    conn.commit()

    conversation_id = cursor.lastrowid
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    conversation = cursor.fetchone()

    conn.close()
    return dict(conversation)


def get_active_conversation(user_id: int, model: str, thinking: bool, personality: str = "kimi") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM conversations WHERE user_id = ? AND active = 1 AND personality = ? LIMIT 1",
        (user_id, personality)
    )
    conversation = cursor.fetchone()

    if conversation is None:
        conn.close()
        return create_conversation(user_id, model, thinking, personality=personality)

    conn.close()
    return dict(conversation)


def list_conversations(user_id: int, personality: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    if personality:
        cursor.execute(
            """
            SELECT * FROM conversations
            WHERE user_id = ? AND personality = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, personality, limit)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
    conversations = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return conversations


def get_conversation_by_id(conversation_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    )
    conversation = cursor.fetchone()

    conn.close()
    return dict(conversation) if conversation else None


def switch_conversation(user_id: int, conversation_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    )
    conversation = cursor.fetchone()

    if conversation is None:
        conn.close()
        return None

    personality = conversation["personality"]
    cursor.execute("UPDATE conversations SET active = 0 WHERE user_id = ? AND personality = ?", (user_id, personality))
    cursor.execute(
        "UPDATE conversations SET active = 1, updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), conversation_id)
    )
    conn.commit()
    conn.close()

    return get_conversation_by_id(conversation_id, user_id)


def add_message(conversation_id: int, role: str, content: str, image_url: str = ""):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content, image_url, created_at) VALUES (?, ?, ?, ?, ?)",
        (conversation_id, role, content, image_url or None, now)
    )

    cursor.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id)
    )

    conn.commit()
    conn.close()


def get_messages(conversation_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (conversation_id, limit)
    )
    messages = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return list(reversed(messages))


def update_conversation_settings(conversation_id: int, model: Optional[str] = None, thinking: Optional[bool] = None):
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if model is not None:
        updates.append("model = ?")
        params.append(model)

    if thinking is not None:
        updates.append("thinking = ?")
        params.append(int(thinking))

    if not updates:
        conn.close()
        return

    params.append(conversation_id)
    query = f"UPDATE conversations SET {', '.join(updates)}, updated_at = ? WHERE id = ?"
    params.insert(-1, datetime.utcnow().isoformat())

    cursor.execute(query, params)
    conn.commit()
    conn.close()


def update_conversation_title(conversation_id: int, title: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
        (title, datetime.utcnow().isoformat(), conversation_id)
    )
    conn.commit()
    conn.close()
