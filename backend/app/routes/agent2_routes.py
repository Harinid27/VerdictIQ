from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.gemini_service import generate_courtroom_strategy
from app.nodes.save_results import save_results_node

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

    logger.info(f"Agent 2 Route: Generating strategy for workspace: {workspace_id}")
    
    # 1. Fetch Agent 0 and Agent 1 outputs
    agent0_doc = await get_collection("structured_case_context").find_one({"workspace_id": workspace_id})
    agent1_doc = await get_collection("agent1_analysis").find_one({"workspace_id": workspace_id})
    
    if not agent0_doc or not agent1_doc:
        raise HTTPException(
            status_code=400,
            detail="Structured case context (Agent 0) and Evidence audit (Agent 1) must be ready first."
        )

    # 2. Call Gemini courtroom strategy engine
    try:
        strategy_result = await generate_courtroom_strategy(agent0_doc, agent1_doc)
    except Exception as e:
        logger.error(f"Failed to generate Agent 2 strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 2 strategy generation failed: {e}"
        )

    # 3. Persist strategy
    try:
        state = {
            "workspace_id": workspace_id,
            "agent0_output": agent0_doc,
            "agent1_output": agent1_doc,
            "agent2_output": strategy_result
        }
        await save_results_node(state)
    except Exception as e:
        logger.error(f"Failed to save Agent 2 strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist strategy: {e}"
        )

    agent2_collection = get_collection("agent2_strategy")
    agent2_doc = await agent2_collection.find_one({"workspace_id": workspace_id})

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
        "adversarial_simulations": agent2_doc.get("adversarial_simulations", []),
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
        "adversarial_simulations": doc.get("adversarial_simulations", []),
        "prepared_for_agent3": True
    }
