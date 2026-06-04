from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.gemini_service import generate_final_legal_report

router = APIRouter(prefix="/api/agent3", tags=["Agent 3 Final Synthesis"])
logger = logging.getLogger(__name__)

# Helper to serialize MongoDB doc
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.post("/generate-report/{workspace_id}", status_code=status.HTTP_200_OK)
async def generate_report(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])

    logger.info("✓ Loading Legal Intelligence Data")

    # 1. Fetch Agent 0 structured context
    scc_collection = get_collection("structured_case_context")
    context_doc = await scc_collection.find_one({"workspace_id": workspace_id})
    
    # 2. Fetch Agent 1 analysis
    agent1_collection = get_collection("agent1_analysis")
    a1_doc = await agent1_collection.find_one({"workspace_id": workspace_id})

    # 3. Fetch Agent 2 strategy
    agent2_collection = get_collection("agent2_strategy")
    a2_doc = await agent2_collection.find_one({"workspace_id": workspace_id})

    # Return 400 error if any of the dependencies are missing
    if not context_doc or not a1_doc or not a2_doc:
        logger.warning(f"Unable to generate report for workspace {workspace_id}: required outputs are missing. Agent0 context: {bool(context_doc)}, Agent1 analysis: {bool(a1_doc)}, Agent2 strategy: {bool(a2_doc)}")
        raise HTTPException(
            status_code=400,
            detail="Required agent outputs unavailable"
        )

    # Fetch workspace metadata
    workspaces_collection = get_collection("workspaces")
    workspace_meta = await workspaces_collection.find_one({"workspace_id": workspace_id})
    if not workspace_meta:
        workspace_meta = {}

    # Merge context & workspace details
    context_data = dict(context_doc)
    context_data["case_title"] = workspace_meta.get("case_title") or context_doc.get("case_title") or "Unnamed Case"
    context_data["case_type"] = workspace_meta.get("case_type") or context_doc.get("case_type") or "General Dispute"
    context_data["lawyer_side"] = workspace_meta.get("lawyer_side") or context_doc.get("lawyer_side") or "Plaintiff"
    context_data["client_name"] = workspace_meta.get("client_name") or "Client"
    context_data["opposing_party"] = workspace_meta.get("opposing_party") or "Opponent"
    context_data["case_description"] = workspace_meta.get("case_description") or ""

    logger.info("✓ Synthesizing Evidence Analysis")
    logger.info("✓ Building Strategic Legal Summary")
    logger.info("✓ Identifying Relevant Legal References")
    logger.info("✓ Evaluating Overall Case Strength")

    # 4. Call Gemini synthesis service to generate report
    try:
        report_result = await generate_final_legal_report(context_data, a1_doc, a2_doc)
    except Exception as e:
        logger.error(f"Failed to generate Agent 3 report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 3 report generation failed: {e}"
        )

    logger.info("✓ Generating Final Intelligence Report")

    # 5. Formulate document for database
    agent3_doc = {
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
        "generated_report": report_result.get("generated_report", {"sections": []}),
        "generated_at": datetime.utcnow()
    }

    # 6. Save in agent3_final_reports collection
    agent3_collection = get_collection("agent3_final_reports")
    await agent3_collection.update_one(
        {"workspace_id": workspace_id},
        {"$set": agent3_doc},
        upsert=True
    )

    # 7. Format output JSON
    response_report = {
        "workspace_id": workspace_id,
        "executive_summary": agent3_doc["executive_summary"],
        "case_strength": agent3_doc["case_strength"],
        "strongest_evidence": agent3_doc["strongest_evidence"],
        "weak_evidence": agent3_doc["weak_evidence"],
        "missing_evidence": agent3_doc["missing_evidence"],
        "identified_loopholes": agent3_doc["loopholes"],
        "counterargument_risks": agent3_doc["courtroom_risks"],
        "legal_references": agent3_doc["legal_references"],
        "strategic_recommendations": agent3_doc["strategic_recommendations"],
        "overall_case_assessment": agent3_doc["final_case_assessment"],
        "ai_disclaimer": "This AI-generated analysis is intended for legal research assistance and strategic support only. It should not be treated as definitive legal advice.",
        "report_ready": True
    }

    return {
        "success": True,
        "message": "Agent 3 report generated",
        "report": response_report
    }

@router.get("/report/{workspace_id}")
async def get_report(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])

    # Fetch stored report
    agent3_collection = get_collection("agent3_final_reports")
    doc = await agent3_collection.find_one({"workspace_id": workspace_id})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Agent 3 report not found. Generate it first."
        )

    # Format output JSON conforming to the Output Format schema
    return {
        "workspace_id": workspace_id,
        "executive_summary": doc.get("executive_summary", ""),
        "case_strength": doc.get("case_strength", "Moderate Case"),
        "strongest_evidence": doc.get("strongest_evidence", []),
        "weak_evidence": doc.get("weak_evidence", []),
        "missing_evidence": doc.get("missing_evidence", []),
        "identified_loopholes": doc.get("loopholes", []),
        "counterargument_risks": doc.get("courtroom_risks", []),
        "legal_references": doc.get("legal_references", []),
        "strategic_recommendations": doc.get("strategic_recommendations", []),
        "overall_case_assessment": doc.get("final_case_assessment", ""),
        "ai_disclaimer": "This AI-generated analysis is intended for legal research assistance and strategic support only. It should not be treated as definitive legal advice.",
        "report_ready": True
    }
