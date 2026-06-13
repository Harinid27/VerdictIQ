import logging
from typing import Dict, Any

from app.state import VerdictState
from app.services.gemini_service import analyze_case_evidence_and_risks

logger = logging.getLogger(__name__)

async def agent1_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: agent1_node
    Role: Evidence Intelligence Agent
    Responsibilities:
      - Audits and classifies all evidence in the case (Strong, Moderate, Weak).
      - Explains reasoning, assumptions, reliability, and challenges for each evidence item.
      - Identifies missing evidence, gaps, contradictions, reliability concerns, alternative interpretations, and loopholes.
    """
    workspace_id = state.get("workspace_id")
    agent0_output = state.get("agent0_output")
    lawyer_side = state.get("lawyer_side") or (agent0_output.get("legal_context", {}).get("lawyer_side") if agent0_output else None)

    logger.info(f"LangGraph: Starting agent1_node (Evidence Intelligence Agent) for workspace_id: {workspace_id}")

    if not agent0_output:
        raise ValueError("Agent 0 structured context is missing in state.")

    # Call Gemini service to perform Agent 1 auditing
    try:
        audit_result = await analyze_case_evidence_and_risks(
            structured_context=agent0_output,
            lawyer_side=lawyer_side
        )
    except Exception as e:
        logger.error(f"Failed to generate Agent 1 audit: {e}")
        raise ValueError(f"Agent 1 auditing failed: {e}")

    # Return updated state
    return {
        **state,
        "agent1_output": audit_result,
        "current_stage": "agent1_completed"
    }
