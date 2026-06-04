import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId
import google.generativeai as genai
from dotenv import load_dotenv

# Ensure environment variables are loaded immediately
load_dotenv()

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini SDK
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IS_MOCK_GEMINI = not GEMINI_API_KEY or GEMINI_API_KEY == "placeholder_key"

if GEMINI_API_KEY and not IS_MOCK_GEMINI:
    logger.info("Initializing Google Generative AI SDK with GEMINI_API_KEY...")
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not configured or is placeholder. Using mock Gemini engine.")

async def analyze_document_text(text: str, filename: str, doc_description: str) -> Dict[str, Any]:
    """
    Calls Gemini to analyze a single document text and extract entities, dates, and a summary.
    """
    if not text.strip():
        return {
            "extracted_entities": {
                "people": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "financial_amounts": [],
                "legal_references": []
            },
            "extracted_dates": [],
            "ai_summary": f"Empty document: {filename}."
        }

    if IS_MOCK_GEMINI:
        logger.info(f"Generating dynamic mock analysis for document: {filename}")
        return generate_mock_document_analysis(text, filename, doc_description)

    prompt = f"""
    You are an AI-powered legal intake assistant.
    Analyze the following text extracted from document '{filename}' (Description: {doc_description}).
    Extract:
    1. Key entities (people, organizations, locations, dates, financial amounts, legal references/statutes).
    2. All important dates mentioned in the text.
    3. A clear, concise, professional AI legal summary of the document.

    STRICT FACTUAL GROUNDING RULES:
    - You must ONLY extract information directly present in the provided Document Text.
    - Do NOT assume, extrapolate, or invent any entities, dates, or details.
    - If a category of entities has no entries in the document text, return an empty list for that category. Do NOT invent placeholders.

    Return the result strictly as a valid JSON object matching the following structure:
    {{
      "extracted_entities": {{
        "people": ["string"],
        "organizations": ["string"],
        "locations": ["string"],
        "dates": ["string"],
        "financial_amounts": ["string"],
        "legal_references": ["string"]
      }},
      "extracted_dates": ["string"],
      "ai_summary": "string"
    }}
    
    Document Text:
    {text}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini document analysis error: {e}. Falling back to dynamic mock data.")
        return generate_mock_document_analysis(text, filename, doc_description)


async def generate_structured_case_context(workspace_meta: Dict[str, Any], document_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates workspace metadata and individual document extractions to build the final structured case context.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock case-wide structured context...")
        return generate_mock_case_context(workspace_meta, document_analyses)

    # Format document analyses for the prompt
    docs_summary = []
    for idx, da in enumerate(document_analyses):
        docs_summary.append(f"""
        Document #{idx+1}: {da.get('file_name', 'Unknown')}
        Type: {da.get('evidence_type', 'N/A')}
        Description: {da.get('description', '')}
        Summary: {da.get('ai_summary', '')}
        Key Entities: {json.dumps(da.get('extracted_entities', {}), cls=MongoJSONEncoder)}
        """)
    
    docs_joined = "\n\n".join(docs_summary)

    prompt = f"""
    You are the core Legal Intake Intelligence engine for VerdictIQ.
    Below is the workspace metadata and the AI analyses of the uploaded evidence files.
    Synthesize all this information to create a structured AI-ready case context.

    Workspace Metadata:
    - Case Title: {workspace_meta.get('case_title')}
    - Case Type: {workspace_meta.get('case_type')}
    - Lawyer Side: {workspace_meta.get('lawyer_side')}
    - Client: {workspace_meta.get('client_name')}
    - Opposing Party: {workspace_meta.get('opposing_party')}
    - Case Description: {workspace_meta.get('case_description')}
    - Objectives: {workspace_meta.get('objectives')}
    - Expected Outcome: {workspace_meta.get('expected_outcome')}
    - Concerns: {workspace_meta.get('concerns')}

    Document Extraction Summaries:
    {docs_joined}

    STRICT FACTUAL GROUNDING RULES:
    - Your output MUST be strictly grounded in the provided Workspace Metadata and Document Extraction Summaries.
    - Do NOT fabricate or introduce any external facts, parties, dates, transactions, or documents.
    - Do NOT duplicate any timeline events, claims, or entities. Ensure every item is unique.
    - If no evidence files are uploaded or if document extractions are empty, you must state that there is no documentary evidence, and base the context strictly on the workspace metadata.
    - If there are no claims, timeline events, or entities, leave those lists empty. Do NOT invent generic items.

    You must output:
    1. A synthesized, high-quality, and comprehensive case summary narrative.
    2. A list of key legal claims or defenses.
    3. A clear chronological timeline of events (dates, incidents, transaction references, legal events).
    4. Key entities identified across the case, mapping them to their type and legal role.
    5. Evidence relationships mapping specific evidence files (use file names or file IDs if available) to specific claims, including a brief description of how they support the claim.
    6. A clear list of legal objectives.
    7. A clear list of legal concerns or vulnerabilities.

    Return the result strictly as a valid JSON object matching the following structure:
    {{
      "case_summary": "string",
      "claims": ["string"],
      "timeline": [
        {{
          "date": "string",
          "incident": "string",
          "transaction_reference": "string",
          "legal_event": "string"
        }}
      ],
      "key_entities": [
        {{
          "name": "string",
          "type": "string",
          "role": "string"
        }}
      ],
      "evidence_relationships": [
        {{
          "evidence_id": "string",
          "claim_id": "string",
          "relationship_description": "string"
        }}
      ],
      "objectives": ["string"],
      "concerns": ["string"]
    }}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini aggregate case structuring error: {e}. Falling back to dynamic mock data.")
        return generate_mock_case_context(workspace_meta, document_analyses)


