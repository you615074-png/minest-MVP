import uuid
from datetime import datetime, timedelta
from utils.db import DB_PATH, get_connection

try:
    import bcrypt as _bcrypt
    BCRYPT_ROUNDS = 12
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

_BCRYPT_PREFIX = b"$2b$"


def hash_password(password: str) -> str:
    if not HAS_BCRYPT:
        raise RuntimeError("bcrypt 未安装，请运行 pip install 'bcrypt>=4.0.0,<5.0.0'")
    return _bcrypt.hashpw(
        password.encode("utf-8"), _bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    ).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    if not HAS_BCRYPT:
        raise RuntimeError("bcrypt 未安装")

    try:
        return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
    except Exception:
        try:
            h = hashed.encode("utf-8")
            if h.startswith(_BCRYPT_PREFIX):
                return _bcrypt.checkpw(password.encode("utf-8"), h)
        except Exception:
            pass
        return False


def register_user(username: str, password: str) -> tuple[bool, str, dict]:
    if not username or not password:
        return False, "用户名和密码不能为空", {}

    if len(username) < 3 or len(password) < 6:
        return False, "用户名至少3位，密码至少6位", {}

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, "用户名已存在，请直接登录", {}

        user_id = str(uuid.uuid4())
        pw_hash = hash_password(password)

        try:
            cursor.execute(
                "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, username, pw_hash, datetime.now())
            )
            conn.commit()
            return True, "注册成功", {"id": user_id, "username": username}
        except Exception:
            return False, "注册失败，请稍后重试", {}


def authenticate_user(username: str, password: str) -> tuple[bool, str, dict]:
    if not username or not password:
        return False, "用户名和密码不能为空", {}

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, password_hash, failed_attempts, locked_until FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            return False, "用户名或密码错误", {}

        user_id = row["id"]
        db_user = row["username"]
        db_hash = row["password_hash"]
        failed_attempts = row["failed_attempts"]
        locked_until_str = row["locked_until"]

        if locked_until_str:
            try:
                locked_until = datetime.fromisoformat(locked_until_str)
                if datetime.now() < locked_until:
                    wait_mins = int((locked_until - datetime.now()).total_seconds() / 60) + 1
                    return False, f"账户已锁定，请在 {wait_mins} 分钟后再试", {}
            except (ValueError, TypeError):
                pass

        if check_password(password, db_hash):
            cursor.execute(
                "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            return True, "登录成功", {"id": user_id, "username": db_user}
        else:
            failed_attempts = (failed_attempts or 0) + 1
            if failed_attempts >= 5:
                lock_time = (datetime.now() + timedelta(minutes=15)).isoformat()
                cursor.execute(
                    "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                    (failed_attempts, lock_time, user_id)
                )
                msg = "密码错误次数过多，账户已被锁定 15 分钟"
            else:
                cursor.execute(
                    "UPDATE users SET failed_attempts = ? WHERE id = ?",
                    (failed_attempts, user_id)
                )
                msg = f"用户名或密码错误，还有 {5 - failed_attempts} 次尝试机会"

            conn.commit()
            return False, msg, {}


def change_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    if not user_id or not old_password or not new_password:
        return False, "所有字段均为必填"
    if len(new_password) < 6:
        return False, "新密码至少6位"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "用户不存在"

        if not check_password(old_password, row["password_hash"]):
            return False, "旧密码错误"

        new_hash = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()
        return True, "密码修改成功"
