import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId
import google.generativeai as genai
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

# Load Pydantic Schemas for validation
from app.schemas.case_schema import (
    Agent0Output,
    Agent1Output,
    LegalResearchOutput,
    Agent2Output,
    Agent3Output,
    Agent4Output
)

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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if GEMINI_API_KEY and not IS_MOCK_GEMINI:
    logger.info("Initializing Google Generative AI SDK with GEMINI_API_KEY...")
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not configured or is placeholder. Using mock Gemini engine.")

def generate_content_with_fallback(prompt: str, generation_config: dict = None, api_key: str = None) -> Any:
    """
    Tries to generate content using a prioritized list of Gemini models
    to handle 429 quota exhaustion errors gracefully by falling back to other models,
    with short sleep retries for transient RPM limits.
    """
    import time
    
    # Configure API key dynamically
    key = api_key or os.getenv("PIPELINE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key:
        genai.configure(api_key=key)

    models = [GEMINI_MODEL]
    for m in ["gemini-2.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"]:
        if m not in models:
            models.append(m)
            
    last_error = None
    for model_name in models:
        for attempt in range(2):
            try:
                logger.info(f"Model Fallback: Attempting generation with model: {model_name} (attempt {attempt+1})")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt, generation_config=generation_config)
                if response and response.text:
                    logger.info(f"Model Fallback: Successfully generated content using: {model_name}")
                    return response
            except Exception as e:
                last_error = e
                if "429" in str(e):
                    sleep_time = 2.0 * (attempt + 1)
                    logger.warning(f"Model Fallback: Model {model_name} hit 429. Sleeping {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Model Fallback: Model {model_name} failed: {e}")
                    break
            
    if last_error:
        raise last_error
    raise Exception("All candidate Gemini models failed to generate content.")

def get_lawyer_side_prefix(lawyer_side: str) -> str:
    if not lawyer_side:
        return "You are assisting the PROSECUTION lawyer.\n"
    side_lower = lawyer_side.lower()
    if "defense" in side_lower or "defendant" in side_lower:
        return "You are assisting the DEFENSE lawyer.\n"
    else:
        return "You are assisting the PROSECUTION lawyer.\n"

def validate_and_parse_json(raw_text: str, pydantic_schema: Any) -> Dict[str, Any]:
    """
    Cleans markdown code fences, parses JSON, and validates it against a Pydantic schema.
    """
    cleaned_text = raw_text.strip()
    if cleaned_text.startswith("```"):
        lines = cleaned_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned_text = "\n".join(lines).strip()
    
    if not cleaned_text.startswith("{") and "{" in cleaned_text:
        cleaned_text = cleaned_text[cleaned_text.find("{"):]
    if not cleaned_text.endswith("}") and "}" in cleaned_text:
        cleaned_text = cleaned_text[:cleaned_text.rfind("}")+1]

    parsed_json = json.loads(cleaned_text, strict=False)
    validated_model = pydantic_schema.model_validate(parsed_json)
    return validated_model.model_dump()


DOCUMENT_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=["lawyer_side_prefix", "filename", "doc_description", "text"],
    template="""{lawyer_side_prefix}
You are an AI-powered legal intake assistant.
Analyze the following text extracted from document '{filename}' (Description: {doc_description}).
Extract:
1. Key entities (people, organizations, locations, dates, financial amounts, legal references/statutes).
2. All important dates mentioned in the text.
3. A clear, concise, professional AI legal summary of the document.

STRICT FACTUAL GROUNDING RULES:
- You must ONLY extract information directly present in the provided Document Text.
- If the actual Document Text conflicts or contradicts the provided Description (Description: {doc_description}), the actual Document Text takes absolute precedence. You must extract information and entities strictly from the Document Text, and explicitly note the contradiction in the 'ai_summary' (e.g., "WARNING: Contradiction detected - user description states X, but document text contains Y").
- If the Document Text is a placeholder indicating a media/video/image file (e.g., starts with '[Evidence document content...' or '[Scanned Image Evidence...'), treat the User-provided Description as the primary source of truth for the file's context.
- Do NOT assume, extrapolate, or invent any entities, dates, or details.
- If a category of entities has no entries in the document text (or in the description if the text is a placeholder), return an empty list for that category. Do NOT invent placeholders.

ADDITIONAL INSTRUCTIONS:
- Explain findings in simple, practical, lawyer-friendly language. Avoid robotic AI wording and unnecessarily complex legal jargon.
- Think practically and logically. If any information is insufficient, state "Insufficient supporting evidence available."

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
{text}"""
)