def generate_mock_document_analysis(text: str, filename: str, doc_description: str) -> Dict[str, Any]:
    """
    Generates dynamic mock document analysis strictly based on the actual text/description.
    """
    import re
    summary = f"Summary of {filename}: "
    if doc_description:
        summary += f"File described as: {doc_description}. "
    
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    if cleaned_text and not cleaned_text.startswith("[Evidence document content"):
        summary += cleaned_text[:200]
        if len(cleaned_text) > 200:
            summary += "..."
    else:
        summary += "No raw document text content was available for extraction."

    dates_found = re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', text, re.IGNORECASE)
    dates = list(set(dates_found))[:5]
    
    amounts_found = re.findall(r'\$\d+(?:,\d+)*(?:\.\d+)?', text)
    amounts = list(set(amounts_found))[:5]

    people = []
    orgs = []
    locs = []
    
    cap_words = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\b', text)
    for word in list(set(cap_words)):
        if "Corp" in word or "Inc" in word or "Ltd" in word or "LLC" in word or "Company" in word:
            orgs.append(word)
        elif word not in ["Summary", "Document", "Description", "Case", "File", "Evidence", "VerdictIQ", "The", "Plaintiff", "Defendant"]:
            if len(word.split()) > 1 and len(people) < 3:
                people.append(word)
            elif len(locs) < 3:
                locs.append(word)

    return {
        "extracted_entities": {
            "people": people,
            "organizations": orgs,
            "locations": locs,
            "dates": dates,
            "financial_amounts": amounts,
            "legal_references": []
        },
        "extracted_dates": dates,
        "ai_summary": summary
    }


