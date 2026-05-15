"""
测试公共配置与 fixtures。
"""
import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import utils.db as db_module


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    """每个测试使用临时数据库，自动清理"""
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr("utils.db.DB_PATH", tmp_path)

    from utils.db import init_db
    init_db()

    yield tmp_path

    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    try:
        os.unlink(tmp_path + "-wal")
    except OSError:
        pass
    try:
        os.unlink(tmp_path + "-shm")
    except OSError:
        pass