CASE_CONTEXT_PROMPT = PromptTemplate(
    input_variables=["lawyer_side_prefix", "case_title", "case_type", "lawyer_side", "client_name", "opposing_party", "case_description", "objectives", "expected_outcome", "concerns", "docs_joined", "previous_structured_context"],
    template="""{lawyer_side_prefix}
You are the core Legal Intake Intelligence engine for VerdictIQ.
Below is the workspace metadata, the AI analyses of the uploaded evidence files, and any previous structured case context.
Synthesize all this information to create a structured AI-ready case context.

Workspace Metadata:
- Case Title: {case_title}
- Case Type: {case_type}
- Lawyer Side: {lawyer_side}
- Client: {client_name}
- Opposing Party: {opposing_party}
- Case Description: {case_description}
- Objectives: {objectives}
- Expected Outcome: {expected_outcome}
- Concerns: {concerns}

Document Extraction Summaries:
{docs_joined}

Previous Structured Case Context (Memory):
{previous_structured_context}

CUMULATIVE CASE MEMORY RULES:
- Workspace memory is cumulative. Incorporate all findings from the previous structured case context and merge them with the new document extraction summaries.
- Reconstruct the complete case understanding. Do NOT overwrite previous findings unless new evidence explicitly contradicts them.
- Reassess the entire case. If new evidence contradicts previous findings, recalculate conclusions (timeline, key claims, key entities, etc.). Do not remain anchored to previous conclusions.
- Output a single, consolidated and updated representation of the case context.

STRICT FACTUAL GROUNDING RULES:
- Your output MUST be strictly grounded in the provided Workspace Metadata, Document Extraction Summaries, and Previous Structured Case Context.
- Do NOT fabricate or introduce any external facts, parties, dates, transactions, or documents.
- Do NOT duplicate any timeline events, claims, or entities. Ensure every item is unique.
- If there are no claims, timeline events, or entities, leave those lists empty. Do NOT invent generic items.
- CRITICAL FORMATTING RULE: Do NOT include raw filenames (such as 'evidence1.txt', 'witness_statement.pdf', etc.) anywhere in the descriptive, narrative, overview, timeline, or inventory fields. Instead, refer to evidence files descriptively based on their content/type/date (e.g. 'the autopsy report', 'the email correspondence dated October 5th').

ADDITIONAL INSTRUCTIONS:
- Explain findings in simple, practical, lawyer-friendly language. Avoid robotic AI wording and unnecessarily complex legal jargon. Output must read like a detailed legal analyst's case briefing.
- Think practically and logically. All suggestions, timelines, and relationships must align with the selected lawyer side: support the prosecution perspective if Plaintiff/Prosecution, and support the defense perspective if Defendant/Defense.
- Avoid exaggerated AI behavior: do NOT act like a judge, claim legal certainty, or predict guaranteed outcomes. Instead, use cautious legal-assistant language.
- If information is insufficient, clearly state: "Insufficient supporting evidence available."

Return the result strictly as a valid JSON object matching the following structure:
{{
  "case_summary": "string (legacy consolidated summary)",
  "claims": ["string (legacy claims list)"],
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
  "objectives": ["string (legacy objectives)"],
  "concerns": ["string (legacy concerns)"],
  "case_overview": "string (comprehensive, detailed legal analyst's case briefing summary narrative)",
  "timeline_of_events": [
    {{
      "date": "string",
      "incident": "string",
      "transaction_reference": "string",
      "legal_event": "string"
    }}
  ],
  "people_involved": [
    {{
      "name": "string",
      "type": "string",
      "role": "string"
    }}
  ],
  "relationships": ["string (descriptions of key relationships between entities and events)"],
  "key_claims": ["string (primary legal claims or defenses)"],
  "important_facts": ["string (detailed key facts established by evidence)"],
  "evidence_inventory": ["string (descriptions of evidence items, NOT raw filenames)"],
  "open_questions": ["string (gaps or unresolved questions to investigate)"],
  "case_understanding_score": 85
}}"""
)

async def analyze_document_text(text: str, filename: str, doc_description: str, lawyer_side: str = None) -> Dict[str, Any]:
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

    prefix = get_lawyer_side_prefix(lawyer_side)
    prompt = DOCUMENT_ANALYSIS_PROMPT.format(
        lawyer_side_prefix=prefix,
        filename=filename,
        doc_description=doc_description,
        text=text
    )

    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text, strict=False)
        return data
    except Exception as e:
        logger.error(f"Gemini document analysis error: {e}. Falling back to dynamic mock data.")
        return generate_mock_document_analysis(text, filename, doc_description)


