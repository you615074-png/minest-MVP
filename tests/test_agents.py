"""
测试 5 个 Agent 节点的输入→输出转换完整性。
使用 mock LLM 避免实际 API 调用。
"""
import pytest
from unittest.mock import patch, MagicMock
from core.agents.researcher import researcher_node


class TestResearcherNode:

    def test_no_url_returns_error(self):
        state = {
            "product_desc": "test",
            "icp_definition": "",
            "target_url": "",
            "language": "简体中文",
            "company_raw_data": "",
            "company_profile": {},
            "lead_score": 0,
            "score_rationale": "",
            "key_hooks": [],
            "email_draft": {},
            "market_analysis": {},
            "mode": "",
            "log_messages": [],
            "error_message": None,
            "should_proceed": False,
        }
        result = researcher_node(state)
        assert result["error_message"] is not None
        assert "无法获取" in result["error_message"]

    @patch("core.agents.researcher.requests.get")
    def test_jina_fetch_appended_to_raw_data(self, mock_get, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "A" * 300
        mock_get.return_value = mock_resp

        state = {
            "product_desc": "test",
            "icp_definition": "",
            "target_url": "https://example.com",
            "language": "简体中文",
            "company_raw_data": "",
            "company_profile": {},
            "lead_score": 0,
            "score_rationale": "",
            "key_hooks": [],
            "email_draft": {},
            "market_analysis": {},
            "mode": "",
            "log_messages": [],
            "error_message": None,
            "should_proceed": False,
        }
        result = researcher_node(state)
        assert result["company_raw_data"] != ""
        assert "官网内容" in result["company_raw_data"]
        assert result["error_message"] is None

    @patch("core.agents.researcher.requests.get")
    def test_jina_empty_returns_error(self, mock_get, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "short"
        mock_get.return_value = mock_resp

        state = {
            "product_desc": "test",
            "icp_definition": "",
            "target_url": "https://example.com",
            "language": "简体中文",
            "company_raw_data": "",
            "company_profile": {},
            "lead_score": 0,
            "score_rationale": "",
            "key_hooks": [],
            "email_draft": {},
            "market_analysis": {},
            "mode": "",
            "log_messages": [],
            "error_message": None,
            "should_proceed": False,
        }
        result = researcher_node(state)
        assert result["error_message"] is not None
