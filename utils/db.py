import sqlite3
import json
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any

DB_PATH = "app_data.db"

MAX_HISTORY_PER_USER = 50


@contextmanager
def get_connection():
    """Streamlit 兼容的 SQLite 连接管理器，启用 WAL 模式"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                created_at TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            )
        ''')

        try:
            cursor.execute("SELECT failed_attempts FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP,
                mode TEXT,
                product_desc TEXT,
                target_url TEXT,
                full_result_json TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()


def save_history(user_id: str, mode: str, product_desc: str, target_url: str, full_result: dict):
    """保存历史记录，超过上限则裁剪最早记录"""
    if not user_id:
        return

    with get_connection() as conn:
        cursor = conn.cursor()

        record_id = str(uuid.uuid4())
        created_at = datetime.now()
        result_json_str = json.dumps(full_result, ensure_ascii=False)

        cursor.execute('''
            INSERT INTO history_logs (id, user_id, created_at, mode, product_desc, target_url, full_result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (record_id, user_id, created_at, mode, product_desc, target_url, result_json_str))

        cursor.execute('SELECT COUNT(*) FROM history_logs WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]

        if count > MAX_HISTORY_PER_USER:
            cursor.execute('''
                DELETE FROM history_logs 
                WHERE id IN (
                    SELECT id FROM history_logs 
                    WHERE user_id = ?
                    ORDER BY created_at ASC 
                    LIMIT ?
                )
            ''', (user_id, count - MAX_HISTORY_PER_USER))

        conn.commit()


def get_user_history(user_id: str) -> List[Dict[str, Any]]:
    """按时间倒序获取用户历史记录"""
    if not user_id:
        return []

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, created_at, mode, product_desc, target_url, full_result_json
            FROM history_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        records = []
        for row in cursor.fetchall():
            records.append({
                "id": row["id"],
                "created_at": row["created_at"],
                "mode": row["mode"],
                "product_desc": row["product_desc"],
                "target_url": row["target_url"],
                "full_result": json.loads(row["full_result_json"]) if row["full_result_json"] else {}
            })

        return records
