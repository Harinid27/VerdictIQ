from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- AGENT 0 SCHEMAS ---
class TimelineEvent(BaseModel):
    date: str = Field(..., description="Date of the event/incident in YYYY-MM-DD or specific context")
    incident: str = Field(..., description="Detailed description of what occurred")
    transaction_reference: str = Field(..., description="Associated transaction ID, invoice, or receipt number, if applicable. If none, put 'N/A'")
    legal_event: str = Field(..., description="Type of event, e.g., Transaction, Breach, Demand Letter, Notice, Filing")

class KeyEntity(BaseModel):
    name: str = Field(..., description="Full name of person or organization")
    type: str = Field(..., description="Entity type, e.g., Person, Corporation, Government Body, Bank")
    role: str = Field(..., description="Legal role in the case, e.g., Plaintiff, Defendant, Witness, Auditor, Contract Signatory")

class EvidenceRelationship(BaseModel):
    evidence_id: str = Field(..., description="Identifier or filename of the evidence document")
    claim_id: str = Field(..., description="Identifier of the claim it links to (e.g. claim_0, claim_1)")
    relationship_description: str = Field(..., description="Precise narrative explaining how this evidence supports or refutes the claim")

class LegalContext(BaseModel):
    case_title: str = Field(..., description="Title of the case/workspace")
    case_type: str = Field(..., description="Type of dispute, e.g. Contract breach, intellectual property, corporate fraud")
    lawyer_side: str = Field(..., description="Side representing, either 'Defense' or 'Plaintiff/Prosecution'")
    client_name: str = Field(..., description="Name of our client")
    opposing_party: str = Field(..., description="Name of opposing party")

class Agent0Output(BaseModel):
    case_summary: str = Field(..., description="Comprehensive objective synthesis of the case landscape based solely on facts")
    claims: List[str] = Field(..., description="List of primary legal claims or defenses identified")
    timeline: List[TimelineEvent] = Field(..., description="Chronological timeline of verified events")
    key_entities: List[KeyEntity] = Field(..., description="List of key entities and their legal roles")
    evidence_relationships: List[EvidenceRelationship] = Field(..., description="Mapping of evidence documents to claims")
    objectives: List[str] = Field(..., description="Strategic litigation objectives for our client")
    concerns: List[str] = Field(..., description="Initial areas of concern or exposure for our client")
    case_overview: Optional[str] = Field(default="", description="Case Overview: Detailed legal analyst's case briefing summary narrative.")
    timeline_of_events: Optional[List[TimelineEvent]] = Field(default=[], description="Timeline of Events: Chronological timeline of verified events.")
    people_involved: Optional[List[KeyEntity]] = Field(default=[], description="People Involved: Key people/entities and their roles in the case.")
    relationships: Optional[List[str]] = Field(default=[], description="Relationships: Descriptions of key relationships between entities/events.")
    key_claims: Optional[List[str]] = Field(default=[], description="Key Claims: Primary legal claims or defenses identified.")
    important_facts: Optional[List[str]] = Field(default=[], description="Important Facts: Detailed key facts established by evidence.")
    evidence_inventory: Optional[List[str]] = Field(default=[], description="Evidence Inventory: Descriptions of evidence, NOT raw filenames.")
    open_questions: Optional[List[str]] = Field(default=[], description="Open Questions: Gaps or unresolved questions to investigate.")
    case_understanding_score: Optional[int] = Field(default=0, description="Confidence score (0-100) of the extracted facts.")


# --- AGENT 1 SCHEMAS ---
class DetailedEvidenceItem(BaseModel):
    evidence_id: str = Field(..., description="Evidence ID or filename")
    file_name: str = Field(..., description="Name of the file")
    supporting_claim: str = Field(..., description="The claim this evidence supports")
    reasoning: str = Field(..., description="Courtroom reasoning explaining why this evidence qualifies for this tier")

class WeakEvidenceItem(BaseModel):
    evidence_id: str = Field(..., description="Evidence ID or filename")
    file_name: str = Field(..., description="Name of the file")
    reasoning: str = Field(..., description="Explanatory reasons why this evidence is weak or easily contested")

class UnsupportedClaimItem(BaseModel):
    claim: str = Field(..., description="The claim lacking proof")
    reasoning: str = Field(..., description="Explanation highlighting the complete absence of corroborating documents")