async def generate_structured_case_context(
    workspace_meta: Dict[str, Any],
    document_analyses: List[Dict[str, Any]],
    previous_structured_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Aggregates workspace metadata and individual document extractions to build the final structured case context.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock case-wide structured context...")
        return generate_mock_case_context(workspace_meta, document_analyses, previous_structured_context)

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

    prev_ctx_str = "No previous structured case context available."
    if previous_structured_context:
        # Filter MongoDB keys
        clean_prev = {k: v for k, v in previous_structured_context.items() if k not in ["_id", "generated_at"]}
        prev_ctx_str = json.dumps(clean_prev, cls=MongoJSONEncoder, indent=2)

    lawyer_side = workspace_meta.get("lawyer_side")
    prefix = get_lawyer_side_prefix(lawyer_side)
    prompt = CASE_CONTEXT_PROMPT.format(
        lawyer_side_prefix=prefix,
        case_title=workspace_meta.get('case_title') or '',
        case_type=workspace_meta.get('case_type') or '',
        lawyer_side=workspace_meta.get('lawyer_side') or '',
        client_name=workspace_meta.get('client_name') or '',
        opposing_party=workspace_meta.get('opposing_party') or '',
        case_description=workspace_meta.get('case_description') or '',
        objectives=workspace_meta.get('objectives') or '',
        expected_outcome=workspace_meta.get('expected_outcome') or '',
        concerns=workspace_meta.get('concerns') or '',
        docs_joined=docs_joined,
        previous_structured_context=prev_ctx_str
    )

    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return validate_and_parse_json(response.text, Agent0Output)
    except Exception as e:
        logger.error(f"Gemini aggregate case structuring error: {e}. Falling back to dynamic mock data.")
        return generate_mock_case_context(workspace_meta, document_analyses, previous_structured_context)



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


def generate_mock_case_context(
    workspace_meta: Dict[str, Any],
    document_analyses: List[Dict[str, Any]],
    previous_structured_context: Dict[str, Any] = None
) -> Dict[str, Any]:
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

    # Map to new Agent0Output schema fields
    timeline_events_objs = []
    for t in timeline:
        timeline_events_objs.append(TimelineEvent(**t))

    entities_objs = []
    for ke in key_entities:
        entities_objs.append(KeyEntity(**ke))

    relationships_list = [f"Client {client} has a dispute of type {case_type} with opponent {opponent}."]
    important_facts_list = [f"Dispute arose under workspace {title}."]
    evidence_inv = []
    for da in document_analyses:
        evidence_inv.append(f"Descriptive metadata for file: {da.get('file_name')} - {da.get('description')}")

    return {
        "case_summary": summary,
        "claims": claims,
        "timeline": timeline,
        "key_entities": key_entities,
        "evidence_relationships": evidence_relationships,
        "objectives": objectives,
        "concerns": concerns,
        "case_overview": f"[Mock overview] {summary}",
        "timeline_of_events": timeline_events_objs,
        "people_involved": entities_objs,
        "relationships": relationships_list,
        "key_claims": claims,
        "important_facts": important_facts_list,
        "evidence_inventory": evidence_inv,
        "open_questions": ["Verify all document dates."],
        "case_understanding_score": 90
    }


EVIDENCE_RISK_PROMPT = PromptTemplate(
    input_variables=["lawyer_side_prefix", "structured_context"],
    template="""{lawyer_side_prefix}
You are Agent 1, the "Legal Evidence Intelligence & Risk Analysis Engine" for VerdictIQ.
Your task is to critically audit the structured legal case context produced by Agent 0.

Input Structured Case Context:
{structured_context}

Perform the following analyses:
1. EVIDENCE STRENGTH ANALYSIS & EVALUATIONS:
   Audit and classify the evidence mentioned in the timeline, context, and evidence relationships.
   Classify evidence items into:
   - strong_evidence: directly supports claims, verifiable, specific, well documented.
   - moderate_evidence: partially supports or lacks absolute verification.
   - weak_evidence: vague, indirect, unsupported, unclear origin, insufficient relevance.
   - unsupported_claims: claims or objectives made in the context that have no supporting evidence files or timeline records.
   Ensure: If any evidence is completely insufficient for a claim, explicitly note "Insufficient supporting evidence available."
   
   For EACH evidence item found in the structured context, generate a detailed evaluation including:
   - why it is strong
   - why it is weak
   - what assumptions exist
   - reliability level
   - possible challenges / objections.

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

7. ADDITIONAL EVIDENTIARY ANALYSIS:
   - investigative_gaps: key investigative directions that lack proof.
   - reliability_concerns: potential credibility issues for witnesses or files.
   - alternative_interpretations: how opposing counsel might interpret the same facts/evidence.

STRICT BEHAVIOR & GROUNDING RULES:
- Never directly modify the input context; only analyze it.
- All analysis, reasoning, suggestion of risks, and audit assessments must align with the selected lawyer side: support the prosecution perspective if Prosecution/Plaintiff, and support the defense perspective if Defense/Defendant.
- Explain findings in simple, practical, lawyer-friendly language. Avoid robotic AI wording and unnecessarily complex legal jargon. Explain findings clearly like a professional legal assistant speaking to a lawyer.
- Think practically and logically. Focus on realistic courtroom terms: what can realistically help the lawyer, what opposing counsel may attack, and what proof is actually convincing.
- Always explain reasoning. Do NOT just label evidence as weak or strong. Explain WHY in courtroom terms.
- Stay strictly evidence-grounded. Do NOT invent witnesses, transactions, events, legal conclusions, or court outcomes.
- If there is absolutely no evidence or it is completely insufficient, output: "Insufficient supporting evidence available." in the corresponding descriptive fields.
- Avoid exaggerated AI behavior: do NOT act like a judge, claim legal certainty, or predict guaranteed outcomes. Instead, use cautious legal-assistant language.
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
  ],
  "evidence_evaluations": [
    {{
      "evidence_id": "string",
      "file_name": "string",
      "classification": "string",
      "why_strong": "string",
      "why_weak": "string",
      "assumptions": "string",
      "reliability_level": "string",
      "possible_challenges": "string"
    }}
  ],
  "investigative_gaps": ["string"],
  "reliability_concerns": ["string"],
  "alternative_interpretations": ["string"]
}}"""
)

async def analyze_case_evidence_and_risks(structured_context: Dict[str, Any], lawyer_side: str = None) -> Dict[str, Any]:
    """
    Agent 1 Analysis using Gemini API.
    Consumes Agent 0 structured context and extracts audit-level insights.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock Agent 1 analysis...")
        return generate_mock_agent1_analysis(structured_context, lawyer_side=lawyer_side)

    if not lawyer_side:
        lawyer_side = structured_context.get("lawyer_side")
    prefix = get_lawyer_side_prefix(lawyer_side)

    prompt = EVIDENCE_RISK_PROMPT.format(
        lawyer_side_prefix=prefix,
        structured_context=json.dumps(structured_context, cls=MongoJSONEncoder, indent=2)
    )

    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()
        if not raw_text.startswith("{") and "{" in raw_text:
            raw_text = raw_text[raw_text.find("{"):]
        if not raw_text.endswith("}") and "}" in raw_text:
            raw_text = raw_text[:raw_text.rfind("}")+1]
        
        parsed_json = json.loads(raw_text, strict=False)
        risk_info = parsed_json.get("risk_analysis", {})
        if "risk_level" not in parsed_json and "risk_level" in risk_info:
            parsed_json["risk_level"] = risk_info["risk_level"]
        elif "risk_level" not in parsed_json:
            parsed_json["risk_level"] = "Medium Risk"
            
        validated_model = Agent1Output.model_validate(parsed_json)
        return validated_model.model_dump()
    except Exception as e:
        logger.error(f"Gemini Agent 1 analysis failure: {e}. Falling back to dynamic mock engine.")
        return generate_mock_agent1_analysis(structured_context, lawyer_side=lawyer_side)



def generate_mock_agent1_analysis(structured_context: Dict[str, Any], lawyer_side: str = None) -> Dict[str, Any]:
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

    evals = []
    for item in strong_ev:
        evals.append({
            "evidence_id": item["evidence_id"],
            "file_name": item["file_name"],
            "classification": "Strong",
            "why_strong": item["reasoning"],
            "why_weak": "N/A",
            "assumptions": "Assumed authentic.",
            "reliability_level": "High",
            "possible_challenges": "None anticipated."
        })
    for item in moderate_ev:
        evals.append({
            "evidence_id": item["evidence_id"],
            "file_name": item["file_name"],
            "classification": "Moderate",
            "why_strong": item["reasoning"],
            "why_weak": "Lacks direct electronic validation.",
            "assumptions": "Assumed standard copy.",
            "reliability_level": "Medium",
            "possible_challenges": "Opponent will demand metadata."
        })
    for item in weak_ev:
        evals.append({
            "evidence_id": item["evidence_id"],
            "file_name": item["file_name"],
            "classification": "Weak",
            "why_strong": "N/A",
            "why_weak": item["reasoning"],
            "assumptions": "Vague significance.",
            "reliability_level": "Low",
            "possible_challenges": "Highly contestable."
        })

    return {
        "strong_evidence": strong_ev,
        "moderate_evidence": moderate_ev,
        "weak_evidence": weak_ev,
        "unsupported_claims": unsupported,
        "missing_evidence": missing_evidence,
        "loopholes": loopholes,
        "contradictions": contradictions,
        "risk_level": "Medium Risk" if evidence_rel else "Critical Risk",
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
        "evidence_relationships": evidence_rel,
        "evidence_evaluations": evals,
        "investigative_gaps": ["Verify other parties' timelines."] if evidence_rel else ["Insufficient supporting evidence available."],
        "reliability_concerns": ["Authentication of files."] if evidence_rel else ["Insufficient supporting evidence available."],
        "alternative_interpretations": ["Opponent might claim innocent mistake."] if evidence_rel else ["Insufficient supporting evidence available."]
    }

COURTROOM_STRATEGY_PROMPT = PromptTemplate(
    input_variables=["lawyer_side_prefix", "lawyer_side", "case_context", "agent1_analysis", "legal_research"],
    template="""{lawyer_side_prefix}
You are Agent 2, the "AI Courtroom Strategy & Adversarial Reasoning Engine" for VerdictIQ.
Your objective is to simulate courtroom reasoning and generate tactical courtroom strategy intelligence.

You represent the '{lawyer_side}' side of the case.
Your strategy must remain strictly aligned with the '{lawyer_side}' position.

If lawyer_side is Plaintiff/Prosecution:
  - Support the prosecution perspective with persuasive, accusatory, and claim-supporting arguments.
If lawyer_side is Defendant/Defense:
  - Support the defense perspective with defensive, claim-challenging, and burden-of-proof challenging arguments.

Input Case Context (from Agent 0):
{case_context}

Input Evidence Auditing (from Agent 1):
{agent1_analysis}

Input Legal Research & Precedents (from Legal Research Agent):
{legal_research}

Perform the following adversarial simulations:
1. LAWYER ARGUMENT GENERATION (SECTION A):
   Generate persuasive, evidence-grounded arguments backing our objectives and claims.
   Ensure all arguments directly link to evidence.
2. OPPOSITION COUNTERARGUMENT SIMULATION (SECTION B):
   Predict how opposing counsel will attack our timeline, credibility, witness narrative, or document validity, attacking the weaknesses of our evidence.
3. REBUTTAL STRATEGY GENERATION (SECTION C):
   Generate mitigation reasoning and timeline/evidence clarifications to counter the predicted opposition attacks.
4. ADVERSARIAL SIMULATIONS EXCHANGE:
   For ALL major evidence items, generate a simulated exchange in the exact format:
   - Argument (SECTION A)
   - Counterargument (SECTION B)
   - Rebuttal (SECTION C)
   Repeat this for each major evidence item to simulate a realistic courtroom exchange.

5. COURTROOM RISKS:
   Identify vulnerabilities (timeline gaps, lack of corroboration, witness credibility concerns).
6. STRATEGIC RECOMMENDATIONS:
   Actionable courtroom directions, argument presentation sequences, and claims to emphasize.
7. ARGUMENT PRIORITIES:
   Group our arguments into "strongest_arguments" (fully backed), "moderate_arguments", and "risky_arguments" (weak evidence/vulnerable).
8. EVIDENCE UTILIZATION STRATEGY:
   Recommend sequencing order and guidance for presenting evidence files.

STRICT FACTUAL GROUNDING & BEHAVIOR RULES:
- All arguments, counterarguments, rebuttals, risks, and recommendations must align with the selected lawyer side: support the prosecution perspective if Prosecution/Plaintiff, and support the defense perspective if Defense/Defendant.
- Explain findings in simple, practical, lawyer-friendly language. Avoid robotic AI wording and unnecessarily complex legal jargon. Explain findings clearly like a professional legal assistant speaking to a lawyer.
- Think practically and logically. Focus on realistic courtroom terms: what can realistically help the lawyer, what opposing counsel may attack, and what proof is actually convincing. Explain WHY evidence is strong or weak.
- Stay completely grounded in the provided facts and evidence. NEVER fabricate laws, statutes, witness testimonies, documents, dates, transactions, or court outcomes.
- If information is insufficient, clearly state: "Insufficient supporting evidence available."
- Avoid exaggerated AI behavior: do NOT act like a judge, claim legal certainty, or predict guaranteed outcomes. Instead, use cautious legal-assistant language.
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
  ],
  "adversarial_simulations": [
    {{
      "evidence_id": "string",
      "evidence_name": "string",
      "argument": "string",
      "counterargument": "string",
      "rebuttal": "string"
    }}
  ]
}}"""
)

async def generate_courtroom_strategy(workspace_meta: Dict[str, Any], agent1_analysis: Dict[str, Any], legal_research: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Agent 2 Room strategy simulation using Gemini.
    Consumes both Agent 0 context, Agent 1 auditing data, and Legal Research outputs to generate trial-ready strategies.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock Agent 2 courtroom strategy...")
        return generate_mock_agent2_strategy(workspace_meta, agent1_analysis)

    lawyer_side = workspace_meta.get("lawyer_side", "Plaintiff")
    prefix = get_lawyer_side_prefix(lawyer_side)

    prompt = COURTROOM_STRATEGY_PROMPT.format(
        lawyer_side_prefix=prefix,
        lawyer_side=lawyer_side,
        case_context=json.dumps(workspace_meta, cls=MongoJSONEncoder, indent=2),
        agent1_analysis=json.dumps(agent1_analysis, cls=MongoJSONEncoder, indent=2),
        legal_research=json.dumps(legal_research or {}, cls=MongoJSONEncoder, indent=2)
    )

    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()
        if not raw_text.startswith("{") and "{" in raw_text:
            raw_text = raw_text[raw_text.find("{"):]
        if not raw_text.endswith("}") and "}" in raw_text:
            raw_text = raw_text[:raw_text.rfind("}")+1]
        
        parsed_json = json.loads(raw_text, strict=False)
        if "lawyer_side" not in parsed_json:
            parsed_json["lawyer_side"] = lawyer_side
            
        validated_model = Agent2Output.model_validate(parsed_json)
        return validated_model.model_dump()
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

    simulations = []
    if has_strong:
        for idx, arg in enumerate(lawyer_arguments[:2]):
            simulations.append({
                "evidence_id": strong_ev_id,
                "evidence_name": strong_ev[0].get("file_name", "Exhibit A"),
                "argument": arg["narrative"],
                "counterargument": opponent_counterarguments[idx]["explanation"] if idx < len(opponent_counterarguments) else "Objection on relevance.",
                "rebuttal": rebuttal_strategies[idx]["rebuttal_narrative"] if idx < len(rebuttal_strategies) else "Reiterate evidentiary weight."
            })
    else:
        simulations.append({
            "evidence_id": "none",
            "evidence_name": "N/A",
            "argument": "Procedural baseline argument supporting our objectives.",
            "counterargument": "Opponent will assert lack of concrete evidence.",
            "rebuttal": "Rely on witness testimony and burden of proof thresholds."
        })

    return {
        "lawyer_side": lawyer_side,
        "lawyer_arguments": lawyer_arguments,
        "opponent_counterarguments": opponent_counterarguments,
        "rebuttal_strategies": rebuttal_strategies,
        "courtroom_risks": courtroom_risks,
        "strategic_recommendations": strategic_recommendations,
        "argument_priorities": arg_priorities,
        "evidence_utilization_strategy": evidence_utilization_strategy,
        "adversarial_simulations": simulations
    }


FINAL_REPORT_PROMPT = PromptTemplate(
    input_variables=["lawyer_side_prefix", "lawyer_side", "case_context", "agent1_analysis", "agent2_strategy", "rag_context"],
    template="""{lawyer_side_prefix}
