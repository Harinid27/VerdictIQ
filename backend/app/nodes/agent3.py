import logging
from typing import Dict, Any

from app.state import VerdictState
from app.services.gemini_service import generate_final_legal_report

logger = logging.getLogger(__name__)

async def agent3_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: agent3_node
    Role: Legal Intelligence Synthesis & Final Reporting Agent
    Responsibilities:
      - Consolidates structured context (Agent 0), evidence audit (Agent 1), and courtroom strategy (Agent 2).
      - Rates overall case strength.
      - Researches contextually relevant legal references and statutes.
      - Provides final recommendations and action items.
      - Generates the complete multi-section legal intelligence report.
    """
    workspace_id = state.get("workspace_id")
    agent0_output = state.get("agent0_output")
    agent1_output = state.get("agent1_output")
    agent2_output = state.get("agent2_output")

    logger.info(f"LangGraph: Starting agent3_node for workspace_id: {workspace_id}")

    if not agent0_output or not agent1_output or not agent2_output:
        raise ValueError("Agent 0, Agent 1, or Agent 2 outputs are missing in state.")

    # Call Gemini synthesis service to generate report
    try:
        report_result = await generate_final_legal_report(
            workspace_meta=agent0_output, 
            agent1_analysis=agent1_output, 
            agent2_strategy=agent2_output
        )
    except Exception as e:
        logger.error(f"Failed to generate Agent 3 report: {e}")
        raise ValueError(f"Agent 3 report generation failed: {e}")

    # Formulate output structure for State inter-agent memory
    agent3_output = {
        "workspace_id": workspace_id,
        "executive_summary": report_result.get("executive_summary", ""),
        "case_strength": report_result.get("case_strength", "Moderate Case"),
        "strongest_evidence": report_result.get("strongest_evidence", []),
        "weak_evidence": report_result.get("weak_evidence", []),
        "missing_evidence": report_result.get("missing_evidence", []),
        "loopholes": report_result.get("loopholes", []),
        "legal_references": report_result.get("legal_references", []),
        "strategic_recommendations": report_result.get("strategic_recommendations", []),
        "courtroom_risks": report_result.get("courtroom_risks", []),
        "final_case_assessment": report_result.get("final_case_assessment", ""),
        "generated_report": report_result.get("generated_report", {"sections": []})
    }

    # Return updated state
    return {
        **state,
        "agent3_output": agent3_output,
        "current_stage": "agent3_completed"
    }
