from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import AgentState
from core import AgentRole, RouteTarget
from core.agents.researcher import researcher_node
from core.agents.processor import processor_node
from core.agents.scorer import scorer_node
from core.agents.copywriter import copywriter_node
from core.agents.market_analyzer import market_analyzer_node


def route_by_score(state: AgentState) -> str:
    if state.get("error_message"):
        return RouteTarget.END
    if state.get("should_proceed", False):
        return RouteTarget.PROCEED
    return RouteTarget.END


def route_start(state: AgentState) -> str:
    if not state.get("target_url") or state.get("target_url").strip() == "":
        return AgentRole.MARKET_ANALYZER
    return AgentRole.RESEARCHER


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node(AgentRole.RESEARCHER, researcher_node)
    builder.add_node(AgentRole.PROCESSOR, processor_node)
    builder.add_node(AgentRole.SCORER, scorer_node)
    builder.add_node(AgentRole.COPYWRITER, copywriter_node)
    builder.add_node(AgentRole.MARKET_ANALYZER, market_analyzer_node)

    builder.set_conditional_entry_point(
        route_start,
        {
            AgentRole.MARKET_ANALYZER: AgentRole.MARKET_ANALYZER,
            AgentRole.RESEARCHER: AgentRole.RESEARCHER,
        },
    )

    builder.add_edge(AgentRole.RESEARCHER, AgentRole.PROCESSOR)
    builder.add_edge(AgentRole.PROCESSOR, AgentRole.SCORER)
    builder.add_conditional_edges(
        AgentRole.SCORER,
        route_by_score,
        {
            RouteTarget.PROCEED: AgentRole.COPYWRITER,
            RouteTarget.END: END,
        },
    )
    builder.add_edge(AgentRole.COPYWRITER, END)
    builder.add_edge(AgentRole.MARKET_ANALYZER, END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


graph = build_graph()
