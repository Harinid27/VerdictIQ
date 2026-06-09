from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection

router = APIRouter(prefix="/api/agent2", tags=["Agent 2 Courtroom Strategy"])
logger = logging.getLogger(__name__)

# Helper to serialize MongoDB doc
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.post("/generate-strategy/{workspace_id}", status_code=status.HTTP_200_OK)
async def generate_strategy(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])

    # Always regenerate strategy fresh on every POST call (ensures new evidence is included)
    logger.info(f"Agent 2 Route: Regenerating strategy for workspace: {workspace_id}")
    from app.routes.agent1_routes import analyze_workspace_evidence
    await analyze_workspace_evidence(workspace_id, current_user)

    agent2_collection = get_collection("agent2_strategy")
    agent2_doc = await agent2_collection.find_one({"workspace_id": workspace_id})
        
    if not agent2_doc:
        raise HTTPException(
            status_code=400,
            detail="Unified Agent 3 intelligence report must be generated first. Structured context unavailable."
        )

    arg_priorities = agent2_doc.get("argument_priorities", {})
    lawyer_side = agent2_doc.get("lawyer_side", "Plaintiff")

    response_strategy = {
        "workspace_id": workspace_id,
        "lawyer_side": lawyer_side,
        "strongest_arguments": arg_priorities.get("strongest_arguments", []),
        "moderate_arguments": arg_priorities.get("moderate_arguments", []),
        "risky_arguments": arg_priorities.get("risky_arguments", []),
        "opponent_counterarguments": [
            {
                "claim_id": oc.get("claim_id"),
                "attack_vector": oc.get("attack_vector"),
                "explanation": oc.get("explanation")
            } for oc in agent2_doc.get("opponent_counterarguments", [])
        ],
        "rebuttal_strategies": [
            {
                "counterargument_targeted": rs.get("counterargument_targeted"),
                "rebuttal_narrative": rs.get("rebuttal_narrative")
            } for rs in agent2_doc.get("rebuttal_strategies", [])
        ],
        "courtroom_risks": agent2_doc.get("courtroom_risks", []),
        "evidence_utilization_strategy": agent2_doc.get("evidence_utilization_strategy", []),
        "strategic_recommendations": agent2_doc.get("strategic_recommendations", []),
        "prepared_for_agent3": True
    }

    return {
        "success": True,
        "message": "Agent 2 courtroom strategy loaded from unified intelligence engine",
        "strategy": response_strategy
    }

@router.get("/results/{workspace_id}")
async def get_agent2_results(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])

    # 1. Fetch Agent 2 strategy results from agent2_strategy collection
    agent2_collection = get_collection("agent2_strategy")
    doc = await agent2_collection.find_one({"workspace_id": workspace_id})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Agent 2 strategy not found. Run strategy generation first."
        )

    arg_priorities = doc.get("argument_priorities", {})

    # 2. Return strategy results matching the output format
    return {
        "workspace_id": workspace_id,
        "lawyer_side": doc.get("lawyer_side", "Plaintiff"),
        "strongest_arguments": arg_priorities.get("strongest_arguments", []),
        "moderate_arguments": arg_priorities.get("moderate_arguments", []),
        "risky_arguments": arg_priorities.get("risky_arguments", []),
        "opponent_counterarguments": [
            {
                "claim_id": oc.get("claim_id"),
                "attack_vector": oc.get("attack_vector"),
                "explanation": oc.get("explanation")
            } for oc in doc.get("opponent_counterarguments", [])
        ],
        "rebuttal_strategies": [
            {
                "counterargument_targeted": rs.get("counterargument_targeted"),
                "rebuttal_narrative": rs.get("rebuttal_narrative")
            } for rs in doc.get("rebuttal_strategies", [])
        ],
        "courtroom_risks": doc.get("courtroom_risks", []),
        "evidence_utilization_strategy": doc.get("evidence_utilization_strategy", []),
        "strategic_recommendations": doc.get("strategic_recommendations", []),
        "prepared_for_agent3": True
    }
