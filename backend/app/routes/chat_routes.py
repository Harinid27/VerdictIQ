from fastapi import APIRouter, Depends, status, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any
import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv

from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.services.rag_service import RAGService
from app.services.gemini_service import run_chat_agent

# Ensure environment variables are loaded immediately
load_dotenv()

router = APIRouter(prefix="/api/chat", tags=["AI Conversations"])
debug_router = APIRouter(prefix="/api/debug", tags=["Diagnostics & Debugging"])
logger = logging.getLogger(__name__)

# Initialize Gemini SDK
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IS_MOCK_GEMINI = not GEMINI_API_KEY or GEMINI_API_KEY == "placeholder_key"

if GEMINI_API_KEY and not IS_MOCK_GEMINI:
    genai.configure(api_key=GEMINI_API_KEY)

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.get("/history/{workspace_id}")
async def get_chat_history(workspace_id: str, current_user: dict = Depends(get_current_user)):
    chats_collection = get_collection("workspace_chats")
    cursor = chats_collection.find({"workspace_id": workspace_id}).sort("timestamp", 1)
    history = await cursor.to_list(length=500)
    return {
        "success": True,
        "data": [serialize_mongo_doc(item) for item in history]
    }

@router.post("/ask/{workspace_id}")
async def ask_workspace_agent(
    workspace_id: str,
    payload: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    try:
        user_email = current_user["email"]
        question = payload.get("message")
        if not question:
            raise HTTPException(status_code=400, detail="Message field is required")

        logger.info(f"Chat Endpoint: Loading workspace retrieval for ID: {workspace_id}")
        
        # 1. Gather Agent 0 + Agent 3 case data for LLM context
        # A. Workspace metadata
        workspaces_collection = get_collection("workspaces")
        workspace = await workspaces_collection.find_one({"workspace_id": workspace_id})
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # B. Structured case context (Agent 0)
        scc_collection = get_collection("structured_case_context")
        context_doc = await scc_collection.find_one({"workspace_id": workspace_id})
        
        # C. Synthesis Report (Agent 3)
        agent3_collection = get_collection("agent3_final_reports")
        a3_doc = await agent3_collection.find_one({"workspace_id": workspace_id})

        # Make sure we have analysis ready
        if not a3_doc:
            raise HTTPException(
                status_code=400,
                detail="Chat is locked. Please run the AI Agent pipeline to generate the case report first."
            )

        # 2. Retrieve document context via RAG
        logger.info(f"Chat Endpoint: Querying RAG context for question: '{question[:50]}'")
        rag_context = await RAGService.retrieve_relevant_context(
            query=question,
            workspace_id=workspace_id,
            top_k=3
        )

        # Fetch recent message history
        chats_collection = get_collection("workspace_chats")
        cursor = chats_collection.find({"workspace_id": workspace_id}).sort("timestamp", -1).limit(10)
        history_docs = await cursor.to_list(length=10)
        history_docs.reverse()
        
        formatted_history = []
        for h in history_docs:
            role = "User" if h["sender"] == "user" else h.get("agent_name", "AI Agent")
            formatted_history.append(f"{role}: {h['text']}")
        history_str = "\n".join(formatted_history)

        # 3. Call Gemini Chat Agent (Agent 3 Chatbot)
        logger.info(f"Chat Endpoint: Executing Gemini call for workspace: {workspace_id}")
        
        agent4_res = await run_chat_agent(
            case_summary=context_doc.get("case_summary", "") if context_doc else "",
            claims=context_doc.get("claims", []) if context_doc else [],
            evidence_audit={},  # Removed Agent 1
            courtroom_strategy={},  # Removed Agent 2
            final_report=a3_doc or {},
            rag_context=rag_context,
            chat_history=history_str,
            question=question,
            lawyer_side=workspace.get("lawyer_side")
        )

        # Format correct Agent Chatbot response
        agent_name = agent4_res.get("agent_name") or "Agent 3 Synthesis Report Agent"
        reply_text = f"[{agent_name}]\n{agent4_res['answer']}"
        
        # Save User message
        user_msg_doc = {
            "workspace_id": workspace_id,
            "sender": "user",
            "text": question,
            "timestamp": datetime.utcnow()
        }
        await chats_collection.insert_one(user_msg_doc)

        # Save Agent response
        agent_msg_doc = {
            "workspace_id": workspace_id,
            "sender": "agent",
            "agent_name": agent_name,
            "text": reply_text,
            "timestamp": datetime.utcnow()
        }
        await chats_collection.insert_one(agent_msg_doc)

        return {
            "success": True,
            "data": serialize_mongo_doc(agent_msg_doc)
        }
    except Exception as e:
        logger.exception("Chat Agent Error")
        return {
            "success": False,
            "error_type": str(type(e).__name__),
            "error_message": str(e),
            "message": str(e)
        }

@debug_router.get("/workspace/{workspace_id}")
async def get_workspace_debug(workspace_id: str, current_user: dict = Depends(get_current_user)):
    """
    GET /api/debug/workspace/{workspace_id}
    Returns availability of agents, history size, context size, and doc count.
    """
    try:
        logger.info(f"Debug: Fetching info for workspace_id: {workspace_id}")
        
        # 1. Agent 0 context
        scc_collection = get_collection("structured_case_context")
        context_doc = await scc_collection.find_one({"workspace_id": workspace_id})
        agent0_avail = bool(context_doc)
        
        # 2. Agent 1 audit
        agent1_collection = get_collection("agent1_analysis")
        a1_doc = await agent1_collection.find_one({"workspace_id": workspace_id})
        agent1_avail = bool(a1_doc)
        
        # 3. Agent 2 strategy
        agent2_collection = get_collection("agent2_strategy")
        a2_doc = await agent2_collection.find_one({"workspace_id": workspace_id})
        agent2_avail = bool(a2_doc)
        
        # 4. Agent 3 report
        agent3_collection = get_collection("agent3_final_reports")
        a3_doc = await agent3_collection.find_one({"workspace_id": workspace_id})
        agent3_avail = bool(a3_doc)
        
        # 5. Chats
        chats_collection = get_collection("workspace_chats")
        chat_count = await chats_collection.count_documents({"workspace_id": workspace_id})
        
        # 6. Context size calculation
        context_size = 0
        if context_doc:
            context_size += len(context_doc.get("case_summary", ""))
            context_size += len(json.dumps(context_doc.get("claims", [])))
            context_size += len(json.dumps(context_doc.get("timeline", [])))
            
        # 7. Document count
        evidence_collection = get_collection("evidence")
        doc_count = await evidence_collection.count_documents({"workspace_id": workspace_id})
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "agent0_available": agent0_avail,
            "agent1_available": agent1_avail,
            "agent2_available": agent2_avail,
            "agent3_available": agent3_avail,
            "chat_history_size": chat_count,
            "context_size_chars": context_size,
            "document_count": doc_count
        }
    except Exception as e:
        logger.exception("Debug Endpoint Error")
        return {
            "success": False,
            "error_type": str(type(e).__name__),
            "error_message": str(e)
        }

