import logging
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId

from app.state import VerdictState
from app.database import get_collection

logger = logging.getLogger(__name__)

async def save_results_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: save_results_node
    Role: Persistence Layer Integration
    Responsibilities:
      - Saves Agent 0's structured context to 'structured_case_context'.
      - Maps the unified Agent 3 output into the legacy collections ('agent1_analysis', 'agent2_strategy', and 'agent3_final_reports').
      - Ensures 100% database schema backward compatibility with the frontend.
    """
    workspace_id = state.get("workspace_id")
    logger.info(f"LangGraph: Starting save_results_node for workspace_id: {workspace_id}")

    agent0_output = state.get("agent0_output")
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
            "evidence_summary": agent0_output.get("evidence_summary", []),
            "evidence_details": agent0_output.get("evidence_details", []),
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

    agent1_output = state.get("agent1_output")
    agent2_output = state.get("agent2_output")

    # 2. Save Agent 1 Output: agent1_analysis
    if agent1_output:
        # Determine overall risk level based on risk analysis
        risk_level = agent1_output.get("risk_level") or agent1_output.get("risk_analysis", {}).get("risk_level", "Medium Risk")
        
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
            "risk_level": risk_level,
            "confidence_scores": agent1_output.get("confidence_scores", []),
            "evidence_relationships": agent1_output.get("evidence_relationships", []),
            "evidence_evaluations": agent1_output.get("evidence_evaluations", []),
            "investigative_gaps": agent1_output.get("investigative_gaps", []),
            "reliability_concerns": agent1_output.get("reliability_concerns", []),
            "alternative_interpretations": agent1_output.get("alternative_interpretations", []),
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
            "adversarial_simulations": agent2_output.get("adversarial_simulations", []),
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
        evidence_analysis = agent3_output.get("evidence_analysis", {})
        
        # Risk level determination based on score
        score_str = agent3_output.get("final_score", "50")
        try:
            score_val = int(score_str.replace("%", "").strip())
        except Exception:
            score_val = 50

        if score_val < 40:
            risk_level = "High Risk"
        elif score_val < 70:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"

        legal_refs = []
        for sec in agent3_output.get("legal_sections", []):
            legal_refs.append({
                "statute_name": sec.get("act_or_statute", ""),
                "section": sec.get("section", ""),
                "jurisdiction": sec.get("jurisdiction", "Applicable Jurisdiction"),
                "description": sec.get("simple_explanation", ""),
                "applicability_to_case": sec.get("relevance", ""),
                "burden_of_proof": sec.get("burden_of_proof", ""),
                "compliance_gap": sec.get("compliance_gap", ""),
                "procedural_considerations": sec.get("procedural_considerations", "N/A"),
                "why_applies": sec.get("why_applies", "N/A")
            })

        sections = [
            {
              "title": "Summary",
              "content": agent3_output.get("final_assessment", "")
            },
            {
              "title": "Strong Points",
              "content": "\n".join([f"- {item.get('file_name')}: {item.get('reasoning')}" for item in evidence_analysis.get("strong_evidence", [])]) or "None identified."
            },
            {
              "title": "Weak Points",
              "content": "\n".join([f"- {item.get('file_name')}: {item.get('reasoning')}" for item in evidence_analysis.get("weak_evidence", [])]) or "None identified."
            },
            {
              "title": "Missing Proof",
              "content": "\n".join([f"- {item.get('description')} (Impact: {item.get('impact')})" for item in evidence_analysis.get("missing_evidence", [])]) or "None identified."
            },
            {
              "title": "Possible Opponent Attack",
              "content": "\n".join([f"- {op.get('attack_vector')}: {op.get('explanation')}" for op in agent3_output.get("legal_arguments", {}).get("opponent_side", [])]) or "None predicted."
            },
            {
              "title": "Recommended Action",
              "content": "\n".join([f"- {r}" for r in agent3_output.get("recommendations", [])]) or "None provided."
            }
        ]

        case_strength = "Strong Case" if score_val > 70 else ("Weak Case" if score_val < 40 else "Moderate Case")

        agent3_doc = {
            "workspace_id": workspace_id,
            "executive_summary": agent3_output.get("executive_summary") or agent3_output.get("final_assessment", ""),
            "case_strength": case_strength,
            "case_strength_score": score_val,
            "strongest_evidence": evidence_analysis.get("strong_evidence", []),
            "weak_evidence": evidence_analysis.get("weak_evidence", []),
            "missing_evidence": evidence_analysis.get("missing_evidence", []),
            "loopholes": evidence_analysis.get("loopholes", []),
            "legal_references": legal_refs,
            "strategic_recommendations": agent3_output.get("recommendations", []),
            "courtroom_risks": [
                {
                    "title": r.get("title", "Risk"),
                    "description": r.get("description", ""),
                    "severity": r.get("severity", "Medium")
                } for r in agent3_output.get("case_risks", [])
            ],
            "final_case_assessment": agent3_output.get("final_assessment", ""),
            "generated_report": {
                "sections": sections
            },
            "case_strength_assessment": agent3_output.get("case_strength_assessment", {}),
            "final_legal_intelligence_report": agent3_output.get("final_legal_intelligence_report", ""),
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
            update_fields = {
                "status": "Audit Completed",
                "riskLevel": risk_level.replace(" Risk", ""),
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

