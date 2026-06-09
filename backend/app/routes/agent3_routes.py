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

    # Check if Agent 3 report is already saved
    agent3_collection = get_collection("agent3_final_reports")
    agent3_doc = await agent3_collection.find_one({"workspace_id": workspace_id})

    if not agent3_doc:
        # Fallback to trigger unified Agent 3 engine
        logger.info(f"Agent 3 Route: Report not found. Triggering Agent 3 reasoning engine for workspace: {workspace_id}")
        from app.routes.agent1_routes import analyze_workspace_evidence
        await analyze_workspace_evidence(workspace_id, current_user)
        agent3_doc = await agent3_collection.find_one({"workspace_id": workspace_id})

    if not agent3_doc:
        raise HTTPException(
            status_code=400,
            detail="Unified Agent 3 intelligence report must be generated first. Structured context unavailable."
        )

    response_report = {
        "workspace_id": workspace_id,
        "executive_summary": agent3_doc.get("executive_summary", ""),
        "case_strength": agent3_doc.get("case_strength", "Moderate Case"),
        "strongest_evidence": agent3_doc.get("strongest_evidence", []),
        "weak_evidence": agent3_doc.get("weak_evidence", []),
        "missing_evidence": agent3_doc.get("missing_evidence", []),
        "identified_loopholes": agent3_doc.get("loopholes", []),
        "counterargument_risks": agent3_doc.get("courtroom_risks", []),
        "legal_references": agent3_doc.get("legal_references", []),
        "strategic_recommendations": agent3_doc.get("strategic_recommendations", []),
        "overall_case_assessment": agent3_doc.get("final_case_assessment", ""),
        "ai_disclaimer": "This AI-generated analysis is intended for legal research assistance and strategic support only. It should not be treated as definitive legal advice.",
        "report_ready": True
    }

    return {
        "success": True,
        "message": "Agent 3 report loaded from unified intelligence engine",
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

@router.get("/reports/all")
async def get_all_reports(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]

    # 1. Fetch workspaces for this user
    workspaces_collection = get_collection("workspaces")
    user_workspaces = await workspaces_collection.find({"created_by": user_email}).to_list(length=1000)
    workspace_ids = [w["workspace_id"] for w in user_workspaces]
    
    workspace_map = {w["workspace_id"]: w for w in user_workspaces}

    # 2. Fetch completed final reports
    agent3_collection = get_collection("agent3_final_reports")
    reports_cursor = agent3_collection.find({"workspace_id": {"$in": workspace_ids}})
    reports_docs = await reports_cursor.to_list(length=1000)

    reports_list = []
    for r in reports_docs:
        ws_id = r["workspace_id"]
        ws = workspace_map.get(ws_id, {})
        reports_list.append({
            "id": ws_id,
            "title": "Legal Intelligence Audit Report",
            "generatedDate": r.get("generated_at").strftime("%Y-%m-%d") if r.get("generated_at") else datetime.utcnow().strftime("%Y-%m-%d"),
            "caseName": ws.get("case_title", "Unnamed Case"),
            "confidenceScore": 95,
            "fileSize": "1.2 MB",
            "category": "Evidentiary Review"
        })

    return {
        "success": True,
        "data": reports_list
    }
