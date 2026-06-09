import logging
from typing import Dict, Any

from app.state import VerdictState
from app.services.gemini_service import generate_final_legal_report

logger = logging.getLogger(__name__)

async def agent3_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: agent3_node
    Role: FULL LEGAL INTELLIGENCE ENGINE (merged system)
    Responsibilities:
      - Sequentially runs evidence analysis, legal strategy generation, legal mapping, and report generation.
      - Consolidates structured context (Agent 0) and statutory RAG context.
      - Generates the complete multi-section legal intelligence report in the new Agent 3 JSON schema.
    """
    workspace_id = state.get("workspace_id")
    agent0_output = state.get("agent0_output")
    case_context = state.get("case_context") or {}
    rag_context = case_context.get("rag_context", "")

    logger.info(f"LangGraph: Starting agent3_node (Full Legal Intelligence Engine) for workspace_id: {workspace_id}")

    if not agent0_output:
        raise ValueError("Agent 0 structured context is missing in state.")

    # Call Gemini synthesis service to generate report
    try:
        report_result = await generate_final_legal_report(
            workspace_meta=agent0_output, 
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