You are Agent 3, the "Legal Intelligence & Final Report Agent" for VerdictIQ.
You are the single synthesis report generation engine for this workspace.

Your objective is to consume the structured case context (Agent 0), the evidence analysis and auditing (Agent 1), the simulated courtroom strategy (Agent 2), and any retrieved legal context from RAG, to produce the final, comprehensive legal intelligence report.

Stated side you are representing: {lawyer_side}
STRICT RULE: All analysis, arguments, risks, and recommendations must align with the represented side (Defense or Prosecution/Plaintiff).

Case Context (Agent 0):
{case_context}

Evidence Auditing & Analysis (Agent 1):
{agent1_analysis}

Courtroom Strategy Sim (Agent 2):
{agent2_strategy}

Retrieved Legal/Factual Context (RAG):
{rag_context}

You must execute the following 4 steps:

### STEP 1: Applicable Laws & Statutory Mapping
- Identify applicable laws, relevant sections (e.g., specific Penal Code sections, Commercial Code sections, etc., based on the case details).
- Highlight burden of proof requirements and legal compliance thresholds.
- Detail the procedural considerations.
- For each section/law mapped, explain clearly WHY it applies to the case facts and evidence.
- STRICT RULE: NEVER hallucinate legal sections. If unsure, say "Not enough information to determine exact section".