class MissingEvidenceItem(BaseModel):
    category: str = Field(..., description="Type of missing proof, e.g. Financial records, communications, witness testimony")
    description: str = Field(..., description="Exact details of the missing document/record")
    impact: str = Field(..., description="Impact level and rationale (e.g. Critical, High, Medium)")

class LoopholeItem(BaseModel):
    title: str = Field(..., description="Brief title of the loophole or gap")
    description: str = Field(..., description="Explanation of how the opposition could exploit this loophole")
    severity: str = Field(..., description="Severity level: Critical, High, Medium, Low")

class ContradictionItem(BaseModel):
    item_a: str = Field(..., description="First statement/timeline/evidence fact")
    item_b: str = Field(..., description="Second conflicting statement/timeline/evidence fact")
    discrepancy: str = Field(..., description="Clear explanation of the logical mismatch or contradiction")

class RiskAnalysisDetails(BaseModel):
    risk_level: str = Field(..., description="Overall risk level: Low Risk, Medium Risk, High Risk, Critical Risk")
    vulnerabilities: List[str] = Field(..., description="Key vulnerabilities in our case strategy")
    assumptions: List[str] = Field(..., description="Unsupported assumptions counsel is currently making")

class ClaimConfidenceScore(BaseModel):
    claim: str = Field(..., description="The legal claim text")
    confidence_score: int = Field(..., description="Confidence score from 0 to 100 based on supporting evidence strength")

class EvidenceEvaluationItem(BaseModel):
    evidence_id: str = Field(..., description="Evidence ID or filename")
    file_name: str = Field(..., description="Name of the file")
    classification: str = Field(..., description="Strong, Moderate, or Weak")
    why_strong: str = Field(..., description="Why the evidence is strong (or N/A)")
    why_weak: str = Field(..., description="Why the evidence is weak (or N/A)")
    assumptions: str = Field(..., description="What assumptions exist regarding this evidence")
    reliability_level: str = Field(..., description="Reliability level (e.g., High, Medium, Low)")
    possible_challenges: str = Field(..., description="Possible challenges or objections by opposing counsel")

class Agent1Output(BaseModel):
    strong_evidence: List[DetailedEvidenceItem] = Field(..., description="Evidence that directly proves key claims")
    moderate_evidence: List[DetailedEvidenceItem] = Field(..., description="Circumstantial or partially unverified evidence")
    weak_evidence: List[WeakEvidenceItem] = Field(..., description="Easily contested or irrelevant evidence")
    unsupported_claims: List[UnsupportedClaimItem] = Field(..., description="Claims with zero document backing")
    missing_evidence: List[MissingEvidenceItem] = Field(..., description="Crucial evidentiary gaps that need to be requested")
    loopholes: List[LoopholeItem] = Field(..., description="Factual or process loopholes in current case narrative")
    contradictions: List[ContradictionItem] = Field(..., description="Internal discrepancies or mismatching facts")
    risk_analysis: RiskAnalysisDetails = Field(..., description="Aggregated risk assessment details")
    risk_level: str = Field(..., description="Overall risk level, e.g., 'Medium Risk'")
    confidence_scores: List[ClaimConfidenceScore] = Field(..., description="Evidence-grounded score per claim")
    evidence_relationships: List[EvidenceRelationship] = Field(..., description="Verified mappings of evidence documents to claims")
    evidence_evaluations: Optional[List[EvidenceEvaluationItem]] = Field(default=[], description="Evaluation details for each evidence item")
    investigative_gaps: Optional[List[str]] = Field(default=[], description="Investigative gaps identified in the case")
    reliability_concerns: Optional[List[str]] = Field(default=[], description="Reliability concerns for evidence or witnesses")
    alternative_interpretations: Optional[List[str]] = Field(default=[], description="Possible alternative interpretations of facts/evidence")


# --- LEGAL RESEARCH SCHEMAS ---
class StatuteReference(BaseModel):
    statute_name: str = Field(..., description="Name of act or code, e.g., Uniform Commercial Code")
    section: str = Field(..., description="Exact section/clause, e.g., Section 2-201")
    jurisdiction: str = Field(..., description="Applicable jurisdiction, e.g., Delaware corporate law, US federal court")
    description: str = Field(..., description="Brief quote or summary of the statutory rule")
    applicability_to_case: str = Field(..., description="Direct analysis of how this section applies to the claims/evidence")

