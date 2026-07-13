import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", "conversations.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            default_model TEXT DEFAULT 'kimi-k2.5',
            default_thinking INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT DEFAULT 'שיחה חדשה',
            model TEXT DEFAULT 'kimi-k2.5',
            personality TEXT DEFAULT 'kimi',
            thinking INTEGER DEFAULT 0,
            active INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT DEFAULT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # Migration: add columns if they don't exist (SQLite limited ALTER TABLE)
    try:
        cursor.execute("ALTER TABLE conversations ADD COLUMN personality TEXT DEFAULT 'kimi'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN image_url TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
