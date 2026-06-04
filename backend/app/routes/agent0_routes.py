from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import requests
import logging

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.gemini_service import analyze_document_text, generate_structured_case_context

router = APIRouter(prefix="/api/agent0", tags=["Agent 0 Processing"])
logger = logging.getLogger(__name__)

# Helper to serialize MongoDB doc
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.post("/process/{workspace_id}", status_code=status.HTTP_200_OK)
async def process_workspace(workspace_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]

    # 1. Fetch workspace data from workspaces collection
    workspaces_collection = get_collection("workspaces")
    workspace = await workspaces_collection.find_one({"workspace_id": workspace_id})
    if not workspace:
        # Try checking from 'cases' collection as fallback
        cases_collection = get_collection("cases")
        try:
            oid = ObjectId(workspace_id)
            case_info = await cases_collection.find_one({"_id": oid, "user_id": user_id})
        except Exception:
            case_info = await cases_collection.find_one({"_id": workspace_id, "user_id": user_id})
            
        if not case_info:
            raise HTTPException(
                status_code=404, 
                detail="Workspace not found. Initialize workspace first."
            )
            
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
            "created_by": user_email,
            "created_at": datetime.utcnow()
        }
        await workspaces_collection.insert_one(workspace)

    # 2. Fetch all evidence files uploaded to this workspace
    evidence_files_collection = get_collection("evidence_files")
    evidence_files_cursor = evidence_files_collection.find({"workspace_id": workspace_id})
    evidence_files = await evidence_files_cursor.to_list(length=100)

    # Fallback: check legacy 'evidence' collection if no files found in evidence_files
    if not evidence_files:
        evidence_cursor = get_collection("evidence").find({"workspace_id": workspace_id, "user_id": user_id})
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
            # Preserve matching id
            ef_doc["_id"] = le["_id"]
            await evidence_files_collection.insert_one(ef_doc)
            evidence_files.append(ef_doc)

    document_analyses = []
    
    # 3. For each evidence file, fetch/extract text and run single-doc analysis
    document_extractions_collection = get_collection("document_extractions")
    
    for ef in evidence_files:
        file_id = str(ef["_id"])
        file_name = ef.get("file_name")
        file_url = ef.get("file_url")
        evidence_type = ef.get("evidence_type")
        description = ef.get("description", "")
        importance_level = ef.get("importance_level", "Important")

        # Check if already processed
        doc_ext = await document_extractions_collection.find_one({
            "workspace_id": workspace_id,
            "file_id": file_id
        })
        
        extracted_text = ""
        if doc_ext:
            extracted_text = doc_ext.get("raw_text", "")

        if not extracted_text:
            # Attempt to find pre-extracted text from the legacy evidence collection
            legacy_doc = await get_collection("evidence").find_one({"_id": ef["_id"]})
            if legacy_doc and legacy_doc.get("extracted_text"):
                extracted_text = legacy_doc.get("extracted_text")
            else:
                # Retrieve from URL or default fallback text
                try:
                    if file_url and not file_url.startswith("https://res.cloudinary.com/verdictiq/image/upload/mock_"):
                        res = requests.get(file_url, timeout=10)
                        if res.status_code == 200:
                            # Re-run text extraction from downloaded stream
                            from app.utils.text_extractor import extract_text_from_file
                            extracted_text = extract_text_from_file(res.content, file_name, res.headers.get("content-type", ""))
                except Exception as ex:
                    logger.error(f"Failed to fetch content from URL: {file_url}. Exception: {ex}")

            if not extracted_text:
                extracted_text = f"[Evidence document content for file {file_name}. Description provided: {description}]"

        # Call Gemini to analyze single document text
        try:
            analysis = await analyze_document_text(
                text=extracted_text, 
                filename=file_name, 
                doc_description=description
            )
        except Exception as ex:
            logger.error(f"Error analyzing document {file_name}: {ex}")
            analysis = {
                "extracted_entities": {"people": [], "organizations": [], "locations": [], "dates": [], "financial_amounts": [], "legal_references": []},
                "extracted_dates": [],
                "ai_summary": f"Failed to run Gemini analysis for {file_name}."
            }

        # Store in document_extractions
        extraction_doc = {
            "workspace_id": workspace_id,
            "file_id": file_id,
            "raw_text": extracted_text,
            "extracted_entities": analysis.get("extracted_entities", {}),
            "extracted_dates": analysis.get("extracted_dates", []),
            "ai_summary": analysis.get("ai_summary", "")
        }
        
        await document_extractions_collection.update_one(
            {"workspace_id": workspace_id, "file_id": file_id},
            {"$set": extraction_doc},
            upsert=True
        )

        document_analyses.append({
            "file_id": file_id,
            "file_name": file_name,
            "evidence_type": evidence_type,
            "description": description,
            "importance_level": importance_level,
            "ai_summary": analysis.get("ai_summary", ""),
            "extracted_entities": analysis.get("extracted_entities", {}),
            "extracted_dates": analysis.get("extracted_dates", [])
        })

    # 4. Synthesize all analyses into case wide structured context
    workspace_meta = {
        "case_title": workspace.get("case_title"),
        "case_type": workspace.get("case_type"),
        "lawyer_side": workspace.get("lawyer_side"),
        "client_name": workspace.get("client_name"),
        "opposing_party": workspace.get("opposing_party"),
        "case_description": workspace.get("case_description"),
        "objectives": workspace.get("objectives"),
        "expected_outcome": workspace.get("expected_outcome"),
        "concerns": workspace.get("concerns")
    }

    try:
        structured_context = await generate_structured_case_context(
            workspace_meta=workspace_meta, 
            document_analyses=document_analyses
        )
    except Exception as ex:
        logger.error(f"Error generating case-wide structured context: {ex}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate structured context from Gemini: {ex}"
        )

    # 5. Save structured context in structured_case_context collection
    scc_doc = {
        "workspace_id": workspace_id,
        "case_summary": structured_context.get("case_summary", ""),
        "claims": structured_context.get("claims", []),
        "timeline": structured_context.get("timeline", []),
        "key_entities": structured_context.get("key_entities", []),
        "evidence_relationships": structured_context.get("evidence_relationships", []),
        "objectives": structured_context.get("objectives", []),
        "concerns": structured_context.get("concerns", []),
        "generated_at": datetime.utcnow()
    }
    
    scc_collection = get_collection("structured_case_context")
    await scc_collection.update_one(
        {"workspace_id": workspace_id},
        {"$set": scc_doc},
        upsert=True
    )

    # 6. Format evidence summary for final JSON
    evidence_summaries = []
    for da in document_analyses:
        evidence_summaries.append({
            "file_name": da.get("file_name"),
            "ai_summary": da.get("ai_summary"),
            "importance_level": da.get("importance_level")
        })

    legal_context = {
        "case_title": workspace.get("case_title"),
        "case_type": workspace.get("case_type"),
        "lawyer_side": workspace.get("lawyer_side"),
        "client_name": workspace.get("client_name"),
        "opposing_party": workspace.get("opposing_party")
    }

    final_structured_output = {
        "workspace_id": workspace_id,
        "case_summary": scc_doc.get("case_summary"),
        "claims": scc_doc.get("claims"),
        "timeline": scc_doc.get("timeline"),
        "key_entities": scc_doc.get("key_entities"),
        "evidence_summary": evidence_summaries,
        "legal_context": legal_context,
        "objectives": scc_doc.get("objectives"),
        "concerns": scc_doc.get("concerns"),
        "prepared_for_agents": True
    }

    return {
        "success": True,
        "message": "Agent 0 processing completed",
        "workspace_id": workspace_id,
        "structured_context": final_structured_output
    }
