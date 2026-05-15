"""
测试 core/state.py — AgentState 字段完整性。
"""
from core.state import AgentState


class TestAgentState:

    def test_valid_state_dict(self):
        state: AgentState = {
            "product_desc": "AI CRM tool for SMBs",
            "icp_definition": "SaaS companies with 50-200 employees",
            "target_url": "https://example.com",
            "language": "English",
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
        assert state["product_desc"] == "AI CRM tool for SMBs"
        assert state["lead_score"] == 0

    def test_partial_state(self):
        state: AgentState = {
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
            "mode": "MARKET_ANALYSIS",
            "log_messages": ["test log"],
            "error_message": None,
            "should_proceed": False,
        }
        assert state["mode"] == "MARKET_ANALYSIS"
        assert len(state["log_messages"]) == 1