@debug_router.post("/test-chat/{workspace_id}")
async def test_chat_diagnostic(
    workspace_id: str,
    payload: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """
    POST /api/debug/test-chat/{workspace_id}
    Returns diagnostic details: retrieved context, generated prompt, token estimate, response, and parsing.
    """
    try:
        question = payload.get("message")
        if not question:
            raise HTTPException(status_code=400, detail="Message field is required")
            
        # 1. RAG retrieval
        logger.info(f"Diagnostic: Querying RAG context for question: {question[:50]}")
        retrieved_context = await RAGService.retrieve_relevant_context(question, workspace_id, top_k=3)
        
        # 2. Gather context
        workspaces_collection = get_collection("workspaces")
        workspace = await workspaces_collection.find_one({"workspace_id": workspace_id})
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        context_doc = await get_collection("structured_case_context").find_one({"workspace_id": workspace_id})
        a1_doc = await get_collection("agent1_analysis").find_one({"workspace_id": workspace_id})
        a2_doc = await get_collection("agent2_strategy").find_one({"workspace_id": workspace_id})
        a3_doc = await get_collection("agent3_final_reports").find_one({"workspace_id": workspace_id})
        
        # Format chat history
        chats_collection = get_collection("workspace_chats")
        cursor = chats_collection.find({"workspace_id": workspace_id}).sort("timestamp", -1).limit(5)
        history_docs = await cursor.to_list(length=5)
        history_docs.reverse()
        
        formatted_history = []
        for h in history_docs:
            role = "User" if h["sender"] == "user" else h.get("agent_name", "AI Agent")
            formatted_history.append(f"{role}: {h['text']}")
        history_str = "\n".join(formatted_history)
        
        # 3. Construct prompt
        from app.services.gemini_service import LEGAL_CHAT_PROMPT, get_lawyer_side_prefix
        prefix = get_lawyer_side_prefix(workspace.get("lawyer_side"))
        prompt = LEGAL_CHAT_PROMPT.format(
            lawyer_side_prefix=prefix,
            case_summary=context_doc.get("case_summary", "") if context_doc else "",
            claims=json.dumps(context_doc.get("claims", []) if context_doc else []),
            evidence_audit=json.dumps(a1_doc or {}),
            courtroom_strategy=json.dumps(a2_doc or {}),
            final_report=json.dumps(a3_doc or {}),
            rag_context=retrieved_context or "No context retrieved.",
            chat_history=history_str or "No history.",
            question=question
        )
        
        token_estimate = len(prompt) // 4
        
        # 4. Invoke Gemini (if not mock)
        gemini_response = ""
        parsing_result = {}
        
        from app.services.gemini_service import IS_MOCK_GEMINI, validate_and_parse_json, Agent4Output, GEMINI_MODEL, generate_content_with_fallback
        if IS_MOCK_GEMINI:
            gemini_response = '{"answer": "Mock diagnostic reply", "supporting_context": [], "confidence": "High"}'
            parsing_result = json.loads(gemini_response)
        else:
            response = generate_content_with_fallback(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            gemini_response = response.text.strip()
            parsing_result = validate_and_parse_json(gemini_response, Agent4Output)
            
        return {
            "success": True,
            "retrieved_context": retrieved_context,
            "generated_prompt": prompt,
            "token_estimate": token_estimate,
            "gemini_response_raw": gemini_response,
            "parsing_result": parsing_result
        }
    except Exception as e:
        logger.exception("Chat Diagnostic Endpoint Error")
        return {
            "success": False,
            "error_type": str(type(e).__name__),
            "error_message": str(e)
        }
