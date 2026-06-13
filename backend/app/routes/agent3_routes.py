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

    logger.info(f"Agent 3 Route: Regenerating report for workspace: {workspace_id}")
    
    # 1. Fetch Agent 0, Agent 1, and Agent 2 outputs from their collections
    agent0_doc = await get_collection("structured_case_context").find_one({"workspace_id": workspace_id})
    agent1_doc = await get_collection("agent1_analysis").find_one({"workspace_id": workspace_id})
    agent2_doc = await get_collection("agent2_strategy").find_one({"workspace_id": workspace_id})

    if not agent0_doc or not agent1_doc or not agent2_doc:
        raise HTTPException(
            status_code=400,
            detail="All previous agent stages (Agent 0, Agent 1, Agent 2) must be generated first."
        )

    # 2. Query RAG statutory context
    try:
        rag_context = await RAGService.retrieve_relevant_context(
            query=agent0_doc.get("case_summary", "")[:300],
            workspace_id=workspace_id,
            top_k=3
        )
    except Exception as e:
        logger.error(f"RAG context retrieval failed in Agent 3 route: {e}")
        rag_context = ""

    # 3. Call Gemini final legal report synthesis
    try:
        report_result = await generate_final_legal_report(
            workspace_meta=agent0_doc,
            agent1_analysis=agent1_doc,
            agent2_strategy=agent2_doc,
            rag_context=rag_context
        )
    except Exception as e:
        logger.error(f"Failed to generate Agent 3 report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 3 synthesis report generation failed: {e}"
        )

    # 4. Save using save_results_node
    try:
        state = {
            "workspace_id": workspace_id,
            "agent0_output": agent0_doc,
            "agent1_output": agent1_doc,
            "agent2_output": agent2_doc,
            "agent3_output": report_result
        }
        await save_results_node(state)
    except Exception as e:
        logger.error(f"Failed to save Agent 3 report results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist report results: {e}"
        )

    # 5. Fetch the saved report to return
    agent3_collection = get_collection("agent3_final_reports")
    agent3_doc = await agent3_collection.find_one({"workspace_id": workspace_id})

    if not agent3_doc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve generated report from database."
        )

    response_report = {
        "workspace_id": workspace_id,
        "executive_summary": agent3_doc.get("executive_summary", ""),
        "case_strength": agent3_doc.get("case_strength", "Moderate Case"),
        "case_strength_score": agent3_doc.get("case_strength_score", 50),
        "strongest_evidence": agent3_doc.get("strongest_evidence", []),
        "weak_evidence": agent3_doc.get("weak_evidence", []),
        "missing_evidence": agent3_doc.get("missing_evidence", []),
        "identified_loopholes": agent3_doc.get("loopholes", []),
        "counterargument_risks": agent3_doc.get("courtroom_risks", []),
        "legal_references": agent3_doc.get("legal_references", []),
        "strategic_recommendations": agent3_doc.get("strategic_recommendations", []),
        "overall_case_assessment": agent3_doc.get("final_case_assessment", ""),
        "case_strength_assessment": agent3_doc.get("case_strength_assessment", {}),
        "final_legal_intelligence_report": agent3_doc.get("final_legal_intelligence_report", ""),
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
        "case_strength_score": doc.get("case_strength_score", 50),
        "strongest_evidence": doc.get("strongest_evidence", []),
        "weak_evidence": doc.get("weak_evidence", []),
        "missing_evidence": doc.get("missing_evidence", []),
        "identified_loopholes": doc.get("loopholes", []),
        "counterargument_risks": doc.get("courtroom_risks", []),
        "legal_references": doc.get("legal_references", []),
        "strategic_recommendations": doc.get("strategic_recommendations", []),
        "overall_case_assessment": doc.get("final_case_assessment", ""),
        "case_strength_assessment": doc.get("case_strength_assessment", {}),
        "final_legal_intelligence_report": doc.get("final_legal_intelligence_report", ""),
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
            "confidenceScore": r.get("case_strength_score", 95),
            "fileSize": "1.2 MB",
            "category": "Evidentiary Review",
            "executive_summary": r.get("executive_summary", ""),
            "case_strength_assessment": r.get("case_strength_assessment", {}),
            "final_legal_intelligence_report": r.get("final_legal_intelligence_report", "")
        })

    return {
        "success": True,
        "data": reports_list
    }
