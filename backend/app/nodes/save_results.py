import logging
from datetime import datetime
from typing import Dict, Any

from app.state import VerdictState
from app.database import get_collection

logger = logging.getLogger(__name__)

async def save_results_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: save_results_node
    Role: Persistence Layer Integration
    Responsibilities:
      - Saves Agent 0's structured context to 'structured_case_context'.
      - Saves Agent 1's evidence audit to 'agent1_analysis'.
      - Saves Agent 2's strategy mockups to 'agent2_strategy'.
      - Saves Agent 3's final synthesized reports to 'agent3_final_reports'.
      - Ensures full persistence and backwards compatibility with the existing database schema.
    """
    workspace_id = state.get("workspace_id")
    logger.info(f"LangGraph: Starting save_results_node for workspace_id: {workspace_id}")

    agent0_output = state.get("agent0_output")
    agent1_output = state.get("agent1_output")
    agent2_output = state.get("agent2_output")
    agent3_output = state.get("agent3_output")

    # 1. Save Agent 0 Output: structured_case_context
    if agent0_output:
        scc_doc = {
            "workspace_id": workspace_id,
            "case_summary": agent0_output.get("case_summary", ""),
            "claims": agent0_output.get("claims", []),
            "timeline": agent0_output.get("timeline", []),
            "key_entities": agent0_output.get("key_entities", []),
            "evidence_relationships": agent0_output.get("evidence_relationships", []),
            "objectives": agent0_output.get("objectives", []),
            "concerns": agent0_output.get("concerns", []),
            "generated_at": datetime.utcnow()
        }
        scc_collection = get_collection("structured_case_context")
        await scc_collection.update_one(
            {"workspace_id": workspace_id},
            {"$set": scc_doc},
            upsert=True
        )
        logger.info(f"LangGraph: Persisted structured_case_context for workspace: {workspace_id}")

    # 2. Save Agent 1 Output: agent1_analysis
    if agent1_output:
        agent1_doc = {
            "workspace_id": workspace_id,
            "strong_evidence": agent1_output.get("strong_evidence", []),
            "moderate_evidence": agent1_output.get("moderate_evidence", []),
            "weak_evidence": agent1_output.get("weak_evidence", []),
            "unsupported_claims": agent1_output.get("unsupported_claims", []),
            "missing_evidence": agent1_output.get("missing_evidence", []),
            "loopholes": agent1_output.get("loopholes", []),
            "contradictions": agent1_output.get("contradictions", []),
            "risk_analysis": agent1_output.get("risk_analysis", {}),
            "risk_level": agent1_output.get("risk_level", "Medium Risk"),
            "confidence_scores": agent1_output.get("confidence_scores", []),
            "evidence_relationships": agent1_output.get("evidence_relationships", []),
            "prepared_for_agent2": True,
            "prepared_for_agent3": True,
            "generated_at": datetime.utcnow()
        }
        agent1_collection = get_collection("agent1_analysis")
        await agent1_collection.update_one(
            {"workspace_id": workspace_id},
            {"$set": agent1_doc},
            upsert=True
        )
        logger.info(f"LangGraph: Persisted agent1_analysis for workspace: {workspace_id}")

    # 3. Save Agent 2 Output: agent2_strategy
    if agent2_output:
        agent2_doc = {
            "workspace_id": workspace_id,
            "lawyer_side": agent2_output.get("lawyer_side", "Plaintiff"),
            "lawyer_arguments": agent2_output.get("lawyer_arguments", []),
            "opponent_counterarguments": agent2_output.get("opponent_counterarguments", []),
            "rebuttal_strategies": agent2_output.get("rebuttal_strategies", []),
            "courtroom_risks": agent2_output.get("courtroom_risks", []),
            "strategic_recommendations": agent2_output.get("strategic_recommendations", []),
            "argument_priorities": agent2_output.get("argument_priorities", {}),
            "evidence_utilization_strategy": agent2_output.get("evidence_utilization_strategy", []),
            "prepared_for_agent3": True,
            "generated_at": datetime.utcnow()
        }
        agent2_collection = get_collection("agent2_strategy")
        await agent2_collection.update_one(
            {"workspace_id": workspace_id},
            {"$set": agent2_doc},
            upsert=True
        )
        logger.info(f"LangGraph: Persisted agent2_strategy for workspace: {workspace_id}")

    # 4. Save Agent 3 Output: agent3_final_reports
    if agent3_output:
        agent3_doc = {
            "workspace_id": workspace_id,
            "executive_summary": agent3_output.get("executive_summary", ""),
            "case_strength": agent3_output.get("case_strength", "Moderate Case"),
            "strongest_evidence": agent3_output.get("strongest_evidence", []),
            "weak_evidence": agent3_output.get("weak_evidence", []),
            "missing_evidence": agent3_output.get("missing_evidence", []),
            "loopholes": agent3_output.get("loopholes", []),
            "legal_references": agent3_output.get("legal_references", []),
            "strategic_recommendations": agent3_output.get("strategic_recommendations", []),
            "courtroom_risks": agent3_output.get("courtroom_risks", []),
            "final_case_assessment": agent3_output.get("final_case_assessment", ""),
            "generated_report": agent3_output.get("generated_report", {"sections": []}),
            "generated_at": datetime.utcnow()
        }
        agent3_collection = get_collection("agent3_final_reports")
        await agent3_collection.update_one(
            {"workspace_id": workspace_id},
            {"$set": agent3_doc},
            upsert=True
        )
        logger.info(f"LangGraph: Persisted agent3_final_reports for workspace: {workspace_id}")

        # Update general case status/riskLevel in legacy 'cases' collection
        try:
            cases_collection = get_collection("cases")
            from bson import ObjectId
            update_fields = {
                "status": "Audit Completed",
                "riskLevel": agent1_output.get("risk_level", "Medium Risk").replace(" Risk", ""),
                "updated_at": datetime.utcnow()
            }
            try:
                oid = ObjectId(workspace_id)
                await cases_collection.update_one({"_id": oid}, {"$set": update_fields})
            except Exception:
                await cases_collection.update_one({"_id": workspace_id}, {"$set": update_fields})
            logger.info(f"LangGraph: Updated case metadata in cases collection for: {workspace_id}")
        except Exception as ex:
            logger.error(f"Failed to update case metadata in cases collection: {ex}")

    # Return updated state
    return {
        **state,
        "current_stage": "results_saved"
    }