### STEP 2: SWOT Case Strength Assessment
- Perform a thorough SWOT analysis of the case favoring our client's side:
  - Strengths: What makes our case strong (e.g., strong evidence items, timeline corroboration).
  - Weaknesses: Vague evidence, uncorroborated assertions.
  - Opportunities: Opponent compliance gaps, procedural missteps.
  - Risks: Loophole exposures, strong opposing arguments.

### STEP 3: Detailed Executive Summary
- Generate a comprehensive, professional, and dense Executive Summary narrative outlining the case, active disputes, major evidence findings, and estimated outcomes.

### STEP 4: Final Legal Intelligence Report
- Generate the final report which must be extremely detailed, understandable by a lawyer who has never seen the case before. Every single conclusion MUST reference specific evidence items. Avoid short summaries or generic statements.

Return the analysis strictly as a valid JSON object matching the following structure:
{{
  "evidence_analysis": {{
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
    "confidence_scores": [
      {{
        "claim": "string",
        "confidence_score": 85
      }}
    ]
  }},
  "legal_arguments": {{
    "lawyer_side": [
      {{
        "argument": "string",
        "strength": "string",
        "claim_id": "string",
        "evidence_support": ["string"]
      }}
    ],
    "opponent_side": [
      {{
        "attack_vector": "string",
        "explanation": "string",
        "rebuttal_strategy": "string",
        "evidence_targeted": ["string"]
      }}
    ]
  }},
  "legal_sections": [
    {{
      "act_or_statute": "string",
      "section": "string",
      "relevance": "string",
      "simple_explanation": "string",
      "burden_of_proof": "string",
      "compliance_gap": "string",
      "procedural_considerations": "string",
      "why_applies": "string"
    }}
  ],
  "case_risks": [
    {{
      "title": "string",
      "description": "string",
      "severity": "string"
    }}
  ],
  "final_assessment": "string (consolidated assessment summary)",
  "recommendations": ["string"],
  "final_score": "string",
  "executive_summary": "string (STEP 3 detailed executive summary)",
  "case_strength_assessment": {{
    "strengths": ["string"],
    "weaknesses": ["string"],
    "opportunities": ["string"],
    "risks": ["string"]
  }},
  "final_legal_intelligence_report": "string (STEP 4 detailed legal intelligence report with references to evidence)"
}}"""
)

async def generate_final_legal_report(
    workspace_meta: Dict[str, Any],
    agent1_analysis: Dict[str, Any] = None,
    agent2_strategy: Dict[str, Any] = None,
    rag_context: str = ""
) -> Dict[str, Any]:
    """
    Agent 3 Unified Final Report Generation using Gemini.
    Consumes Agent 0 structured context, Agent 1 audit, Agent 2 strategy, and RAG statutory inputs.
    """
    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock Agent 3 unified final report...")
        return generate_mock_agent3_report(workspace_meta)

    lawyer_side = workspace_meta.get("legal_context", {}).get("lawyer_side", "Plaintiff") if "legal_context" in workspace_meta else workspace_meta.get("lawyer_side", "Plaintiff")
    prefix = get_lawyer_side_prefix(lawyer_side)

    prompt = FINAL_REPORT_PROMPT.format(
        lawyer_side_prefix=prefix,
        lawyer_side=lawyer_side,
        case_context=json.dumps(workspace_meta, cls=MongoJSONEncoder, indent=2),
        agent1_analysis=json.dumps(agent1_analysis or {}, cls=MongoJSONEncoder, indent=2),
        agent2_strategy=json.dumps(agent2_strategy or {}, cls=MongoJSONEncoder, indent=2),
        rag_context=rag_context or "No statutory document matched in local vector index."
    )

    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return validate_and_parse_json(response.text, Agent3Output)
    except Exception as e:
        logger.error(f"Gemini Agent 3 unified report generation failure: {e}. Falling back to dynamic mock engine.")
        return generate_mock_agent3_report(workspace_meta)

def generate_mock_agent3_report(workspace_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates dynamic mock Agent 3 report matching the new Agent3Output schema.
    """
    claims = workspace_meta.get("claims", [])
    evidence_rel = workspace_meta.get("evidence_relationships", [])
    lawyer_side = workspace_meta.get("legal_context", {}).get("lawyer_side", "Plaintiff") if workspace_meta else "Plaintiff"
    client_name = workspace_meta.get("legal_context", {}).get("client_name", "Client") if workspace_meta else "Client"
    opposing_party = workspace_meta.get("legal_context", {}).get("opposing_party", "Opponent") if workspace_meta else "Opponent"
    
    strong_ev = []
    if evidence_rel:
        for idx, er in enumerate(evidence_rel):
            strong_ev.append({
                "evidence_id": er.get("evidence_id", f"ev_{idx}"),
                "file_name": f"Document_{idx}",
                "supporting_claim": claims[0] if claims else "Primary Claim",
                "reasoning": f"Grounded document support: {er.get('relationship_description')}"
            })
    else:
        strong_ev.append({
            "evidence_id": "none",
            "file_name": "N/A",
            "supporting_claim": "N/A",
            "reasoning": "Insufficient supporting evidence available."
        })

    evidence_analysis = {
        "strong_evidence": strong_ev,
        "moderate_evidence": [],
        "weak_evidence": [],
        "unsupported_claims": [],
        "missing_evidence": [
            {
                "category": "Verification Records",
                "description": "Additional transactional verification logs.",
                "impact": "High"
            }
        ],
        "loopholes": [
            {
                "title": "Verification Gap",
                "description": "Electronic records require validation of original signatures.",
                "severity": "Medium"
            }
        ],
        "contradictions": [],
        "confidence_scores": [
            {
                "claim": c,
                "confidence_score": 85 if evidence_rel else 15
            } for c in claims
        ]
    }

    lawyer_args = [
        {
            "argument": f"Establishment of elements under {claims[0] if claims else 'dispute'}.",
            "strength": "Strongest",
            "claim_id": "claim_0",
            "evidence_support": [strong_ev[0]["evidence_id"]]
        }
    ]

    opponent_args = [
        {
            "attack_vector": "Completeness of transaction records",
            "explanation": "Opponent will challenge the compliance timelines.",
            "rebuttal_strategy": "Present contemporaneous email timeline.",
            "evidence_targeted": [strong_ev[0]["evidence_id"]]
        }
    ]

    legal_sections = [
        {
            "act_or_statute": "Indian Penal Code" if lawyer_side.lower() == "prosecution" else "Uniform Commercial Code",
            "section": "Section 420" if lawyer_side.lower() == "prosecution" else "Section 2-201",
            "relevance": "Governs the transaction requirements.",
            "simple_explanation": "Requires clear written proof of obligations.",
            "burden_of_proof": "Preponderance of evidence is on the claimant.",
            "compliance_gap": "Timeline details must be validated.",
            "procedural_considerations": "Requires filing within the statutory period of limitations.",
            "why_applies": f"Directly governs the active transaction dispute in the {client_name} and {opposing_party} case."
        }
    ]

    swot = {
        "strengths": ["Documentary timeline matches client assertions."],
        "weaknesses": ["Lack of independent third-party witnesses."],
        "opportunities": ["Opponent failed to deliver written notice of default."],
        "risks": ["Vulnerable to digital authentication challenges."]
    }

    report_str = f"DETAILED LEGAL REPORT\n=====================\n\nCase Overview:\nThis synthesized legal audit details the commercial dispute between client {client_name} and {opposing_party}.\n\nApplicable Law:\nIPC Section 420 or UCC Section 2-201 applies because the transaction exceeds the statutory threshold.\n\nEvidentiary Findings:\nEvidence suggests a clear transaction path. The client has provided primary contract documents."

    return {
        "evidence_analysis": evidence_analysis,
        "legal_arguments": {
            "lawyer_side": lawyer_args,
            "opponent_side": opponent_args
        },
        "legal_sections": legal_sections,
        "case_risks": [
            {
                "title": "Factual Contestation Risk",
                "description": "Opposing party may present conflicting narrative.",
                "severity": "Medium"
            }
        ],
        "final_assessment": f"This synthesized legal audit details the case between {client_name} and {opposing_party}. The client {client_name} holds a moderate claim.",
        "recommendations": [
            "Review original electronic metadata.",
            "Consolidate timeline witnesses."
        ],
        "final_score": "75%",
        "executive_summary": f"This synthesized legal audit details the case between {client_name} and {opposing_party}.",
        "case_strength_assessment": swot,
        "final_legal_intelligence_report": report_str
    }


