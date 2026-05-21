"""
Agent 路由常量、命名空间与异常白名单。
"""
import requests


class AgentRole:
    RESEARCHER = "researcher"
    PROCESSOR = "processor"
    SCORER = "scorer"
    COPYWRITER = "copywriter"
    MARKET_ANALYZER = "market_analyzer"


class Mode:
    SDR = "SDR"
    MARKET_ANALYSIS = "MARKET_ANALYSIS"


class RouteTarget:
    END = "end"
    PROCEED = "proceed"


AGENT_TEMPERATURES = {
    AgentRole.PROCESSOR: 0.0,
    AgentRole.SCORER: 0.0,
    AgentRole.MARKET_ANALYZER: 0.0,
    AgentRole.COPYWRITER: 0.2,
    AgentRole.RESEARCHER: 0.0,
}

RECOVERABLE_ERRORS = (
    requests.RequestException,
    TimeoutError,
    ConnectionError,
    OSError,
    ValueError,
    KeyError,
    TypeError,
    ImportError,
    AttributeError,
)
