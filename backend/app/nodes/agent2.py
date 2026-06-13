import logging
from typing import Dict, Any

from app.state import VerdictState
from app.services.gemini_service import generate_courtroom_strategy

logger = logging.getLogger(__name__)

async def agent2_node(state: VerdictState) -> VerdictState:
    """
    LangGraph node: agent2_node
    Role: Courtroom Strategy & Adversarial Reasoning Agent
    Responsibilities:
      - Uses Agent 1 findings and Agent 0 case details.
      - Generates adversarial simulations including arguments, counterarguments, and rebuttals.
      - Produces strategic courtroom recommendations, argument priorities, and exhibit utilization order.
    """
    workspace_id = state.get("workspace_id")
    agent0_output = state.get("agent0_output")
    agent1_output = state.get("agent1_output")

    logger.info(f"LangGraph: Starting agent2_node (Courtroom Strategy Agent) for workspace_id: {workspace_id}")

    if not agent0_output:
        raise ValueError("Agent 0 structured context is missing in state.")
    if not agent1_output:
        raise ValueError("Agent 1 auditing output is missing in state.")

    # Call Gemini service to perform Agent 2 courtroom strategy simulation
    try:
        strategy_result = await generate_courtroom_strategy(
            workspace_meta=agent0_output,
            agent1_analysis=agent1_output
        )
    except Exception as e:
        logger.error(f"Failed to generate Agent 2 strategy: {e}")
        raise ValueError(f"Agent 2 strategy generation failed: {e}")

    # Return updated state
    return {
        **state,
        "agent2_output": strategy_result,
        "current_stage": "agent2_completed"
    }