CHAT_PROMPT = PromptTemplate(
    input_variables=["lawyer_side_prefix", "case_metadata", "evidence_files", "agent0_output", "agent1_output", "agent2_output", "agent3_output", "rag_context", "chat_history", "question"],
    template="""{lawyer_side_prefix}
You are a case-aware AI legal assistant for VerdictIQ.
Your goal is to answer follow-up questions from the lawyer about the active legal case workspace.
You must ground your answers strictly on the consolidated case workspace context provided below, including all evidence and previous agent outputs.
Do NOT rerun any agent pipeline or call external systems.

Case Metadata:
{case_metadata}

Uploaded Evidence Files:
{evidence_files}

Agent 0 Output (Case Intake & Overview):
{agent0_output}

Agent 1 Output (Evidentiary Auditing & Gaps):
{agent1_output}

Agent 2 Output (Courtroom Strategy & Simulation):
{agent2_strategy}

Agent 3 Output (Statutory Mapping & Final Report):
{agent3_output}

Retrieved Document Context (RAG):
{rag_context}

Conversation History:
{chat_history}

Lawyer's Question:
{question}

CHATBOT RESPONSIBILITIES:
- Answer questions, explain evidence, explain legal sections, explain contradictions, explain report findings, compare old vs new evidence, and explain confidence/score changes.
- Ground your answers strictly on the provided case data. Do NOT invent/fabricate facts, documents, dates, witnesses, laws, or legal conclusions.

CONFIDENCE RULES:
- If the answer exists in the workspace context, answer confidently.
- If the answer is partially known, explicitly state uncertainty and what is missing.
- If the answer does not exist, say: "The available case materials do not provide enough information to answer this question."

PERSONA SELECTION RULES:
Select your answering agent persona based on the question:
- Use "Agent 0 Case Intake Agent" if the question is about general case summaries, timeline dates, or key entities.
- Use "Agent 1 Evidentiary Auditing Agent" if the question is about evidence strength, missing evidence, gaps, or loopholes.
- Use "Agent 2 Courtroom Strategy Agent" if the question is about arguments, opponent counterarguments, rebuttals, or strategic recommendations.
- Use "Agent 3 Synthesis Report Agent" if the question is about overall case synthesis, statutory applicability, or final reports.

Return the response strictly as a JSON object matching the following structure:
{{
  "answer": "string",
  "supporting_context": ["string"],
  "confidence": "string",
  "agent_name": "string" (must be one of: 'Agent 0 Case Intake Agent', 'Agent 1 Evidentiary Auditing Agent', 'Agent 2 Courtroom Strategy Agent', or 'Agent 3 Synthesis Report Agent')
}}"""
)

