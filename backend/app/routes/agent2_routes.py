from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.gemini_service import generate_courtroom_strategy

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

    # 1. Fetch Agent 0 structured context
    scc_collection = get_collection("structured_case_context")
    context_doc = await scc_collection.find_one({"workspace_id": workspace_id})
    
    # 2. Fetch Agent 1 analysis
    agent1_collection = get_collection("agent1_analysis")
    a1_doc = await agent1_collection.find_one({"workspace_id": workspace_id})

    # Return structured error response if either is missing
    if not context_doc or not a1_doc:
        return {
            "success": False,
            "message": "Evidence intelligence unavailable"
        }

    # Fetch workspaces meta details to get lawyer_side
    workspace_meta = await get_collection("workspaces").find_one({"workspace_id": workspace_id})
    if not workspace_meta:
        workspace_meta = {}
    
    # Merge lawyer side into structured context dictionary if it isn't already there
    context_data = dict(context_doc)
    context_data["lawyer_side"] = workspace_meta.get("lawyer_side") or context_doc.get("lawyer_side") or "Plaintiff"
    context_data["client_name"] = workspace_meta.get("client_name") or "Client"
    context_data["opposing_party"] = workspace_meta.get("opposing_party") or "Opponent"
    context_data["case_description"] = workspace_meta.get("case_description") or ""

    # 3. Call Gemini to simulate courtroom strategy
    try:
        strategy_result = await generate_courtroom_strategy(context_data, a1_doc)
    except Exception as e:
        logger.error(f"Failed to generate Agent 2 strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 2 courtroom strategy execution failed: {e}"
        )

    # 4. Formulate the document to be saved in agent2_strategy
    lawyer_side = context_data["lawyer_side"]
    arg_priorities = strategy_result.get("argument_priorities", {})
    
    agent2_doc = {
        "workspace_id": workspace_id,
        "lawyer_side": lawyer_side,
        "lawyer_arguments": strategy_result.get("lawyer_arguments", []),
        "opponent_counterarguments": strategy_result.get("opponent_counterarguments", []),
        "rebuttal_strategies": strategy_result.get("rebuttal_strategies", []),
        "courtroom_risks": strategy_result.get("courtroom_risks", []),
        "strategic_recommendations": strategy_result.get("strategic_recommendations", []),
        "argument_priorities": arg_priorities,
        "evidence_utilization_strategy": strategy_result.get("evidence_utilization_strategy", []),
        "prepared_for_agent3": True,
        "generated_at": datetime.utcnow()
    }

    # 5. Save/Update in MongoDB agent2_strategy collection
    agent2_collection = get_collection("agent2_strategy")
    await agent2_collection.update_one(
        {"workspace_id": workspace_id},
        {"$set": agent2_doc},
        upsert=True
    )

    # 6. Format output JSON matching expectations
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
            } for oc in agent2_doc["opponent_counterarguments"]
        ],
        "rebuttal_strategies": [
            {
                "counterargument_targeted": rs.get("counterargument_targeted"),
                "rebuttal_narrative": rs.get("rebuttal_narrative")
            } for rs in agent2_doc["rebuttal_strategies"]
        ],
        "courtroom_risks": agent2_doc["courtroom_risks"],
        "evidence_utilization_strategy": agent2_doc["evidence_utilization_strategy"],
        "strategic_recommendations": agent2_doc["strategic_recommendations"],
        "prepared_for_agent3": True
    }

    return {
        "success": True,
        "message": "Agent 2 courtroom strategy generated",
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
