from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.gemini_service import analyze_case_evidence_and_risks

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

    # 2. Call Gemini service to perform evidence audit and risk assessment
    try:
        analysis_result = await analyze_case_evidence_and_risks(context_doc)
    except Exception as e:
        logger.error(f"Failed to perform Agent 1 analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 1 analysis execution failed: {e}"
        )

    # Extract risk level from risk_analysis dict
    risk_info = analysis_result.get("risk_analysis", {})
    risk_level = risk_info.get("risk_level", "Medium Risk")

    # 3. Formulate the document to be saved in agent1_analysis collection
    agent1_doc = {
        "workspace_id": workspace_id,
        "strong_evidence": analysis_result.get("strong_evidence", []),
        "moderate_evidence": analysis_result.get("moderate_evidence", []),
        "weak_evidence": analysis_result.get("weak_evidence", []),
        "unsupported_claims": analysis_result.get("unsupported_claims", []),
        "missing_evidence": analysis_result.get("missing_evidence", []),
        "loopholes": analysis_result.get("loopholes", []),
        "contradictions": analysis_result.get("contradictions", []),
        "risk_analysis": risk_info,
        "risk_level": risk_level, # store for quick query
        "confidence_scores": analysis_result.get("confidence_scores", []),
        "evidence_relationships": analysis_result.get("evidence_relationships", []),
        "prepared_for_agent2": True,
        "prepared_for_agent3": True,
        "generated_at": datetime.utcnow()
    }

    # 4. Save/Update in MongoDB agent1_analysis collection
    agent1_collection = get_collection("agent1_analysis")
    await agent1_collection.update_one(
        {"workspace_id": workspace_id},
        {"$set": agent1_doc},
        upsert=True
    )

    # 5. Build response conforming to OUTPUT FORMAT
    response_analysis = {
        "workspace_id": workspace_id,
        "strong_evidence": agent1_doc["strong_evidence"],
        "moderate_evidence": agent1_doc["moderate_evidence"],
        "weak_evidence": agent1_doc["weak_evidence"],
        "unsupported_claims": agent1_doc["unsupported_claims"],
        "missing_evidence": agent1_doc["missing_evidence"],
        "loopholes": agent1_doc["loopholes"],
        "contradictions": agent1_doc["contradictions"],
        "risk_level": risk_level,
        "confidence_scores": agent1_doc["confidence_scores"],
        "evidence_relationships": agent1_doc["evidence_relationships"],
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
        "prepared_for_agent2": True,
        "prepared_for_agent3": True
    }