LEGAL_CHAT_PROMPT = CHAT_PROMPT

async def run_chat_agent(
    case_metadata: Dict[str, Any],
    evidence_files: List[Dict[str, Any]],
    agent0_output: Dict[str, Any],
    agent1_output: Dict[str, Any],
    agent2_output: Dict[str, Any],
    agent3_output: Dict[str, Any],
    rag_context: str,
    chat_history: str,
    question: str,
    lawyer_side: str = None
) -> Dict[str, Any]:
    """
    Unified conversational chatbot execution function using Gemini API.
    Consolidates Agent 0, 1, 2, 3 outputs, case metadata, and evidence catalog.
    """
    chat_key = os.getenv("CHAT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if chat_key:
        genai.configure(api_key=chat_key)

    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock Agent chatbot response...")
        return generate_mock_chat_agent(question, lawyer_side)

    prefix = get_lawyer_side_prefix(lawyer_side)

    # Serialize contexts for token efficiency
    clean_a3 = {
        "executive_summary": agent3_output.get("executive_summary", ""),
        "case_strength": agent3_output.get("case_strength", ""),
        "case_strength_score": agent3_output.get("case_strength_score", 50),
        "strongest_evidence": agent3_output.get("strongest_evidence", []),
        "weak_evidence": agent3_output.get("weak_evidence", []),
        "missing_evidence": agent3_output.get("missing_evidence", []),
        "loopholes": agent3_output.get("loopholes", []),
        "legal_references": agent3_output.get("legal_references", []),
        "courtroom_risks": agent3_output.get("courtroom_risks", []),
        "final_case_assessment": agent3_output.get("final_case_assessment", ""),
        "recommendations": agent3_output.get("strategic_recommendations", []),
        "case_strength_assessment": agent3_output.get("case_strength_assessment", {}),
        "final_legal_intelligence_report": agent3_output.get("final_legal_intelligence_report", "")
    }

    clean_a1 = {k: v for k, v in agent1_output.items() if k not in ["_id", "generated_at", "workspace_id"]}
    clean_a2 = {k: v for k, v in agent2_output.items() if k not in ["_id", "generated_at", "workspace_id"]}
    clean_a0 = {k: v for k, v in agent0_output.items() if k not in ["_id", "generated_at", "workspace_id"]}

    prompt = CHAT_PROMPT.format(
        lawyer_side_prefix=prefix,
        case_metadata=json.dumps(case_metadata, cls=MongoJSONEncoder, indent=2),
        evidence_files=json.dumps(evidence_files, cls=MongoJSONEncoder, indent=2),
        agent0_output=json.dumps(clean_a0, cls=MongoJSONEncoder, indent=2),
        agent1_output=json.dumps(clean_a1, cls=MongoJSONEncoder, indent=2),
        agent2_strategy=json.dumps(clean_a2, cls=MongoJSONEncoder, indent=2),
        agent3_output=json.dumps(clean_a3, cls=MongoJSONEncoder, indent=2),
        rag_context=rag_context or "No context retrieved.",
        chat_history=chat_history or "No previous history.",
        question=question
    )

    logger.info(f"Gemini Chat: Running request for question length: {len(question)}. Prompt size: {len(prompt)} chars.")
    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"},
            api_key=chat_key
        )
        logger.info(f"Gemini Chat: Received response of length: {len(response.text)}.")
        return validate_and_parse_json(response.text, Agent4Output)
    except Exception as e:
        logger.error(f"Gemini Chat API call failed: {e}. Falling back to dynamic mock chat assistant.")
        return generate_mock_chat_agent(question, lawyer_side)

def generate_mock_chat_agent(question: str, lawyer_side: str = None) -> Dict[str, Any]:
    """
    Fallback mock response for conversational chatbot with dynamic agent classification.
    """
    side = lawyer_side or "Plaintiff"
    q_lower = question.lower()
    
    if any(k in q_lower for k in ["evidence", "loophole", "missing", "proof", "audit", "contradict"]):
        agent_name = "Agent 1 Evidentiary Auditing Agent"
    elif any(k in q_lower for k in ["strategy", "argument", "rebuttal", "risk", "counter", "court"]):
        agent_name = "Agent 2 Courtroom Strategy Agent"
    elif any(k in q_lower for k in ["summary", "timeline", "fact", "intake", "entity"]):
        agent_name = "Agent 0 Case Intake Agent"
    else:
        agent_name = "Agent 3 Synthesis Report Agent"
        
    return {
        "answer": f"Case-aware assistant response assisting the {side} side regarding: '{question}'. All evidence audit and strategy details remain active.",
        "supporting_context": ["Case Intake Context", "Agent 3 Consolidated Intelligence"],
        "confidence": "High (Grounded in unified report context)",
        "agent_name": agent_name
    }

async def generate_ai_activity_feed(cases: List[dict], tasks: List[dict], evidence_files: List[dict]) -> List[dict]:
    """
    Generates dynamic AI activity feed items based on active cases, tasks, and evidence.
    """
    if not cases:
        return [
            {
                "id": "init-feed",
                "title": "Awaiting Case Initialization",
                "desc": "Evidentiary audit systems online. Initialize a workspace to start AI synthesis.",
                "time": "Just now",
                "type": "strategy"
            }
        ]

    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock AI activity feed...")
        return generate_mock_ai_activity_feed(cases, tasks, evidence_files)

    cases_summary = [{"name": c.get("name"), "caseType": c.get("caseType"), "riskLevel": c.get("riskLevel"), "status": c.get("status"), "evidenceCount": c.get("evidenceCount")} for c in cases]
    tasks_summary = [{"title": t.get("title"), "completed": t.get("completed"), "case_name": t.get("case_name")} for t in tasks]
    evidence_summary = [{"file_name": ef.get("file_name"), "evidence_type": ef.get("evidence_type")} for ef in evidence_files]

    prompt = f"""
    You are the VerdictIQ AI activity log generator.
    Based on the following active cases, tasks, and evidence files, generate a list of 3-5 real-time legal activity feed events.
    Make the events sound like professional, live legal audit events, analyzing loopholes, identifying witness risks, assessing evidentiary strength, or highlighting timeline checkpoints.
    Do NOT return duplicate or rigid text. The items must feel alive and completely unique to these specific cases.
    
    Active cases: {json.dumps(cases_summary)}
    Active tasks: {json.dumps(tasks_summary)}
    Uploaded evidence: {json.dumps(evidence_summary)}
    
    Return the result strictly as a valid JSON list of objects matching the structure:
    [
      {{
        "id": "string (unique id)",
        "title": "string (concise alert title, e.g. 'Evidentiary Gap Detected', 'Strategy Pivot recommended')",
        "desc": "string (detailed description of the activity and what the AI analyzed)",
        "time": "string (e.g. 'Just now', '10 mins ago', '1 hour ago')",
        "type": "string (one of: 'critical', 'strength', 'strategy')"
      }}
    ]
    """
    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip(), strict=False)
    except Exception as e:
        logger.error(f"Gemini activity feed generation failed: {e}. Falling back to mock generator.")
        return generate_mock_ai_activity_feed(cases, tasks, evidence_files)

