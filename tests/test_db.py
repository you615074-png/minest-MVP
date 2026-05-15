"""
测试 utils/db.py — 数据库初始化、历史记录 CRUD、50条裁剪。
"""
import json
from utils.db import init_db, save_history, get_user_history, MAX_HISTORY_PER_USER


class TestDatabaseInit:

    def test_init_creates_tables(self):
        init_db()

    def test_init_idempotent(self):
        init_db()
        init_db()


class TestHistory:

    def test_save_and_retrieve(self):
        result = {"lead_score": 85, "company_profile": {"company_name": "TestCo"}}
        save_history("user1", "SDR", "test product", "https://test.com", result)

        records = get_user_history("user1")
        assert len(records) == 1
        assert records[0]["mode"] == "SDR"
        assert records[0]["full_result"]["lead_score"] == 85

    def test_empty_user(self):
        records = get_user_history("nonexistent")
        assert records == []

    def test_none_user(self):
        save_history("", "SDR", "x", "y", {})
        records = get_user_history("")
        assert records == []

    def test_multiple_records(self):
        for i in range(3):
            save_history("multi_user", "SDR", f"p{i}", f"url{i}", {"i": i})

        records = get_user_history("multi_user")
        assert len(records) == 3

    def test_order_desc(self):
        for i in range(5):
            save_history("order_user", "SDR", f"p{i}", f"url{i}", {"i": i})

        records = get_user_history("order_user")
        # 最新插入的应该排在前面
        assert records[0]["product_desc"] == "p4"

    def test_max_history_trim(self):
        total = MAX_HISTORY_PER_USER + 10
        for i in range(total):
            save_history("trim_user", "SDR", f"p{i}", f"url{i}", {"i": i})

        records = get_user_history("trim_user")
        assert len(records) == MAX_HISTORY_PER_USER
        # 最早的应该被裁剪掉了
        descriptions = {r["product_desc"] for r in records}
        assert "p0" not in descriptions
