from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.gemini_service import analyze_case_evidence_and_risks
from app.services.rag_service import RAGService
from app.nodes.save_results import save_results_node

router = APIRouter(prefix="/api/agent1", tags=["Agent 1 Auditing"])
logger = logging.getLogger(__name__)

# Helper to serialize MongoDB doc
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.post("/analyze/{workspace_id}", status_code=status.HTTP_200_OK)
async def analyze_workspace_evidence(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])

    # 1. Fetch Agent 0 structured context from structured_case_context collection
    scc_collection = get_collection("structured_case_context")
    context_doc = await scc_collection.find_one({"workspace_id": workspace_id})
    if not context_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Structured case context unavailable. Please run Agent 0 intake compilation first."
        )

    # Fetch workspaces meta details to get lawyer_side
    workspace_meta = await get_collection("workspaces").find_one({"workspace_id": workspace_id})
    lawyer_side = workspace_meta.get("lawyer_side") if workspace_meta else None

    # Retrieve RAG context
    try:
        rag_context = await RAGService.retrieve_relevant_context(
            query=context_doc.get("case_summary", "")[:300],
            workspace_id=workspace_id,
            top_k=3
        )
    except Exception as e:
        logger.error(f"RAG context retrieval failed in Agent 1 route: {e}")
        rag_context = ""

    # Call Gemini service to perform Agent 1 evidence auditing and risk analysis
    try:
        analysis_result = await analyze_case_evidence_and_risks(
            structured_context=context_doc,
            lawyer_side=lawyer_side
        )
    except Exception as e:
        logger.error(f"Failed to perform Agent 1 analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 1 reasoning engine failed: {e}"
        )

    # 3. Use save_results_node to map and save Agent 1 results
    try:
        state = {
            "workspace_id": workspace_id,
            "agent0_output": context_doc,
            "agent1_output": analysis_result
        }
        await save_results_node(state)
    except Exception as e:
        logger.error(f"Failed to save Agent 1 analysis results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist analysis results: {e}"
        )

    # Fetch stored analysis for response
    agent1_collection = get_collection("agent1_analysis")
    agent1_doc = await agent1_collection.find_one({"workspace_id": workspace_id})
    if not agent1_doc:
        raise HTTPException(status_code=500, detail="Saved Agent 1 analysis could not be retrieved")

    # 5. Build response conforming to OUTPUT FORMAT
    response_analysis = {
        "workspace_id": workspace_id,
        "strong_evidence": agent1_doc.get("strong_evidence", []),
        "moderate_evidence": agent1_doc.get("moderate_evidence", []),
        "weak_evidence": agent1_doc.get("weak_evidence", []),
        "unsupported_claims": agent1_doc.get("unsupported_claims", []),
        "missing_evidence": agent1_doc.get("missing_evidence", []),
        "loopholes": agent1_doc.get("loopholes", []),
        "contradictions": agent1_doc.get("contradictions", []),
        "risk_level": agent1_doc.get("risk_level", "Medium Risk"),
        "confidence_scores": agent1_doc.get("confidence_scores", []),
        "evidence_relationships": agent1_doc.get("evidence_relationships", []),
        "evidence_evaluations": agent1_doc.get("evidence_evaluations", []),
        "investigative_gaps": agent1_doc.get("investigative_gaps", []),
        "reliability_concerns": agent1_doc.get("reliability_concerns", []),
        "alternative_interpretations": agent1_doc.get("alternative_interpretations", []),
        "prepared_for_agent2": True,
        "prepared_for_agent3": True
    }

    return {
        "success": True,
        "message": "Agent 1 analysis completed",
        "analysis": response_analysis
    }

@router.get("/results/{workspace_id}")
async def get_agent1_results(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])

    # 1. Fetch Agent 1 results from agent1_analysis collection
    agent1_collection = get_collection("agent1_analysis")
    doc = await agent1_collection.find_one({"workspace_id": workspace_id})
    if not doc:
        raise HTTPException(
            status_code=404, 
            detail="Agent 1 analysis not found for this workspace. Run Agent 1 analysis first."
        )

    # 2. Return the structured results
    return {
        "workspace_id": workspace_id,
        "strong_evidence": doc.get("strong_evidence", []),
        "moderate_evidence": doc.get("moderate_evidence", []),
        "weak_evidence": doc.get("weak_evidence", []),
        "unsupported_claims": doc.get("unsupported_claims", []),
        "missing_evidence": doc.get("missing_evidence", []),
        "loopholes": doc.get("loopholes", []),
        "contradictions": doc.get("contradictions", []),
        "risk_level": doc.get("risk_level") or doc.get("risk_analysis", {}).get("risk_level", "Medium Risk"),
        "confidence_scores": doc.get("confidence_scores", []),
        "evidence_relationships": doc.get("evidence_relationships", []),
        "evidence_evaluations": doc.get("evidence_evaluations", []),
        "investigative_gaps": doc.get("investigative_gaps", []),
        "reliability_concerns": doc.get("reliability_concerns", []),
        "alternative_interpretations": doc.get("alternative_interpretations", []),
        "prepared_for_agent2": True,
        "prepared_for_agent3": True
    }
