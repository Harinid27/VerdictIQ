import logging
from typing import Dict, Any

from app.state import VerdictState
from app.services.gemini_service import generate_final_legal_report

logger = logging.getLogger(__name__)

async def agent3_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: agent3_node
    Role: Legal Intelligence & Final Report Agent
    Responsibilities:
      - Consumes Agent 0, Agent 1, and Agent 2 outputs.
      - Maps facts to legal sections and handles procedural mapping (Step 1).
      - Performs case strength SWOT analysis (Step 2).
      - Generates detailed Executive Summary (Step 3).
      - Produces the comprehensive Final Legal Intelligence Report (Step 4).
    """
    workspace_id = state.get("workspace_id")
    agent0_output = state.get("agent0_output")
    agent1_output = state.get("agent1_output")
    agent2_output = state.get("agent2_output")
    case_context = state.get("case_context") or {}
    rag_context = case_context.get("rag_context", "")

    logger.info(f"LangGraph: Starting agent3_node (Full Legal Intelligence Engine) for workspace_id: {workspace_id}")

    if not agent0_output:
        raise ValueError("Agent 0 structured context is missing in state.")
    if not agent1_output:
        raise ValueError("Agent 1 auditing output is missing in state.")
    if not agent2_output:
        raise ValueError("Agent 2 strategic output is missing in state.")

    # Call Gemini synthesis service to generate report
    try:
        report_result = await generate_final_legal_report(
            workspace_meta=agent0_output, 
            agent1_analysis=agent1_output,
            agent2_strategy=agent2_output,
            rag_context=rag_context
        )
    except Exception as e:
        logger.error(f"Failed to generate Agent 3 report: {e}")
        raise ValueError(f"Agent 3 report generation failed: {e}")

    # Return updated state
    return {
        **state,
        "agent3_output": report_result,
        "current_stage": "agent3_completed"
    }

