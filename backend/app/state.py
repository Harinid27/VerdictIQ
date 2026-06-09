from typing import TypedDict, Dict, Any, Optional

class VerdictState(TypedDict):
    workspace_id: str
    lawyer_side: Optional[str]
    case_context: Optional[Dict[str, Any]]
    agent0_output: Optional[Dict[str, Any]]
    agent1_output: Optional[Dict[str, Any]]
    legal_research_output: Optional[Dict[str, Any]]
    agent2_output: Optional[Dict[str, Any]]
    agent3_output: Optional[Dict[str, Any]]
    current_stage: Optional[str]