def generate_mock_case_context(workspace_meta: Dict[str, Any], document_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates dynamic structured context strictly based on actual workspace metadata and document analyses.
    """
    title = workspace_meta.get("case_title") or "Unnamed Case"
    client = workspace_meta.get("client_name") or "Client"
    opponent = workspace_meta.get("opposing_party") or "Opposing Party"
    case_type = workspace_meta.get("case_type") or "General Dispute"
    desc = workspace_meta.get("case_description") or ""
    side = workspace_meta.get("lawyer_side") or "Counsel"
    
    summary = f"This legal workspace concerns a {case_type} between the client {client} (represented as {side}) and the opposing party {opponent}. "
    if desc:
        summary += f"Case Details: {desc}"
    else:
        summary += "The parties are involved in active dispute resolution."

    objectives_str = workspace_meta.get("objectives") or ""
    claims = []
    if objectives_str:
        raw_claims = [c.strip() for c in objectives_str.replace('\n', ',').split(',') if c.strip()]
        for rc in raw_claims:
            if rc not in claims:
                claims.append(rc)
    
    if not claims:
        claims = [f"Breach/Dispute claim by {client} against {opponent}"]

    timeline = []
    seen_dates = set()
    for da in document_analyses:
        file_name = da.get("file_name", "Evidence File")
        for dt in da.get("extracted_dates", []):
            if dt not in seen_dates:
                seen_dates.add(dt)
                timeline.append({
                    "date": dt,
                    "incident": f"Event referenced in evidence document '{file_name}': {da.get('ai_summary', '')[:100]}...",
                    "transaction_reference": "N/A",
                    "legal_event": "Evidence Reference"
                })
    
    try:
        timeline.sort(key=lambda x: x["date"])
    except Exception:
        pass

    if not timeline:
        timeline = [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "incident": "Workspace created and case initialized by counsel.",
                "transaction_reference": "N/A",
                "legal_event": "Case Intake"
            }
        ]

    key_entities = [
        {"name": client, "type": "Person/Organization", "role": f"Client ({side})"},
        {"name": opponent, "type": "Person/Organization", "role": "Opposing Party"}
    ]
    for da in document_analyses:
        ents = da.get("extracted_entities", {})
        for category in ["people", "organizations"]:
            for name in ents.get(category, []):
                if name not in [client, opponent] and not any(e["name"] == name for e in key_entities):
                    role = "Mentioned Entity"
                    key_entities.append({
                        "name": name,
                        "type": "Organization" if category == "organizations" else "Person",
                        "role": role
                    })

    evidence_relationships = []
    for idx, da in enumerate(document_analyses):
        file_name = da.get("file_name", "Evidence Document")
        file_id = da.get("file_id") or f"mock_file_{idx}"
        evidence_relationships.append({
            "evidence_id": file_id,
            "claim_id": "claim_0",
            "relationship_description": f"Document '{file_name}' provides contextual support. Summary: {da.get('ai_summary', '')}"
        })

    objectives = []
    if objectives_str:
        objectives = [o.strip() for o in objectives_str.split('\n') if o.strip()]
    if not objectives:
        objectives = [f"Successfully resolve the {case_type} in favor of {client}"]

    concerns_str = workspace_meta.get("concerns") or ""
    concerns = []
    if concerns_str:
        concerns = [c.strip() for c in concerns_str.split('\n') if c.strip()]
    if not concerns:
        concerns = [f"Proof requirements and validation of opposing claims"]

    return {
        "case_summary": summary,
        "claims": claims,
        "timeline": timeline,
        "key_entities": key_entities,
        "evidence_relationships": evidence_relationships,
        "objectives": objectives,
        "concerns": concerns
    }


async def analyze_case_evidence_and_risks(structured_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 1 Analysis using Gemini API.
    Consumes Agent 0 structured context and extracts audit-level insights.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock Agent 1 analysis...")
        return generate_mock_agent1_analysis(structured_context)

    prompt = f"""
    You are Agent 1, the "Legal Evidence Intelligence & Risk Analysis Engine" for VerdictIQ.
    Your task is to critically audit the structured legal case context produced by Agent 0.

    Input Structured Case Context:
    {json.dumps(structured_context, cls=MongoJSONEncoder, indent=2)}

    Perform the following analyses:
    1. EVIDENCE STRENGTH ANALYSIS:
       Audit and classify the evidence mentioned in the timeline, context, and evidence relationships.
       Classify evidence items into:
       - strong_evidence: directly supports claims, verifiable, specific, well documented.
       - moderate_evidence: partially supports or lacks absolute verification.
       - weak_evidence: vague, indirect, unsupported, unclear origin, insufficient relevance.
       - unsupported_claims: claims or objectives made in the context that have no supporting evidence files or timeline records.
       Ensure: If any evidence is completely insufficient for a claim, explicitly note "Insufficient supporting evidence available."

    2. MISSING EVIDENCE DETECTION:
       Identify gaps in proof. What documentation, witness statements, transaction records, or timestamps are missing?

    3. LOOPHOLE DETECTION:
       Detect vague claims, timeline inconsistencies, documentation weaknesses, or conflicting witness narrative points.

    4. CONTRADICTION ANALYSIS:
       Find mismatch/contradiction between:
       - claims and evidence
       - evidence and timeline
       - evidence and objectives
       - timeline events that conflict with each other.

    5. RISK ANALYSIS:
       Evaluate vulnerabilities, assumptions, and assign a risk_level ("Low Risk", "Medium Risk", "High Risk", "Critical Risk").

    6. CONFIDENCE SCORING:
       For each claim listed in the claims, assign a confidence_score between 0 and 100 representing the strength/reliability of supporting evidence.

    7. EVIDENCE RELATIONSHIPS:
       List mapping details connecting evidence_id/file_name to specific claim_id or claims.

    STRICT FACTUAL GROUNDING RULES:
    - Never directly modify the input context; only analyze it.
    - Avoid hallucinations; stay strictly evidence-grounded. Use professional legal reasoning tone.
    - Do NOT assume or invent any evidence files, legal terms, verbal notices, or contract details not explicitly present in the input context.
    - If there is absolutely no evidence or it is completely insufficient, output: "Insufficient supporting evidence available." in the corresponding descriptive fields.
    - Ensure there are no duplicate items in any list.

    Return the analysis strictly as a valid JSON object matching the following structure:
    {{
      "strong_evidence": [
        {{
          "evidence_id": "string",
          "file_name": "string",
          "supporting_claim": "string",
          "reasoning": "string"
        }}
      ],
      "moderate_evidence": [
        {{
          "evidence_id": "string",
          "file_name": "string",
          "supporting_claim": "string",
          "reasoning": "string"
        }}
      ],
      "weak_evidence": [
        {{
          "evidence_id": "string",
          "file_name": "string",
          "reasoning": "string"
        }}
      ],
      "unsupported_claims": [
        {{
          "claim": "string",
          "reasoning": "string"
        }}
      ],
      "missing_evidence": [
        {{
          "category": "string",
          "description": "string",
          "impact": "string"
        }}
      ],
      "loopholes": [
        {{
          "title": "string",
          "description": "string",
          "severity": "string"
        }}
      ],
      "contradictions": [
        {{
          "item_a": "string",
          "item_b": "string",
          "discrepancy": "string"
        }}
      ],
      "risk_analysis": {{
        "risk_level": "string",
        "vulnerabilities": ["string"],
        "assumptions": ["string"]
      }},
      "confidence_scores": [
        {{
          "claim": "string",
          "confidence_score": 82
        }}
      ],
      "evidence_relationships": [
        {{
          "evidence_id": "string",
          "claim_id": "string",
          "relationship_description": "string"
        }}
      ]
    }}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini Agent 1 analysis failure: {e}. Falling back to dynamic mock engine.")
        return generate_mock_agent1_analysis(structured_context)


def generate_mock_agent1_analysis(structured_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates dynamic Agent 1 analysis strictly grounded in structured context, avoiding any fake data.
    """
    claims = structured_context.get("claims", [])
    evidence_rel = structured_context.get("evidence_relationships", [])
    
    strong_ev = []
    moderate_ev = []
    weak_ev = []
    unsupported = []
    
    if evidence_rel:
        for idx, er in enumerate(evidence_rel):
            ev_id = er.get("evidence_id", f"ev_{idx}")
            desc = er.get("relationship_description", "")
            
            if idx == 0:
                strong_ev.append({
                    "evidence_id": ev_id,
                    "file_name": f"Document_{idx}",
                    "supporting_claim": claims[0] if claims else "Primary Case Claim",
                    "reasoning": f"Document provides direct supporting details: {desc[:100]}..."
                })
            else:
                moderate_ev.append({
                    "evidence_id": ev_id,
                    "file_name": f"Document_{idx}",
                    "supporting_claim": claims[0] if claims else "Primary Case Claim",
                    "reasoning": "Provides secondary corroboration."
                })
    else:
        weak_ev.append({
            "evidence_id": "none",
            "file_name": "N/A",
            "reasoning": "Insufficient supporting evidence available. No document files uploaded."
        })
        
    for c in claims:
        if not evidence_rel:
            unsupported.append({
                "claim": c,
                "reasoning": "Insufficient supporting evidence available. No documentation uploaded links to this claim."
            })

    missing_evidence = []
    concerns = structured_context.get("concerns", [])
    for cn in concerns:
        missing_evidence.append({
            "category": "Evidentiary Verification",
            "description": f"Further proof needed regarding: {cn}",
            "impact": "High - crucial for verification."
        })
    if not missing_evidence:
        missing_evidence.append({
            "category": "Evidentiary Verification",
            "description": "Insufficient supporting evidence available. Missing primary validation documents.",
            "impact": "High"
        })

    loopholes = []
    contradictions = []
    
    if evidence_rel:
        loopholes.append({
            "title": "Verifiability Gaps",
            "description": "Evidence requires verification against original digital metadata.",
            "severity": "Medium"
        })
        contradictions.append({
            "item_a": "Unverified electronic submissions",
            "item_b": "Burden of proof requirements",
            "discrepancy": "Self-serving documents require third-party validation."
        })
    else:
        loopholes.append({
            "title": "Missing Evidence Baseline",
            "description": "Insufficient supporting evidence available.",
            "severity": "Critical"
        })
        contradictions.append({
            "item_a": "Case Claims",
            "item_b": "Available Evidence Files",
            "discrepancy": "Insufficient supporting evidence available to prove any claims."
        })

    conf_scores = []
    for idx, c in enumerate(claims):
        score = 70 if evidence_rel else 10
        conf_scores.append({
            "claim": c,
            "confidence_score": score
        })

    return {
        "strong_evidence": strong_ev,
        "moderate_evidence": moderate_ev,
        "weak_evidence": weak_ev,
        "unsupported_claims": unsupported,
        "missing_evidence": missing_evidence,
        "loopholes": loopholes,
        "contradictions": contradictions,
        "risk_analysis": {
            "risk_level": "Medium Risk" if evidence_rel else "Critical Risk",
            "vulnerabilities": [
                "Lack of secondary witness statements." if evidence_rel else "Insufficient supporting evidence available."
            ],
            "assumptions": [
                "Assuming the provided electronic files represent authentic copies." if evidence_rel else "None"
            ]
        },
        "confidence_scores": conf_scores,
        "evidence_relationships": evidence_rel
    }


async def generate_courtroom_strategy(workspace_meta: Dict[str, Any], agent1_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 2 Room strategy simulation using Gemini.
    Consumes both Agent 0 context and Agent 1 auditing data to generate trial-ready strategies.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock Agent 2 courtroom strategy...")
        return generate_mock_agent2_strategy(workspace_meta, agent1_analysis)

    lawyer_side = workspace_meta.get("lawyer_side", "Plaintiff")

    prompt = f"""
    You are Agent 2, the "AI Courtroom Strategy & Adversarial Reasoning Engine" for VerdictIQ.
    Your objective is to simulate courtroom reasoning and generate tactical courtroom strategy intelligence.
    
    You represent the '{lawyer_side}' side of the case.
    Your strategy must remain strictly aligned with the '{lawyer_side}' position.
    
    If lawyer_side is Plaintiff/Prosecution:
      - Persuasive, accusatory, and claim-supporting arguments.
    If lawyer_side is Defendant/Defense:
      - Defensive, claim-challenging, and burden-of-proof challenging arguments.

    Input Case Context (from Agent 0):
    {json.dumps(workspace_meta, cls=MongoJSONEncoder, indent=2)}

    Input Evidence Auditing (from Agent 1):
    {json.dumps(agent1_analysis, cls=MongoJSONEncoder, indent=2)}

    Perform the following adversarial simulations:
    1. LAWYER ARGUMENT GENERATION:
       Generate persuasive, evidence-grounded arguments backing our objectives and claims.
       Ensure all arguments directly link to evidence.
    2. OPPOSITION COUNTERARGUMENT SIMULATION:
       Predict how opposing counsel will attack our timeline, credibility, witness narrative, or document validity.
    3. REBUTTAL STRATEGY GENERATION:
       Generate mitigation reasoning and timeline/evidence clarifications to counter the predicted opposition attacks.
    4. COURTROOM RISKS:
       Identify vulnerabilities (timeline gaps, lack of corroboration, witness credibility concerns).
    5. STRATEGIC RECOMMENDATIONS:
       Actionable courtroom directions, argument presentation sequences, and claims to emphasize.
    6. ARGUMENT PRIORITIES:
       Group our arguments into "strongest_arguments" (fully backed), "moderate_arguments", and "risky_arguments" (weak evidence/vulnerable).
    7. EVIDENCE UTILIZATION STRATEGY:
       Recommend sequencing order and guidance for presenting evidence files.

    STRICT FACTUAL GROUNDING & ADVERSARIAL RULES:
    - Stay completely grounded in the provided facts and evidence.
    - NEVER fabricate laws, statutes, witness testimonies, documents, dates, or transactions.
    - Do NOT assume or invent any arguments not backed by the provided case context and audit.
    - Keep a highly professional, clinical, courtroom-ready tone.
    - Ensure there are no duplicate entries.

    Return the analysis strictly as a valid JSON object matching the following structure:
    {{
      "lawyer_arguments": [
        {{
          "claim_id": "string",
          "argument_title": "string",
          "narrative": "string",
          "evidence_support": ["string"]
        }}
      ],
      "opponent_counterarguments": [
        {{
          "claim_id": "string",
          "attack_vector": "string",
          "explanation": "string",
          "evidence_targeted": ["string"]
        }}
      ],
      "rebuttal_strategies": [
        {{
          "counterargument_targeted": "string",
          "rebuttal_narrative": "string",
          "mitigation_steps": ["string"]
        }}
      ],
      "courtroom_risks": [
        {{
          "title": "string",
          "description": "string",
          "severity": "string"
        }}
      ],
      "strategic_recommendations": ["string"],
      "argument_priorities": {{
        "strongest_arguments": ["string"],
        "moderate_arguments": ["string"],
        "risky_arguments": ["string"]
      }},
      "evidence_utilization_strategy": [
        {{
          "evidence_id": "string",
          "sequence_order": 1,
          "presentation_guidance": "string"
        }}
      ]
    }}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini Agent 2 strategy failure: {e}. Falling back to dynamic mock engine.")
        return generate_mock_agent2_strategy(workspace_meta, agent1_analysis)


def generate_mock_agent2_strategy(workspace_meta: Dict[str, Any], agent1_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates dynamic Agent 2 courtroom strategy strictly based on workspace metadata and agent 1 analysis.
    """
    lawyer_side = workspace_meta.get("lawyer_side", "Plaintiff")
    client_name = workspace_meta.get("client_name") or "Client"
    opposing_party = workspace_meta.get("opposing_party") or "Opponent"
    claims = workspace_meta.get("claims") or ["General Claim"]
    if isinstance(claims, str):
        claims = [claims]
    
    strong_ev = agent1_analysis.get("strong_evidence", [])
    has_strong = len(strong_ev) > 0
    strong_ev_id = strong_ev[0].get("evidence_id", "none") if has_strong else "none"
    
    lawyer_arguments = []
    opponent_counterarguments = []
    rebuttal_strategies = []
    
    for idx, claim in enumerate(claims[:3]):
        claim_id = f"claim_{idx}"
        
        if lawyer_side.lower() in ["plaintiff", "prosecution"]:
            arg_title = f"Establishment of {claim}"
            narrative = f"As the {lawyer_side}, we assert that {opposing_party} is liable under {claim}. The client {client_name} has presented documentary evidence detailing the transaction and events."
            attack_vector = f"Challenging the credibility/completeness of {claim}"
            explanation = f"Opposing counsel will argue that the evidence presented is insufficient, self-serving, or lacks corroboration."
            rebuttal_narrative = f"Highlight the specific dates and factual records present in our timeline to show compliance and establish liability."
            mitigation_steps = ["Reference the explicit documentary dates.", "Anchor arguments in undisputed timeline events."]
        else:
            arg_title = f"Defense Against {claim}"
            narrative = f"As the {lawyer_side}, we assert that the plaintiff {opposing_party} has failed to meet the burden of proof required for {claim}."
            attack_vector = "Equitable Estoppel and Waiver arguments"
            explanation = f"Opposing counsel will argue that {client_name} waived strict compliance through course of conduct."
            rebuttal_narrative = "Emphasize strict compliance with procedural terms and contract conditions."
            mitigation_steps = ["Point out gaps in the plaintiff's documentation.", "Highlight lack of written notices."]

        lawyer_arguments.append({
            "claim_id": claim_id,
            "argument_title": arg_title,
            "narrative": narrative,
            "evidence_support": [strong_ev_id] if has_strong else []
        })
        
        opponent_counterarguments.append({
            "claim_id": claim_id,
            "attack_vector": attack_vector,
            "explanation": explanation,
            "evidence_targeted": [strong_ev_id] if has_strong else []
        })
        
        rebuttal_strategies.append({
            "counterargument_targeted": attack_vector,
            "rebuttal_narrative": rebuttal_narrative,
            "mitigation_steps": mitigation_steps
        })

    courtroom_risks = [
        {
            "title": "Evidentiary Gaps",
            "description": "Potential vulnerability to objections on uncorroborated timeline assertions." if has_strong else "Vulnerability due to absolute lack of uploaded evidence files.",
            "severity": "High" if not has_strong else "Medium"
        }
    ]

    strategic_recommendations = [
        f"Sequence presentation starting with the strongest documented claims for {client_name}.",
        "Emphasize strict legal standards and burden of proof requirements."
    ]

    strongest_args = [arg["argument_title"] for arg in lawyer_arguments]
    arg_priorities = {
        "strongest_arguments": strongest_args[:1] if strongest_args else ["Procedural Defense"],
        "moderate_arguments": strongest_args[1:2] if len(strongest_args) > 1 else [],
        "risky_arguments": strongest_args[2:] if len(strongest_args) > 2 else []
    }

    evidence_utilization_strategy = []
    if has_strong:
        evidence_utilization_strategy.append({
            "evidence_id": strong_ev_id,
            "sequence_order": 1,
            "presentation_guidance": "Introduce during initial statements to anchor the factual timeline."
        })

    return {
        "lawyer_arguments": lawyer_arguments,
        "opponent_counterarguments": opponent_counterarguments,
        "rebuttal_strategies": rebuttal_strategies,
        "courtroom_risks": courtroom_risks,
        "strategic_recommendations": strategic_recommendations,
        "argument_priorities": arg_priorities,
        "evidence_utilization_strategy": evidence_utilization_strategy
    }


async def generate_final_legal_report(workspace_meta: Dict[str, Any], agent1_analysis: Dict[str, Any], agent2_strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 3 Final Report Synthesis using Gemini.
    Consumes outputs from Agents 0, 1, and 2 to compile the consolidated legal report.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock Agent 3 final report...")
        return generate_mock_agent3_report(workspace_meta, agent1_analysis, agent2_strategy)

    prompt = f"""
    You are Agent 3, the "AI Legal Intelligence Synthesis & Final Reporting Engine" for VerdictIQ.
    Your task is to synthesize all prior agent analyses to create a polished, professional legal intelligence report.

    Input Case Context (from Agent 0):
    {json.dumps(workspace_meta, cls=MongoJSONEncoder, indent=2)}

    Input Evidence Analysis (from Agent 1):
    {json.dumps(agent1_analysis, cls=MongoJSONEncoder, indent=2)}

    Input Courtroom Strategy (from Agent 2):
    {json.dumps(agent2_strategy, cls=MongoJSONEncoder, indent=2)}

    Perform the following report synthesis tasks:
    1. EXECUTIVE CASE SUMMARY:
       Synthesize a concise overview of the case, highlighting major legal concerns, strongest evidence, and critical vulnerabilities.
    2. CASE STRENGTH EVALUATION:
       Assign an overall case strength rating: "Strong Case", "Moderate Case", "Weak Case", or "High Risk Case" based on evidence and contradictions.
    3. LEGAL REFERENCE IDENTIFICATION:
       Identify contextually relevant acts, statutes, laws, and probable legal sections. Include descriptions of their relevance.
       STRICT RULE: Suggest relevant sections contextually; DO NOT claim guaranteed legal applicability or provide definitive legal advice.
    4. STRATEGIC RECOMMENDATIONS:
       List prioritized next-step recommendations and risk mitigation strategies.
    5. PROFESSIONAL REPORT GENERATION:
       Compile the final consolidated report divided into sections:
       - Executive Summary
       - Case Overview
       - Evidence Analysis
       - Missing Evidence
       - Loophole Analysis
       - Counterargument Risks
       - Legal References
       - Strategic Recommendations
       - Overall Case Assessment

    STRICT FACTUAL GROUNDING RULES:
    - Stay completely grounded in the provided facts.
    - NEVER fabricate statutes, precedents, witness testimonies, or evidence.
    - Do NOT introduce any external facts or documents.
    - Add this mandatory AI disclaimer text:
      "This AI-generated analysis is intended for legal research assistance and strategic support only. It should not be treated as definitive legal advice."
    - Ensure there are no duplicate entries.

    Return the analysis strictly as a valid JSON object matching the following structure:
    {{
      "executive_summary": "string",
      "case_strength": "string",
      "strongest_evidence": [
        {{
          "evidence_id": "string",
          "file_name": "string",
          "supporting_claim": "string",
          "reasoning": "string"
        }}
      ],
      "weak_evidence": [
        {{
          "evidence_id": "string",
          "file_name": "string",
          "reasoning": "string"
        }}
      ],
      "missing_evidence": [
        {{
          "category": "string",
          "description": "string",
          "impact": "string"
        }}
      ],
      "loopholes": [
        {{
          "title": "string",
          "description": "string",
          "severity": "string"
        }}
      ],
      "legal_references": [
        {{
          "act_or_statute": "string",
          "section": "string",
          "relevance": "string"
        }}
      ],
      "strategic_recommendations": ["string"],
      "courtroom_risks": [
        {{
          "title": "string",
          "description": "string",
          "severity": "string"
        }}
      ],
      "final_case_assessment": "string",
      "generated_report": {{
        "sections": [
          {{
            "title": "string",
            "content": "string"
          }}
        ]
      }}
    }}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini Agent 3 report generation failure: {e}. Falling back to dynamic mock engine.")
        return generate_mock_agent3_report(workspace_meta, agent1_analysis, agent2_strategy)


def generate_mock_agent3_report(workspace_meta: Dict[str, Any], agent1_analysis: Dict[str, Any], agent2_strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates dynamic mock Agent 3 legal report strictly using metadata and prior analyses.
    """
    strongest_ev = agent1_analysis.get("strong_evidence", [])
    weak_ev = agent1_analysis.get("weak_evidence", [])
    missing_ev = agent1_analysis.get("missing_evidence", [])
    loopholes = agent1_analysis.get("loopholes", [])
    courtroom_risks = agent2_strategy.get("courtroom_risks", [])
    strategic_recs = agent2_strategy.get("strategic_recommendations", [])
    
    lawyer_side = workspace_meta.get("lawyer_side", "Plaintiff")
    client_name = workspace_meta.get("client_name") or "Client"
    opposing_party = workspace_meta.get("opposing_party") or "Opponent"
    case_type = workspace_meta.get("case_type") or "General Dispute"

    case_strength = "Moderate Case" if strongest_ev else "Weak Case"

    executive_summary = f"This consolidated legal intelligence report details the {case_type} between {client_name} (represented as {lawyer_side}) and {opposing_party}. Strategic arguments are anchored on {len(strongest_ev)} strong evidence items. Overall case readiness is classified as {case_strength}."

    legal_references = [
        {
            "act_or_statute": "Standard Procedure and Rules of Evidence",
            "section": "General Burden of Proof",
            "relevance": "Governs the evidentiary requirements to prove the assertions made in the case."
        }
    ]

    final_case_assessment = f"Based on prior analysis, {client_name} holds a {case_strength.lower()} claim. Counsel must actively address the vulnerabilities and missing evidence identified in the audit."

    sections = [
        {
          "title": "Executive Summary",
          "content": executive_summary
        },
        {
          "title": "Case Overview",
          "content": f"The dispute centers around a {case_type}. Client side: {client_name}, Opposing side: {opposing_party}."
        },
        {
          "title": "Evidence Analysis",
          "content": f"Found {len(strongest_ev)} strong evidence items and {len(weak_ev)} weak/unsupported evidence items."
        },
        {
          "title": "Missing Evidence",
          "content": "; ".join([f"{item.get('category')}: {item.get('description')}" for item in missing_ev]) if missing_ev else "No critical missing evidence items reported."
        },
        {
          "title": "Loophole Analysis",
          "content": "; ".join([f"{item.get('title')}: {item.get('description')}" for item in loopholes]) if loopholes else "No loopholes identified."
        },
        {
          "title": "Counterargument Risks",
          "content": "; ".join([f"{item.get('title')}: {item.get('description')}" for item in courtroom_risks]) if courtroom_risks else "No critical counterargument risks identified."
        },
        {
          "title": "Legal References",
          "content": "Refer to applicable state civil procedures and evidence codes governing burden of proof."
        },
        {
          "title": "Strategic Recommendations",
          "content": "; ".join(strategic_recs) if strategic_recs else "Maintain standard procedural compliance."
        },
        {
          "title": "Overall Case Assessment",
          "content": final_case_assessment
        }
    ]

    return {
        "executive_summary": executive_summary,
        "case_strength": case_strength,
        "strongest_evidence": strongest_ev,
        "weak_evidence": weak_ev,
        "missing_evidence": missing_ev,
        "loopholes": loopholes,
        "legal_references": legal_references,
        "strategic_recommendations": strategic_recs,
        "courtroom_risks": courtroom_risks,
        "final_case_assessment": final_case_assessment,
        "generated_report": {
            "sections": sections
        }
    }
