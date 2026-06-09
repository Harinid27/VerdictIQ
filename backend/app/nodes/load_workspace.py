import logging
from datetime import datetime
from bson import ObjectId
from typing import Dict, Any

from app.state import VerdictState
from app.database import get_collection

logger = logging.getLogger(__name__)

async def load_workspace_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: load_workspace_node
    Fetches the workspace metadata and related evidence documents from MongoDB,
    sets the initial state context, and prepares it for processing by Agent 0.
    """
    workspace_id = state.get("workspace_id")
    logger.info(f"LangGraph: Starting load_workspace_node for workspace_id: {workspace_id}")

    if not workspace_id:
        raise ValueError("workspace_id is missing from graph state.")

    # 1. Fetch workspace data from workspaces collection
    workspaces_collection = get_collection("workspaces")
    workspace = await workspaces_collection.find_one({"workspace_id": workspace_id})
    
    if not workspace:
        # Check from 'cases' collection as fallback
        cases_collection = get_collection("cases")
        # Try finding by ObjectId or string id
        try:
            oid = ObjectId(workspace_id)
            case_info = await cases_collection.find_one({"_id": oid})
        except Exception:
            case_info = await cases_collection.find_one({"_id": workspace_id})
            
        if not case_info:
            raise ValueError(f"Workspace/Case not found for ID: {workspace_id}")
            
        # Re-populate workspaces collection
        workspace = {
            "workspace_id": workspace_id,
            "case_title": case_info.get("name", "Unnamed Case"),
            "case_type": case_info.get("caseType", "General Dispute"),
            "lawyer_side": case_info.get("lawyerSide", "Plaintiff"),
            "client_name": case_info.get("client", "Client"),
            "opposing_party": case_info.get("opposingParty", "Opponent"),
            "case_description": case_info.get("description") or "",
            "objectives": case_info.get("claims") or "",
            "expected_outcome": case_info.get("expectedOutcome") or "",
            "concerns": case_info.get("concerns") or "",
            "created_by": case_info.get("created_by", "system"),
            "created_at": datetime.utcnow()
        }
        await workspaces_collection.insert_one(workspace)

    # 2. Fetch all evidence files uploaded to this workspace
    evidence_files_collection = get_collection("evidence_files")
    evidence_files_cursor = evidence_files_collection.find({"workspace_id": workspace_id})
    evidence_files = await evidence_files_cursor.to_list(length=100)

    # Fallback to legacy 'evidence' collection if empty
    if not evidence_files:
        evidence_cursor = get_collection("evidence").find({"workspace_id": workspace_id})
        legacy_evidence = await evidence_cursor.to_list(length=100)
        for le in legacy_evidence:
            ef_doc = {
                "workspace_id": workspace_id,
                "file_url": le.get("file_url"),
                "file_name": le.get("file_name"),
                "evidence_type": le.get("evidence_type"),
                "description": le.get("description", ""),
                "related_claim": le.get("related_claim", ""),
                "importance_level": le.get("importance_level", "Important"),
                "uploaded_at": le.get("uploaded_at", datetime.utcnow())
            }
            # Preserve matching ID
            ef_doc["_id"] = le["_id"]
            await evidence_files_collection.insert_one(ef_doc)
            evidence_files.append(ef_doc)

    # Serialize files to be JSON safe inside state
    serialized_files = []
    for f in evidence_files:
        file_doc = dict(f)
        if "_id" in file_doc:
            file_doc["_id"] = str(file_doc["_id"])
        if isinstance(file_doc.get("uploaded_at"), datetime):
            file_doc["uploaded_at"] = file_doc["uploaded_at"].isoformat()
        serialized_files.append(file_doc)

    lawyer_side = workspace.get("lawyer_side", "Plaintiff")

    # Construct the case context
    case_context = {
        "workspace_meta": {
            "case_title": workspace.get("case_title"),
            "case_type": workspace.get("case_type"),
            "lawyer_side": lawyer_side,
            "client_name": workspace.get("client_name"),
            "opposing_party": workspace.get("opposing_party"),
            "case_description": workspace.get("case_description"),
            "objectives": workspace.get("objectives"),
            "expected_outcome": workspace.get("expected_outcome"),
            "concerns": workspace.get("concerns")
        },
        "evidence_files": serialized_files
    }

    # Implement Hook for Future RAG Integration
    # RAG Hook: Can retrieve relevant contextual paragraphs and inject them here
    # from app.services.rag_service import RAGService
    # case_context["rag_context"] = RAGService.retrieve_relevant_context("query context", workspace_id)

    # Return updated state
    return {
        **state,
        "lawyer_side": lawyer_side,
        "case_context": case_context,
        "current_stage": "workspace_loaded"
    }
