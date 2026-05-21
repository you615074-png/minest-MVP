import sqlite3
import json
import uuid
from contextlib import contextmanager
from datetime import datetime, date
from typing import List, Dict, Any

DB_PATH = "app_data.db"
MAX_HISTORY_PER_USER = 50


def _adapt_datetime(val: datetime) -> str:
    return val.isoformat()


def _adapt_date(val: date) -> str:
    return val.isoformat()


sqlite3.register_adapter(datetime, _adapt_datetime)
sqlite3.register_adapter(date, _adapt_date)


def _json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_configs (
                user_id TEXT PRIMARY KEY,
                smtp_host TEXT NOT NULL DEFAULT '',
                smtp_port INTEGER NOT NULL DEFAULT 465,
                smtp_user TEXT NOT NULL DEFAULT '',
                smtp_pass_encrypted TEXT NOT NULL DEFAULT '',
                smtp_pass_salt TEXT NOT NULL DEFAULT '',
                sender_name TEXT NOT NULL DEFAULT 'AI SDR',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()


def save_email_config(user_id: str, smtp_host: str, smtp_port: int,
                      smtp_user: str, pass_encrypted: str, pass_salt: str,
                      sender_name: str):
    if not user_id:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO email_configs
                (user_id, smtp_host, smtp_port, smtp_user, smtp_pass_encrypted, smtp_pass_salt, sender_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, smtp_host, smtp_port, smtp_user, pass_encrypted, pass_salt, sender_name))
        conn.commit()


def get_email_config(user_id: str) -> dict | None:
    if not user_id:
        return None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT smtp_host, smtp_port, smtp_user, smtp_pass_encrypted, smtp_pass_salt, sender_name "
            "FROM email_configs WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "smtp_host": row["smtp_host"],
            "smtp_port": row["smtp_port"],
            "smtp_user": row["smtp_user"],
            "smtp_pass_encrypted": row["smtp_pass_encrypted"],
            "smtp_pass_salt": row["smtp_pass_salt"],
            "sender_name": row["sender_name"],
        }


def delete_email_config(user_id: str) -> bool:
    if not user_id:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_configs WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def save_history(user_id: str, mode: str, product_desc: str, target_url: str, full_result: dict):
    if not user_id:
        return

    with get_connection() as conn:
        cursor = conn.cursor()

        record_id = str(uuid.uuid4())
        created_at = datetime.now()
        result_json_str = json.dumps(full_result, ensure_ascii=False, default=_json_serializer)

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
                "full_result": json.loads(row["full_result_json"]) if row["full_result_json"] else {},
            })
        return records


def search_user_history(user_id: str, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not user_id or not keyword:
        return []

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, created_at, mode, product_desc, target_url, full_result_json
            FROM history_logs
            WHERE user_id = ? AND (
                product_desc LIKE ? OR target_url LIKE ? OR full_result_json LIKE ?
            )
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))

        records = []
        for row in cursor.fetchall():
            records.append({
                "id": row["id"],
                "created_at": row["created_at"],
                "mode": row["mode"],
                "product_desc": row["product_desc"],
                "target_url": row["target_url"],
                "full_result": json.loads(row["full_result_json"]) if row["full_result_json"] else {},
            })
        return records


def delete_history(record_id: str, user_id: str) -> bool:
    if not record_id or not user_id:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM history_logs WHERE id = ? AND user_id = ?",
            (record_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
