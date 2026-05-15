"""
测试 utils/helpers.py — LLM 工厂、Agent 角色分配。
默认依赖环境变量，测试含容错分支。
"""
import os
import pytest
from utils.helpers import get_agent_llm, get_llm


class TestGetLlm:

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.setenv("TESTPROV_API_KEY", "")
        monkeypatch.setenv("TESTPROV_MODEL", "")
        with pytest.raises(ValueError, match="API_KEY"):
            get_llm("TESTPROV")

    def test_missing_model_raises(self, monkeypatch):
        monkeypatch.setenv("TESTPROV_API_KEY", "sk-fake")
        monkeypatch.setenv("TESTPROV_MODEL", "")
        with pytest.raises(ValueError, match="MODEL"):
            get_llm("TESTPROV")


class TestGetAgentLlm:

    def test_processor_default_provider(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        monkeypatch.setenv("DEEPSEEK_MODEL", "test-model")
        monkeypatch.delenv("PROCESSOR_PROVIDER", raising=False)

        llm = get_agent_llm("PROCESSOR")
        assert llm is not None
        assert llm.temperature == 0.0

    def test_copywriter_temperature(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        monkeypatch.setenv("DEEPSEEK_MODEL", "test-model")
        monkeypatch.delenv("COPYWRITER_PROVIDER", raising=False)

        llm = get_agent_llm("COPYWRITER")
        assert llm.temperature == 0.2