class CasePrecedent(BaseModel):
    case_name: str = Field(..., description="Title of precedent case, e.g., Hadley v Baxendale")
    citation: str = Field(..., description="Official legal reporter citation, e.g., 9 Exch. 341")
    summary: str = Field(..., description="Key facts of the precedent case")
    holding: str = Field(..., description="Legal rule or decision held by the court")
    key_takeaway_for_counsel: str = Field(..., description="Strategic implications and how it helps/hurts client side")

class LegalResearchOutput(BaseModel):
    relevant_statutes: List[StatuteReference] = Field(..., description="List of applicable laws and statutory provisions")
    precedent_cases: List[CasePrecedent] = Field(..., description="List of binding or persuasive case law precedents")


# --- AGENT 2 SCHEMAS ---
class LawyerArgument(BaseModel):
    claim_id: str = Field(..., description="Claim ID this argument addresses")
    argument_title: str = Field(..., description="Short catchphrase for the argument")
    narrative: str = Field(..., description="Draft of the argument logic in simple, professional terms")
    evidence_support: List[str] = Field(..., description="List of filenames or IDs of supporting documents")

class OpponentCounterargument(BaseModel):
    claim_id: str = Field(..., description="Claim ID targeted")
    attack_vector: str = Field(..., description="Expected line of defense or attack by the opponent")
    explanation: str = Field(..., description="Detailed narrative of the opposition's challenge")
    evidence_targeted: List[str] = Field(..., description="Evidence items they will likely challenge or object to")

class RebuttalStrategy(BaseModel):
    counterargument_targeted: str = Field(..., description="Title or key claim of the opponent's counterargument")
    rebuttal_narrative: str = Field(..., description="Our proposed counter-argument and factual explanation")
    mitigation_steps: List[str] = Field(..., description="Tasks/investigations needed to secure this rebuttal")

class ArgumentPriorities(BaseModel):
    strongest_arguments: List[str] = Field(..., description="Fully corroborated, high confidence arguments")
    moderate_arguments: List[str] = Field(..., description="Circumstantial or moderate arguments")
    risky_arguments: List[str] = Field(..., description="Vulnerable arguments requiring caution")

class EvidenceUtilization(BaseModel):
    evidence_id: str = Field(..., description="File ID or filename")
    sequence_order: int = Field(..., description="Chronological sequence order for courtroom presentation")
    presentation_guidance: str = Field(..., description="Advice on how counsel should present this specific exhibit")

class AdversarialSimulation(BaseModel):
    evidence_id: str = Field(..., description="Evidence ID or filename referenced")
    evidence_name: str = Field(..., description="Evidence document name")
    argument: str = Field(..., description="Section A: Lawyer Argument (strongest argument for our side referencing this evidence)")
    counterargument: str = Field(..., description="Section B: Defense Counterargument (strongest opposing argument attacking this evidence's weaknesses)")
    rebuttal: str = Field(..., description="Section C: Rebuttal (our response to the counterargument)")

class Agent2Output(BaseModel):
    lawyer_side: str = Field(..., description="Represented side, e.g. 'Defense'")
    lawyer_arguments: List[LawyerArgument] = Field(..., description="Core arguments backing client side")
    opponent_counterarguments: List[OpponentCounterargument] = Field(..., description="Simulated adversary counter-arguments")
    rebuttal_strategies: List[RebuttalStrategy] = Field(..., description="Planned rebuttals to predicted counter-arguments")
    courtroom_risks: List[LoopholeItem] = Field(..., description="Identified litigation risks")
    strategic_recommendations: List[str] = Field(..., description="Strategic recommendations for litigation direction")
    argument_priorities: ArgumentPriorities = Field(..., description="Categorization of argument confidence levels")
    evidence_utilization_strategy: List[EvidenceUtilization] = Field(..., description="Ordered plan of exhibit presentation")
    adversarial_simulations: Optional[List[AdversarialSimulation]] = Field(default=[], description="Section A, B, and C courtroom exchange simulation for all major evidence items")


# --- AGENT 3 SCHEMAS ---
class FinalEvidenceAnalysis(BaseModel):
    strong_evidence: List[DetailedEvidenceItem] = Field(..., description="Evidence that directly proves key claims")
    moderate_evidence: List[DetailedEvidenceItem] = Field(..., description="Circumstantial or partially unverified evidence")
    weak_evidence: List[WeakEvidenceItem] = Field(..., description="Easily contested or irrelevant evidence")
    unsupported_claims: List[UnsupportedClaimItem] = Field(..., description="Claims with zero document backing")
    missing_evidence: List[MissingEvidenceItem] = Field(..., description="Crucial evidentiary gaps that need to be requested")
    loopholes: List[LoopholeItem] = Field(..., description="Factual or process loopholes in current case narrative")
    contradictions: List[ContradictionItem] = Field(..., description="Internal discrepancies or mismatching facts")
    confidence_scores: List[ClaimConfidenceScore] = Field(..., description="Evidence-grounded score per claim")

