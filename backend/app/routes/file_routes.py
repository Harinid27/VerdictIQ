from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, Form, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List
from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.utils.cloudinary_helper import upload_file_to_cloudinary, delete_file_from_cloudinary
from app.utils.text_extractor import extract_text_from_file

router = APIRouter(prefix="/api/files", tags=["Files & Evidence"])

# Helper to serialize MongoDB doc
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    doc["_id"] = str(doc["_id"])
    return doc

@router.post("/upload")
async def upload_evidence_file(
    file: UploadFile = FastAPIFile(...),
    workspace_id: str = Form(...),
    evidence_type: str = Form(...),
    description: str = Form(...),
    importance_level: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]

    # Read file buffer
    try:
        file_bytes = await file.read()
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to read file stream: {e}"
        }

    # Upload to Cloudinary
    upload_res = upload_file_to_cloudinary(file_bytes, file.filename)
    
    # Extract file text contents
    extracted_text = extract_text_from_file(file_bytes, file.filename, file.content_type)

    # Prepare document for MongoDB
    evidence_doc = {
        "workspace_id": workspace_id,
        "file_name": file.filename,
        "file_url": upload_res["secure_url"],
        "public_id": upload_res["public_id"],
        "evidence_type": evidence_type,
        "description": description,
        "importance_level": importance_level,
        "extracted_text": extracted_text,
        "uploaded_by": user_email,
        "user_id": user_id,
        "uploaded_at": datetime.utcnow()
    }

    # Insert into MongoDB evidence collection
    try:
        evidence_collection = get_collection("evidence")
        result = await evidence_collection.insert_one(evidence_doc)
        evidence_doc["_id"] = str(result.inserted_id)
        
        # Trigger RAG Indexing
        try:
            from app.services.rag_service import RAGService
            await RAGService.index_document(
                file_id=evidence_doc["_id"],
                text=extracted_text,
                workspace_id=workspace_id,
                file_name=file.filename,
                evidence_type=evidence_type,
                importance_level=importance_level
            )
        except Exception as rag_err:
            import logging
            logging.getLogger(__name__).error(f"RAG Indexing failed on upload: {rag_err}")

        return {
            "success": True,
            "file_url": upload_res["secure_url"],
            "message": "Uploaded successfully",
            "data": serialize_mongo_doc(evidence_doc)
        }
    except Exception as e:
        # Cleanup Cloudinary on failure
        delete_file_from_cloudinary(upload_res["public_id"])
        return {
            "success": False,
            "message": f"Upload failed: database write failed ({e})"
        }

@router.get("/{workspace_id}")
async def get_workspace_files(
    workspace_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    evidence_collection = get_collection("evidence")

    # Strict user and workspace isolation
    query = {
        "workspace_id": workspace_id,
        "user_id": user_id
    }
    
    cursor = evidence_collection.find(query).sort("uploaded_at", -1)
    docs = await cursor.to_list(length=500)
    return {
        "success": True,
        "data": [serialize_mongo_doc(doc) for doc in docs]
    }

@router.delete("/{file_id}")
async def delete_evidence_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    evidence_collection = get_collection("evidence")

    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file ID format")

    # Verify file ownership
    existing_file = await evidence_collection.find_one({"_id": oid, "user_id": user_id})
    if not existing_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from Cloudinary using public_id
    cloudinary_deleted = delete_file_from_cloudinary(existing_file.get("public_id"))

    # Delete from MongoDB
    await evidence_collection.delete_one({"_id": oid, "user_id": user_id})

    return {
        "success": True,
        "message": "File deleted successfully",
        "cloudinary_deleted": cloudinary_deleted
    }
