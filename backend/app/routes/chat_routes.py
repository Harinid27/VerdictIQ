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

# Ensure environment variables are loaded immediately
load_dotenv()

router = APIRouter(prefix="/api/chat", tags=["AI Conversations"])
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
    user_email = current_user["email"]
    question = payload.get("message")
    if not question:
        raise HTTPException(status_code=400, detail="Message field is required")

    # 1. Gather all case data for LLM context
    # A. Workspace metadata
    workspaces_collection = get_collection("workspaces")
    workspace = await workspaces_collection.find_one({"workspace_id": workspace_id})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # B. Structured case context (Agent 0)
    scc_collection = get_collection("structured_case_context")
    context_doc = await scc_collection.find_one({"workspace_id": workspace_id})
    
    # C. Auditing (Agent 1)
    agent1_collection = get_collection("agent1_analysis")
    a1_doc = await agent1_collection.find_one({"workspace_id": workspace_id})

    # D. Strategy (Agent 2)
    agent2_collection = get_collection("agent2_strategy")
    a2_doc = await agent2_collection.find_one({"workspace_id": workspace_id})

    # E. Synthesis Report (Agent 3)
    agent3_collection = get_collection("agent3_final_reports")
    a3_doc = await agent3_collection.find_one({"workspace_id": workspace_id})

    # Make sure we have analysis ready
    if not a3_doc:
        raise HTTPException(
            status_code=400,
            detail="Chat is locked. Please run the AI Agent pipeline to generate the case report first."
        )

    # 2. Build contextual prompt for the routing agent
    context_data = {
        "workspace": {
            "title": workspace.get("case_title"),
            "type": workspace.get("case_type"),
            "side": workspace.get("lawyer_side"),
            "client": workspace.get("client_name"),
            "opponent": workspace.get("opposing_party"),
            "description": workspace.get("case_description"),
            "objectives": workspace.get("objectives"),
            "concerns": workspace.get("concerns")
        },
        "structured_context": {
            "summary": context_doc.get("case_summary") if context_doc else "",
            "timeline": context_doc.get("timeline") if context_doc else [],
            "key_entities": context_doc.get("key_entities") if context_doc else [],
            "claims": context_doc.get("claims") if context_doc else []
        },
        "evidence_audit": {
            "strong_evidence": a1_doc.get("strong_evidence") if a1_doc else [],
            "weak_evidence": a1_doc.get("weak_evidence") if a1_doc else [],
            "missing_evidence": a1_doc.get("missing_evidence") if a1_doc else [],
            "loopholes": a1_doc.get("loopholes") if a1_doc else [],
            "contradictions": a1_doc.get("contradictions") if a1_doc else []
        },
        "courtroom_strategy": {
            "lawyer_arguments": a2_doc.get("lawyer_arguments") if a2_doc else [],
            "opponent_counterarguments": a2_doc.get("opponent_counterarguments") if a2_doc else [],
            "rebuttal_strategies": a2_doc.get("rebuttal_strategies") if a2_doc else [],
            "courtroom_risks": a2_doc.get("courtroom_risks") if a2_doc else [],
            "recommendations": a2_doc.get("strategic_recommendations") if a2_doc else []
        },
        "final_report": {
            "executive_summary": a3_doc.get("executive_summary") if a3_doc else "",
            "case_strength": a3_doc.get("case_strength") if a3_doc else "",
            "legal_references": a3_doc.get("legal_references") if a3_doc else [],
            "final_assessment": a3_doc.get("final_case_assessment") if a3_doc else ""
        }
    }

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

    side_lower = (workspace.get("lawyer_side") or "").lower()
    prefix = "You are assisting the DEFENSE lawyer." if ("defense" in side_lower or "defendant" in side_lower) else "You are assisting the PROSECUTION lawyer."

    prompt = f"""
    {prefix}
    You are the VerdictIQ Multi-Agent Routing and Cognitive Coordinator.
    
    A lawyer is asking a question regarding an active legal case workspace.
    Your task is twofold:
    1. Determine which of the three specialized legal AI agents is best suited to answer this question.
       - Agent 1: Case Analysis Agent (Evidence auditing, weaknesses, missing evidence, loopholes, contradictions, risk assessments)
       - Agent 2: Courtroom Strategy Agent (Trial arguments, predicting opposition counterarguments, rebuttals, sequence of proof)
       - Agent 3: Legal Intelligence & Report Agent (Consolidated final report, professional summaries, legal references, recommendations, case assessment)
       
    2. Answer the question in character as that selected agent.
       - IMPORTANT: Start your response with the agent designation header exactly, e.g. '[Agent 1 - Case Analysis Agent]' or '[Agent 2 - Courtroom Strategy Agent]' or '[Agent 3 - Legal Intelligence & Report Agent]'.
       - Deliver an evidence-grounded, professional, and clinical legal answer based strictly on the provided case data.
       - STRICT FACTUAL GROUNDING RULE: You must ONLY refer to documents, facts, dates, timeline events, and entities that are present in the provided Case Context Data or the Recent Chat History. Do NOT assume, extrapolate, or invent any files, contracts, verbal agreements, names, or legal conclusions. If information is insufficient, state "Insufficient supporting evidence available."
       - If the user asks about a detail or document not present in the context, explicitly state: "This detail/document is not present in the workspace files."
       - Explain findings in simple, practical, lawyer-friendly language. Avoid robotic AI wording and unnecessarily complex legal jargon. Write like an intelligent legal assistant speaking to a lawyer.
       - Think practically and logically. Focus on realistic courtroom terms: what can realistically help the lawyer, what opposing counsel may attack, and what proof is actually convincing.
       - STRUCTURE YOUR RESPONSE: Avoid giant paragraphs and unreadable text walls. You must structure your findings/answers using these exact sections where applicable:
         ### Summary
         ### Strong Points
         ### Weak Points
         ### Missing Proof
         ### Possible Opponent Attack
         ### Recommended Action
       - Keep responses concise, clear, and practical.

    Case Context Data:
    {json.dumps(context_data, cls=MongoJSONEncoder, indent=2)}

    Recent Chat History:
    {history_str}

    User Question:
    "{question}"

    Let's think step by step: which agent is most answerable, and what is the best professional response?
    """

    agent_name = "Agent 3 - Legal Intelligence & Report Agent"
    reply_text = ""

    if IS_MOCK_GEMINI:
        # Mock Routing & Answer based dynamically on actual context
        lower_q = question.lower()
        client = workspace.get("client_name") or "Client"
        opponent = workspace.get("opposing_party") or "Opponent"
        case_type = workspace.get("case_type") or "General Dispute"
        
        strong_ev = context_data.get("evidence_audit", {}).get("strong_evidence", [])
        
        if any(w in lower_q for w in ["loophole", "weak", "evidence", "contradict", "missing", "risk"]):
            agent_name = "Agent 1 - Case Analysis Agent"
            ev_summary = f"including files: {', '.join([item.get('file_name', 'Document') for item in strong_ev])}" if strong_ev else "none"
            missing_desc = ', '.join([m.get('description', '') for m in context_data.get("evidence_audit", {}).get("missing_evidence", [])]) or "Additional corroboration documents"
            reply_text = f"""[Agent 1 - Case Analysis Agent]
### Summary
Audited case analysis for the {case_type} between {client} and {opponent}.

### Strong Points
Verified evidence: {ev_summary}.

### Weak Points
Gaps in documentation and electronic verification metadata.

### Missing Proof
Missing critical evidence: {missing_desc}.

### Possible Opponent Attack
Targeting the chain of custody or authenticity of electronic documents.

### Recommended Action
Obtain metadata validation reports and verify the timeline entries."""
            
        elif any(w in lower_q for w in ["argument", "opposing", "opponent", "attack", "rebut", "court", "trial"]):
            agent_name = "Agent 2 - Courtroom Strategy Agent"
            side = workspace.get("lawyer_side") or "counsel"
            reply_text = f"""[Agent 2 - Courtroom Strategy Agent]
### Summary
Simulating courtroom strategy for the {side} representing {client}.

### Strong Points
Assertion of liability under the claims backed by available timeline evidence.

### Weak Points
Vulnerabilities in proving strict compliance and oral notifications.

### Missing Proof
Written confirmation of notice and signed statements.

### Possible Opponent Attack
Opposing counsel will target procedural gaps and argue waiver or estoppel.

### Recommended Action
Prioritize arguments that rely on undisputed written timeline records and exclude verbal interactions."""
            
        else:
            agent_name = "Agent 3 - Legal Intelligence & Report Agent"
            strength = context_data.get("final_report", {}).get("case_strength") or "Moderate"
            reply_text = f"""[Agent 3 - Legal Intelligence & Report Agent]
### Summary
Synthesized case intelligence report for case '{workspace.get('case_title')}'. Case strength is evaluated as {strength}.

### Strong Points
Documented contract timeline and primary transaction records.

### Weak Points
Uncorroborated timeline assertions and potential waiver risks.

### Missing Proof
Third-party verification of digital metadata.

### Possible Opponent Attack
Burden-of-proof challenging arguments targeting our timeline details.

### Recommended Action
Reference general civil procedures and evidence codes governing burden of proof to address evidentiary gaps."""
    else:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt
            )
            reply_text = response.text.strip()
            
            # Extract agent name from header if possible
            if reply_text.startswith("[Agent 1"):
                agent_name = "Agent 1 - Case Analysis Agent"
            elif reply_text.startswith("[Agent 2"):
                agent_name = "Agent 2 - Courtroom Strategy Agent"
            elif reply_text.startswith("[Agent 3"):
                agent_name = "Agent 3 - Legal Intelligence & Report Agent"
        except Exception as e:
            logger.error(f"Failed to query Gemini for chat: {e}")
            agent_name = "Agent 3 - Legal Intelligence & Report Agent"
            reply_text = f"[Agent 3 - Legal Intelligence & Report Agent] An error occurred while communicating with the AI reasoning system. Case summary remains ready."

    # 3. Save User message
    user_msg_doc = {
        "workspace_id": workspace_id,
        "sender": "user",
        "text": question,
        "timestamp": datetime.utcnow()
    }
    await chats_collection.insert_one(user_msg_doc)

    # 4. Save Agent response
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
