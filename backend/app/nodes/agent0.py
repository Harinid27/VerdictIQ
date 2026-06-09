import logging
import requests
from datetime import datetime
from typing import Dict, Any

from app.state import VerdictState
from app.database import get_collection
from app.services.gemini_service import analyze_document_text, generate_structured_case_context

logger = logging.getLogger(__name__)

async def agent0_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: agent0_node
    Role: Intake & Structuring Agent
    Responsibilities:
      - Structures raw case metadata and evidence files.
      - Extracts and analyzes text for each evidence document.
      - Synthesizes claims, timeline, entities, and evidence relationships.
    """
    workspace_id = state.get("workspace_id")
    case_context = state.get("case_context") or {}
    workspace_meta = case_context.get("workspace_meta") or {}
    evidence_files = case_context.get("evidence_files") or []

    logger.info(f"LangGraph: Starting agent0_node for workspace_id: {workspace_id}")

    document_analyses = []
    document_extractions_collection = get_collection("document_extractions")

    for ef in evidence_files:
        file_id = ef.get("_id")
        file_name = ef.get("file_name")
        file_url = ef.get("file_url")
        evidence_type = ef.get("evidence_type")
        description = ef.get("description", "")
        importance_level = ef.get("importance_level", "Important")

        # 1. Check if document has already been extracted/analyzed in the database
        doc_ext = None
        if file_id:
            doc_ext = await document_extractions_collection.find_one({
                "workspace_id": workspace_id,
                "file_id": file_id
            })

        extracted_text = ""
        if doc_ext:
            extracted_text = doc_ext.get("raw_text", "")

        # 2. Extract text if not cached
        if not extracted_text:
            # Fallback to check legacy 'evidence' collection
            legacy_doc = None
            if file_id:
                try:
                    from bson import ObjectId
                    legacy_doc = await get_collection("evidence").find_one({"_id": ObjectId(file_id)})
                except Exception:
                    legacy_doc = await get_collection("evidence").find_one({"_id": file_id})

            if legacy_doc and legacy_doc.get("extracted_text"):
                extracted_text = legacy_doc.get("extracted_text")
            else:
                try:
                    if file_url and not file_url.startswith("https://res.cloudinary.com/verdictiq/image/upload/mock_"):
                        res = requests.get(file_url, timeout=10)
                        if res.status_code == 200:
                            from app.utils.text_extractor import extract_text_from_file
                            # Attempt to get Content-Type
                            ct = res.headers.get("content-type", "")
                            extracted_text = extract_text_from_file(res.content, file_name, ct)
                except Exception as ex:
                    logger.error(f"Failed to fetch file stream from URL: {file_url}. Exception: {ex}")

            if not extracted_text:
                extracted_text = f"[Evidence document content for file {file_name}. Description provided: {description}]"

        # 3. Call Gemini to analyze single document text (uses PromptTemplate under-the-hood)
        try:
            analysis = await analyze_document_text(
                text=extracted_text,
                filename=file_name,
                doc_description=description,
                lawyer_side=workspace_meta.get("lawyer_side")
            )
        except Exception as ex:
            logger.error(f"Error during single doc analysis for {file_name}: {ex}")
            analysis = {
                "extracted_entities": {
                    "people": [], "organizations": [], "locations": [],
                    "dates": [], "financial_amounts": [], "legal_references": []
                },
                "extracted_dates": [],
                "ai_summary": f"Failed to run Gemini analysis for {file_name}."
            }

        # 4. Save/Update cache in document_extractions
        if file_id:
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

    # 5. Synthesize all analyses into a case-wide structured context
    try:
        structured_context = await generate_structured_case_context(
            workspace_meta=workspace_meta,
            document_analyses=document_analyses
        )
    except Exception as ex:
        logger.error(f"Error generating case-wide structured context: {ex}")
        raise ValueError(f"Failed to generate structured context from Gemini: {ex}")

    # 6. Format evidence summary for final output
    evidence_summaries = []
    for da in document_analyses:
        evidence_summaries.append({
            "file_name": da.get("file_name"),
            "ai_summary": da.get("ai_summary"),
            "importance_level": da.get("importance_level")
        })

    legal_context = {
        "case_title": workspace_meta.get("case_title"),
        "case_type": workspace_meta.get("case_type"),
        "lawyer_side": workspace_meta.get("lawyer_side"),
        "client_name": workspace_meta.get("client_name"),
        "opposing_party": workspace_meta.get("opposing_party")
    }

    final_structured_output = {
        "workspace_id": workspace_id,
        "case_summary": structured_context.get("case_summary", ""),
        "claims": structured_context.get("claims", []),
        "timeline": structured_context.get("timeline", []),
        "key_entities": structured_context.get("key_entities", []),
        "evidence_relationships": structured_context.get("evidence_relationships", []),
        "evidence_summary": evidence_summaries,
        "legal_context": legal_context,
        "objectives": structured_context.get("objectives", []),
        "concerns": structured_context.get("concerns", []),
        "prepared_for_agents": True
    }

    # Return updated state
    return {
        **state,
        "agent0_output": final_structured_output,
        "current_stage": "agent0_completed"
    }
