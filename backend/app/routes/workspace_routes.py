from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, Form, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Optional
from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.utils.cloudinary_helper import upload_file_to_cloudinary, delete_file_from_cloudinary
from app.utils.text_extractor import extract_text_from_file

router = APIRouter(prefix="/api/workspace", tags=["Workspaces"])

# Helper to serialize MongoDB doc
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_workspace(case_data: dict, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]

    workspace_id = case_data.get("id") or case_data.get("workspace_id")
    if not workspace_id:
        workspace_id = str(ObjectId())

    # Map name vs case_title, etc.
    case_title = case_data.get("case_title") or case_data.get("name") or "Unnamed Case"
    case_type = case_data.get("case_type") or case_data.get("caseType") or "General Dispute"
    lawyer_side = case_data.get("lawyer_side") or case_data.get("lawyerSide") or "Plaintiff"
    
    client_name = case_data.get("client_name") or case_data.get("client") or "Client"
    opposing_party = case_data.get("opposing_party") or case_data.get("opposingParty") or "Opponent"
    case_description = case_data.get("case_description") or case_data.get("description") or ""
    objectives = case_data.get("objectives") or case_data.get("claims") or ""
    expected_outcome = case_data.get("expected_outcome") or case_data.get("expectedOutcome") or ""
    concerns = case_data.get("concerns") or ""

    # 1. Save in workspaces collection (Agent 0 requirement)
    workspace_doc = {
        "workspace_id": workspace_id,
        "case_title": case_title,
        "case_type": case_type,
        "lawyer_side": lawyer_side,
        "client_name": client_name,
        "opposing_party": opposing_party,
        "case_description": case_description,
        "objectives": objectives,
        "expected_outcome": expected_outcome,
        "concerns": concerns,
        "created_by": user_email,
        "created_at": datetime.utcnow()
    }
    
    workspaces_collection = get_collection("workspaces")
    # Clean insert by converting workspace_id to ObjectId if it fits, else use string
    try:
        workspace_doc["_id"] = ObjectId(workspace_id)
    except Exception:
        workspace_doc["_id"] = workspace_id
        
    await workspaces_collection.insert_one(workspace_doc)

    # 2. Save in cases collection (Existing app compatibility)
    case_doc = {
        "_id": workspace_doc["_id"],
        "name": case_title,
        "caseType": case_type,
        "lawyerSide": lawyer_side,
        "lastUpdated": "Just now",
        "riskLevel": case_data.get("riskLevel") or "Medium",
        "evidenceCount": case_data.get("evidenceCount") or 0,
        "status": "Pre-Trial Audit",
        "client": client_name,
        "opposingParty": opposing_party,
        "incidentDate": case_data.get("incidentDate") or datetime.utcnow().strftime("%Y-%m-%d"),
        "user_id": user_id,
        "created_by": user_email,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    cases_collection = get_collection("cases")
    await cases_collection.insert_one(case_doc)

    return {
        "success": True,
        "message": "Workspace created successfully",
        "workspace_id": workspace_id,
        "workspace": serialize_mongo_doc(workspace_doc)
    }

@router.post("/upload-evidence")
async def upload_evidence(
    file: UploadFile = FastAPIFile(...),
    workspace_id: str = Form(...),
    evidence_type: str = Form(...),
    description: str = Form(...),
    related_claim: Optional[str] = Form(None),
    importance_level: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]

    # 1. Read file buffer
    try:
        file_bytes = await file.read()
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to read file stream: {e}"
        }

    # 2. Upload to Cloudinary
    upload_res = upload_file_to_cloudinary(file_bytes, file.filename)
    
    # 3. Extract file text contents (uses our updated text_extractor)
    extracted_text = extract_text_from_file(file_bytes, file.filename, file.content_type)

    # 4. Save in evidence_files collection (Agent 0 requirement)
    evidence_file_doc = {
        "workspace_id": workspace_id,
        "file_url": upload_res["secure_url"],
        "file_name": file.filename,
        "evidence_type": evidence_type,
        "description": description,
        "related_claim": related_claim or "",
        "importance_level": importance_level,
        "uploaded_at": datetime.utcnow()
    }
    
    try:
        evidence_files_collection = get_collection("evidence_files")
        result = await evidence_files_collection.insert_one(evidence_file_doc)
        file_id = str(result.inserted_id)
        evidence_file_doc["_id"] = file_id
        
        # 5. Dual write to evidence collection (Existing app compatibility)
        evidence_doc = {
            "workspace_id": workspace_id,
            "file_name": file.filename,
            "file_url": upload_res["secure_url"],
            "public_id": upload_res["public_id"],
            "evidence_type": evidence_type,
            "description": description,
            "importance_level": importance_level,
            "extracted_text": extracted_text, # legacy field
            "uploaded_by": user_email,
            "user_id": user_id,
            "uploaded_at": datetime.utcnow()
        }
        # Use matching custom id for the legacy doc if possible
        evidence_doc["_id"] = result.inserted_id
        await get_collection("evidence").insert_one(evidence_doc)

        return {
            "success": True,
            "message": "Evidence uploaded successfully",
            "file_id": file_id,
            "file_url": upload_res["secure_url"],
            "data": serialize_mongo_doc(evidence_file_doc)
        }
    except Exception as e:
        # Cleanup Cloudinary on DB write failure
        delete_file_from_cloudinary(upload_res["public_id"])
        return {
            "success": False,
            "message": f"Upload failed: database write failed ({e})"
        }

@router.get("/{workspace_id}/structured-context")
async def get_structured_context(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # 1. Fetch structured context from structured_case_context collection
    scc_collection = get_collection("structured_case_context")
    context_doc = await scc_collection.find_one({"workspace_id": workspace_id})
    if not context_doc:
        raise HTTPException(status_code=404, detail="Structured context not found for this workspace. Please run Agent 0 processing first.")

    # 2. Compile response in output format
    # Let's retrieve workspaces and evidence files metadata
    workspace = await get_collection("workspaces").find_one({"workspace_id": workspace_id})
    if not workspace:
        workspace = {}

    evidence_files_cursor = get_collection("evidence_files").find({"workspace_id": workspace_id})
    evidence_files = await evidence_files_cursor.to_list(length=100)
    
    # Pull in the AI summaries from document_extractions if available
    evidence_summaries = []
    for ef in evidence_files:
        ef_id = str(ef["_id"])
        # Find document extraction
        doc_ext = await get_collection("document_extractions").find_one({
            "workspace_id": workspace_id,
            "file_id": ef_id
        })
        ai_summary = doc_ext.get("ai_summary", "") if doc_ext else ""
        if not ai_summary:
            ai_summary = ef.get("description", "No summary available.")
            
        evidence_summaries.append({
            "file_name": ef.get("file_name"),
            "ai_summary": ai_summary,
            "importance_level": ef.get("importance_level")
        })

    legal_context = {
        "case_title": workspace.get("case_title", ""),
        "case_type": workspace.get("case_type", ""),
        "lawyer_side": workspace.get("lawyer_side", ""),
        "client_name": workspace.get("client_name", ""),
        "opposing_party": workspace.get("opposing_party", "")
    }

    return {
        "workspace_id": workspace_id,
        "case_summary": context_doc.get("case_summary", ""),
        "claims": context_doc.get("claims", []),
        "timeline": context_doc.get("timeline", []),
        "key_entities": context_doc.get("key_entities", []),
        "evidence_summary": evidence_summaries,
        "legal_context": legal_context,
        "objectives": context_doc.get("objectives", []),
        "concerns": context_doc.get("concerns", []),
        "prepared_for_agents": True
    }