class LawyerArgumentDetail(BaseModel):
    argument: str = Field(..., description="The argument narrative")
    strength: str = Field(..., description="Argument confidence level (e.g. Strongest, Moderate, Risky)")
    claim_id: str = Field(..., description="Claim ID this argument addresses")
    evidence_support: List[str] = Field(..., description="Evidence document names/IDs backing this argument")

class OpponentArgumentDetail(BaseModel):
    attack_vector: str = Field(..., description="Expected line of defense or attack by opponent")
    explanation: str = Field(..., description="Detailed narrative of opposition challenge")
    rebuttal_strategy: str = Field(..., description="Proposed rebuttal narrative and factual explanation")
    evidence_targeted: List[str] = Field(..., description="Evidence items they will likely challenge")

class LegalArguments(BaseModel):
    lawyer_side: List[LawyerArgumentDetail] = Field(..., description="List of arguments backing client side")
    opponent_side: List[OpponentArgumentDetail] = Field(..., description="List of opposing counterarguments and rebuttals")

class LegalSectionMap(BaseModel):
    act_or_statute: str = Field(..., description="Name of act or code, e.g., Indian Penal Code, CPC, CrPC or jurisdiction-specific laws")
    section: str = Field(..., description="Exact section/clause, e.g., Section 302, Section 420")
    relevance: str = Field(..., description="Direct analysis of how this section applies to the claims/evidence")
    simple_explanation: str = Field(..., description="Simple explanation of applicability in simple language")
    burden_of_proof: str = Field(..., description="Burden of proof requirements")
    compliance_gap: str = Field(..., description="Legal thresholds and compliance gaps")
    procedural_considerations: Optional[str] = Field(default="N/A", description="Procedural considerations for this section")
    why_applies: Optional[str] = Field(default="N/A", description="Detailed explanation of why this law/section applies")

class CaseRiskDetail(BaseModel):
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Explanation of risk")
    severity: str = Field(..., description="Severity level: Critical, High, Medium, Low")

class SWOTAssessment(BaseModel):
    strengths: List[str] = Field(..., description="SWOT: Strengths of the case")
    weaknesses: List[str] = Field(..., description="SWOT: Weaknesses of the case")
    opportunities: List[str] = Field(..., description="SWOT: Opportunities for strategy")
    risks: List[str] = Field(..., description="SWOT: Risks and threats")

class Agent3Output(BaseModel):
    evidence_analysis: FinalEvidenceAnalysis = Field(..., description="Analysis of the case evidence and reliability")
    legal_arguments: LegalArguments = Field(..., description="Arguments for lawyer side and opponent side")
    legal_sections: List[LegalSectionMap] = Field(..., description="Relevant legal provisions and statutory mapping")
    case_risks: List[CaseRiskDetail] = Field(..., description="Vulnerabilities and strategic risks in the case")
    final_assessment: str = Field(..., description="Executive summary and overall case assessment")
    recommendations: List[str] = Field(..., description="Strategic litigation recommendations")
    final_score: str = Field(..., description="Final case assessment score (0-100 or favorability rating, e.g. '85%')")
    executive_summary: Optional[str] = Field(default="", description="STEP 3: Detailed Executive Summary of the case")
    case_strength_assessment: Optional[SWOTAssessment] = Field(default=None, description="STEP 2: SWOT Case Strength Assessment")
    final_legal_intelligence_report: Optional[str] = Field(default="", description="STEP 4: Comprehensive, detailed Final Legal Intelligence Report referencing evidence")


class Agent4Output(BaseModel):
    answer: str = Field(..., description="Conversational answer to the lawyer's question, grounded strictly in the provided case data")
    supporting_context: List[str] = Field(..., description="Fact snippets, evidence files, or legal citations supporting the answer")
    confidence: str = Field(..., description="Confidence level: High, Medium, or Low, explaining any missing gaps")
    agent_name: str = Field(..., description="Name of the agent answering: Agent 0 Case Intake Agent, Agent 1 Evidentiary Auditing Agent, Agent 2 Courtroom Strategy Agent, or Agent 3 Synthesis Report Agent")

