import logging
from typing import Dict, Any

from app.state import VerdictState
from app.services.gemini_service import analyze_case_evidence_and_risks

logger = logging.getLogger(__name__)

async def agent1_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: agent1_node
    Role: Evidence Strength & Risk Audit Agent
    Responsibilities:
      - Audits the case-wide structured context from Agent 0.
      - Classifies evidence strength (strong, moderate, weak).
      - Identifies unsupported claims and missing evidence.
      - Uncovers loopholes and timeline/factual contradictions.
    """
    workspace_id = state.get("workspace_id")
    agent0_output = state.get("agent0_output")
    lawyer_side = state.get("lawyer_side")

    logger.info(f"LangGraph: Starting agent1_node for workspace_id: {workspace_id}")

    if not agent0_output:
        raise ValueError("Agent 0 structured context is missing in state.")

    # Call Gemini service to perform evidence audit and risk assessment
    try:
        analysis_result = await analyze_case_evidence_and_risks(
            structured_context=agent0_output, 
            lawyer_side=lawyer_side
        )
    except Exception as e:
        logger.error(f"Failed to perform Agent 1 analysis: {e}")
        raise ValueError(f"Agent 1 analysis execution failed: {e}")

    # Extract risk level
    risk_info = analysis_result.get("risk_analysis", {})
    risk_level = risk_info.get("risk_level", "Medium Risk")

    # Formulate output structure for State inter-agent memory
    agent1_output = {
        "workspace_id": workspace_id,
        "strong_evidence": analysis_result.get("strong_evidence", []),
        "moderate_evidence": analysis_result.get("moderate_evidence", []),
        "weak_evidence": analysis_result.get("weak_evidence", []),
        "unsupported_claims": analysis_result.get("unsupported_claims", []),
        "missing_evidence": analysis_result.get("missing_evidence", []),
        "loopholes": analysis_result.get("loopholes", []),
        "contradictions": analysis_result.get("contradictions", []),
        "risk_analysis": risk_info,
        "risk_level": risk_level,
        "confidence_scores": analysis_result.get("confidence_scores", []),
        "evidence_relationships": analysis_result.get("evidence_relationships", []),
        "prepared_for_agent2": True,
        "prepared_for_agent3": True
    }

    # Return updated state
    return {
        **state,
        "agent1_output": agent1_output,
        "current_stage": "agent1_completed"
    }