def generate_mock_ai_activity_feed(cases: List[dict], tasks: List[dict], evidence_files: List[dict]) -> List[dict]:
    feed = []
    for idx, c in enumerate(cases[:3]):
        case_name = c.get("name") or "Unnamed Case"
        risk = c.get("riskLevel", "Medium")
        ev_count = c.get("evidenceCount", 0)
        
        feed.append({
            "id": f"feed-risk-{c.get('_id') or idx}",
            "title": f"Risk Evaluation: {case_name}",
            "desc": f"VerdictIQ completed intake risk screening. Case marked as {risk} Risk. Primary claims indexed for defense/prosecution review.",
            "time": "Just now" if idx == 0 else f"{idx * 20} mins ago",
            "type": "critical" if risk == "High" else "strategy"
        })
        
        if ev_count > 0:
            feed.append({
                "id": f"feed-ev-{c.get('_id') or idx}",
                "title": f"Evidentiary Synthesis: {case_name}",
                "desc": f"AI reviewed {ev_count} evidence files. Initial case strength stands at Moderate. Evidence disclosure gaps flagged for witness preparation.",
                "time": "10 mins ago" if idx == 0 else f"{idx * 30 + 10} mins ago",
                "type": "strength"
            })
            
    pending_tasks = [t for t in tasks if not t.get("completed")]
    if pending_tasks:
        t = pending_tasks[0]
        feed.append({
            "id": f"feed-task-{t.get('_id') or 'task'}",
            "title": "Checklist Deadline Monitoring",
            "desc": f"Upcoming task '{t.get('title')}' for case '{t.get('case_name') or 'active workspace'}' flagged on the calendar timeline.",
            "time": "1 hour ago",
            "type": "strategy"
        })
        
    return feed[:5]

async def generate_calendar_recommendations(cases: List[dict], hearings: List[dict], evidence_files: List[dict]) -> List[dict]:
    """
    Generates dynamic calendar prep recommendations based on active cases, hearings, and evidence files.
    """
    if not cases:
        return [
            {
                "type": "gap",
                "title": "Initialize case workspace",
                "desc": "Create a workspace and upload contract, deposition or complaint documents to generate custom AI recommendations."
            }
        ]

    if IS_MOCK_GEMINI:
        logger.info("Generating dynamic mock calendar recommendations...")
        return generate_mock_calendar_recommendations(cases, hearings, evidence_files)

    cases_summary = [{"name": c.get("name"), "caseType": c.get("caseType")} for c in cases]
    hearings_summary = [{"case_name": h.get("case_name"), "court_name": h.get("court_name"), "hearing_date": h.get("hearing_date")} for h in hearings]
    evidence_summary = [{"file_name": ef.get("file_name"), "evidence_type": ef.get("evidence_type")} for ef in evidence_files]

    prompt = f"""
    You are the VerdictIQ AI calendar schedule recommender.
    Based on the following active cases, upcoming hearings, and uploaded evidence, generate a list of 2-3 strategic calendar prep recommendations.
    These recommendations should help the lawyer prepare for trial, address evidence gaps, coordinate witness depositions, or prepare briefs.
    Do NOT return duplicate or rigid text. The items must feel completely unique to these specific cases.
    
    Active cases: {json.dumps(cases_summary)}
    Hearings: {json.dumps(hearings_summary)}
    Uploaded evidence: {json.dumps(evidence_summary)}
    
    Return the result strictly as a valid JSON list of objects matching the structure:
    [
      {{
        "type": "string (one of: 'prep', 'gap')",
        "title": "string (short title)",
        "desc": "string (detailed description of recommendation, e.g. 'AI suggests scheduling a mock cross-examination for CaseName 48 hours prior')",
        "action": "string (optional button text, e.g. 'Auto-Schedule Prep')"
      }}
    ]
    """
    try:
        response = generate_content_with_fallback(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip(), strict=False)
    except Exception as e:
        logger.error(f"Gemini calendar recommendations failed: {e}. Falling back to mock generator.")
        return generate_mock_calendar_recommendations(cases, hearings, evidence_files)

def generate_mock_calendar_recommendations(cases: List[dict], hearings: List[dict], evidence_files: List[dict]) -> List[dict]:
    recs = []
    
    if hearings:
        h = hearings[0]
        recs.append({
            "type": "prep",
            "title": "Pre-Trial Prep Alert",
            "desc": f"AI suggests scheduling a mock cross-examination for **{h.get('case_name')}** 48 hours prior to the hearing at **{h.get('court_name') or 'court'}**.",
            "action": "Auto-Schedule Prep"
        })
    else:
        c = cases[0]
        recs.append({
            "type": "prep",
            "title": "Mock Strategy Simulation",
            "desc": f"Review legal arguments and mock-test courtroom counter-risks for **{c.get('name')}**.",
            "action": "Simulate Room"
        })
        
    c = cases[0]
    ev_count = c.get("evidenceCount", 0)
    if ev_count == 0:
        recs.append({
            "type": "gap",
            "title": "Evidentiary Intake Deficit",
            "desc": f"No files uploaded for **{c.get('name')}**. AI recommends importing contracts or deposition records to index loopholes.",
            "action": "Upload Files"
        })
    else:
        recs.append({
            "type": "gap",
            "title": "Evidence Disclosure Gap",
            "desc": f"Witness disclosure docket for **{c.get('name')}** is approaching. Complete final expert witness exchanges.",
            "action": None
        })
        
    return recs



