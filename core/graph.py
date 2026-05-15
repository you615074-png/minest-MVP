from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import AgentState
from core.agents.researcher import researcher_node
from core.agents.processor import processor_node
from core.agents.scorer import scorer_node
from core.agents.copywriter import copywriter_node
from core.agents.market_analyzer import market_analyzer_node


def route_by_score(state: AgentState) -> str:
    """条件路由：根据评分和错误状态决定下一步"""
    if state.get("error_message"):
        return "end"
    if state.get("should_proceed", False):
        return "proceed"
    return "end"


def route_start(state: AgentState) -> str:
    """如果未提供目标 URL，走市场分析模式；否则走 SDR 抓取模式"""
    if not state.get("target_url") or state.get("target_url").strip() == "":
        return "market_analyzer"
    return "researcher"


def build_graph():
    builder = StateGraph(AgentState)

    # 注册节点
    builder.add_node("researcher", researcher_node)
    builder.add_node("processor", processor_node)
    builder.add_node("scorer", scorer_node)
    builder.add_node("copywriter", copywriter_node)
    builder.add_node("market_analyzer", market_analyzer_node)

    # 入口分流
    builder.set_conditional_entry_point(
        route_start,
        {
            "market_analyzer": "market_analyzer",
            "researcher": "researcher"
        }
    )

    # SDR 模式分支
    builder.add_edge("researcher", "processor")
    builder.add_edge("processor", "scorer")
    builder.add_conditional_edges(
        "scorer",
        route_by_score,
        {
            "proceed": "copywriter",
            "end": END,
        },
    )
    builder.add_edge("copywriter", END)

    # 市场分析模式分支
    builder.add_edge("market_analyzer", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


# 模块级编译（结构层不含异步客户端，可安全缓存）
graph = build_graph()
