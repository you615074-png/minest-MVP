"""
测试 utils/auth.py — bcrypt 密码哈希、注册、登录、锁定逻辑。
"""
import time
import pytest
from utils.auth import hash_password, check_password, register_user, authenticate_user


class TestBcryptHashing:

    def test_hash_and_verify(self):
        pw = "SecureP@ss123"
        hashed = hash_password(pw)
        assert check_password(pw, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not check_password("wrong", hashed)

    def test_same_password_different_hash(self):
        """bcrypt 每次生成不同哈希（内置随机盐）"""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2

    def test_empty_password_hash_works(self):
        hashed = hash_password("")
        assert check_password("", hashed)


class TestRegisterUser:

    def test_successful_registration(self):
        success, msg, user = register_user("testuser", "password123")
        assert success
        assert user["username"] == "testuser"
        assert "id" in user

    def test_duplicate_username(self):
        register_user("dupuser", "pass123")
        success, msg, user = register_user("dupuser", "other456")
        assert not success
        assert "已存在" in msg

    def test_empty_username(self):
        success, msg, _ = register_user("", "pass123")
        assert not success

    def test_empty_password(self):
        success, msg, _ = register_user("user", "")
        assert not success

    def test_too_short_username(self):
        success, msg, _ = register_user("ab", "pass123")
        assert not success
        assert "至少3位" in msg

    def test_too_short_password(self):
        success, msg, _ = register_user("validuser", "12345")
        assert not success
        assert "至少6位" in msg


class TestAuthenticateUser:

    def test_login_success(self):
        register_user("loginuser", "correct123")
        success, msg, user = authenticate_user("loginuser", "correct123")
        assert success
        assert user["username"] == "loginuser"

    def test_login_wrong_password(self):
        register_user("badpw_user", "correct123")
        success, msg, _ = authenticate_user("badpw_user", "wrong456")
        assert not success

    def test_login_nonexistent_user(self):
        success, msg, _ = authenticate_user("nobody", "anything")
        assert not success


class TestAccountLockout:

    def test_lockout_after_5_failed_attempts(self):
        register_user("lockme", "realpass")
        for _ in range(5):
            authenticate_user("lockme", "wrongpass")
        success, msg, _ = authenticate_user("lockme", "realpass")
        assert not success
        assert "锁定" in msg

    def test_successful_login_resets_failed_count(self):
        register_user("resetme", "realpass")
        authenticate_user("resetme", "wrongpass")
        authenticate_user("resetme", "wrongpass")
        success, _, _ = authenticate_user("resetme", "realpass")
        assert success

        # 登录成功后应该再次可以正常登录
        success2, _, _ = authenticate_user("resetme", "realpass")
        assert success2
