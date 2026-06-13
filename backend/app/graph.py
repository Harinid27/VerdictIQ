import logging
from langgraph.graph import StateGraph, START, END

from app.state import VerdictState
from app.nodes.load_workspace import load_workspace_node
from app.nodes.agent0 import agent0_node
from app.nodes.agent1 import agent1_node
from app.nodes.agent2 import agent2_node
from app.nodes.agent3 import agent3_node
from app.nodes.save_results import save_results_node

logger = logging.getLogger(__name__)

# Initialize the StateGraph with the shared VerdictState schema
workflow = StateGraph(VerdictState)

# Register all multi-agent processing nodes
workflow.add_node("load_workspace_node", load_workspace_node)
workflow.add_node("agent0_node", agent0_node)
workflow.add_node("agent1_node", agent1_node)
workflow.add_node("agent2_node", agent2_node)
workflow.add_node("agent3_node", agent3_node)
workflow.add_node("save_results_node", save_results_node)

# Configure the workflow edges (sequence: START -> load_workspace -> agent0 -> agent1 -> agent2 -> agent3 -> save_results -> END)
workflow.add_edge(START, "load_workspace_node")
workflow.add_edge("load_workspace_node", "agent0_node")
workflow.add_edge("agent0_node", "agent1_node")
workflow.add_edge("agent1_node", "agent2_node")
workflow.add_edge("agent2_node", "agent3_node")
workflow.add_edge("agent3_node", "save_results_node")
workflow.add_edge("save_results_node", END)

# Compile the workflow into a runnable graph
app_graph = workflow.compile()

logger.info("LangGraph VerdictIQ multi-agent workflow compiled successfully.")

