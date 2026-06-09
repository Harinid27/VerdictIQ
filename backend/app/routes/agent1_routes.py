from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.gemini_service import generate_final_legal_report
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
        return {
            "success": False,
            "message": "Structured context unavailable"
        }

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

    # Call Gemini service to perform unified Agent 3 legal intelligence
    try:
        merged_meta = dict(context_doc)
        if workspace_meta:
            merged_meta["legal_context"] = {
                "case_title": workspace_meta.get("case_title"),
                "case_type": workspace_meta.get("case_type"),
                "lawyer_side": lawyer_side or "Plaintiff",
                "client_name": workspace_meta.get("client_name"),
                "opposing_party": workspace_meta.get("opposing_party")
            }
        else:
            merged_meta["legal_context"] = {
                "case_title": "Unnamed Case",
                "case_type": "General Dispute",
                "lawyer_side": lawyer_side or "Plaintiff",
                "client_name": "Client",
                "opposing_party": "Opponent"
            }

        analysis_result = await generate_final_legal_report(merged_meta, rag_context)
    except Exception as e:
        logger.error(f"Failed to perform unified Agent 3 analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 3 reasoning engine failed: {e}"
        )

    # 3. Use save_results_node to map and save everything across collections
    try:
        state = {
            "workspace_id": workspace_id,
            "agent0_output": context_doc,
            "agent3_output": analysis_result
        }
        await save_results_node(state)
    except Exception as e:
        logger.error(f"Failed to save unified analysis results: {e}")
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
        "prepared_for_agent2": True,
        "prepared_for_agent3": True
    }

    return {
        "success": True,
        "message": "Agent 1 analysis completed",
        "analysis": response_analysis
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
        "prepared_for_agent2": True,
        "prepared_for_agent3": True
    }
