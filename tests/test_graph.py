"""
测试 LangGraph 条件路由逻辑。
"""
import pytest
from core.graph import route_start, route_by_score
from core import AgentRole, RouteTarget, Mode


class TestRouteStart:

    def test_empty_url_goes_to_market_analyzer(self):
        state = {"target_url": "", "product_desc": "x", "icp_definition": "",
                 "language": "zh", "company_raw_data": "", "company_profile": {},
                 "lead_score": 0, "score_rationale": "", "key_hooks": [],
                 "email_draft": {}, "market_analysis": {}, "mode": "",
                 "log_messages": [], "error_message": None, "should_proceed": False}
        assert route_start(state) == AgentRole.MARKET_ANALYZER

    def test_whitespace_url_goes_to_market_analyzer(self):
        state = {"target_url": "   ", "product_desc": "x", "icp_definition": "",
                 "language": "zh", "company_raw_data": "", "company_profile": {},
                 "lead_score": 0, "score_rationale": "", "key_hooks": [],
                 "email_draft": {}, "market_analysis": {}, "mode": "",
                 "log_messages": [], "error_message": None, "should_proceed": False}
        assert route_start(state) == AgentRole.MARKET_ANALYZER

    def test_url_goes_to_researcher(self):
        state = {"target_url": "https://example.com", "product_desc": "x",
                 "icp_definition": "", "language": "zh", "company_raw_data": "",
                 "company_profile": {}, "lead_score": 0, "score_rationale": "",
                 "key_hooks": [], "email_draft": {}, "market_analysis": {},
                 "mode": "", "log_messages": [], "error_message": None,
                 "should_proceed": False}
        assert route_start(state) == AgentRole.RESEARCHER

    def test_none_target_url(self):
        state = {"target_url": None, "product_desc": "x", "icp_definition": "",
                 "language": "zh", "company_raw_data": "", "company_profile": {},
                 "lead_score": 0, "score_rationale": "", "key_hooks": [],
                 "email_draft": {}, "market_analysis": {}, "mode": "",
                 "log_messages": [], "error_message": None, "should_proceed": False}
        assert route_start(state) == AgentRole.MARKET_ANALYZER


class TestRouteByScore:

    def _make_state(self, error=None, should_proceed=False):
        return {"target_url": "x", "product_desc": "x", "icp_definition": "",
                "language": "zh", "company_raw_data": "", "company_profile": {},
                "lead_score": 80, "score_rationale": "", "key_hooks": [],
                "email_draft": {}, "market_analysis": {}, "mode": "",
                "log_messages": [], "error_message": error,
                "should_proceed": should_proceed}

    def test_error_routes_to_end(self):
        assert route_by_score(self._make_state(error="some error")) == RouteTarget.END

    def test_should_proceed_routes_to_proceed(self):
        assert route_by_score(self._make_state(should_proceed=True)) == RouteTarget.PROCEED

    def test_no_proceed_routes_to_end(self):
        assert route_by_score(self._make_state(should_proceed=False)) == RouteTarget.END


class TestModeConstants:

    def test_sdr_mode(self):
        assert Mode.SDR == "SDR"

    def test_market_analysis_mode(self):
        assert Mode.MARKET_ANALYSIS == "MARKET_ANALYSIS"
