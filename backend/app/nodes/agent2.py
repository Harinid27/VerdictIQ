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
      - Simulates courtroom reasoning and adversary attacks.
      - Generates evidence-grounded arguments for the client.
      - Predicts opposing counsel attacks (counterarguments).
      - Develops rebuttal narratives and mitigation steps.
      - Sequences evidence utilization strategy.
    """
    workspace_id = state.get("workspace_id")
    agent0_output = state.get("agent0_output")
    agent1_output = state.get("agent1_output")

    logger.info(f"LangGraph: Starting agent2_node for workspace_id: {workspace_id}")

    if not agent0_output or not agent1_output:
        raise ValueError("Agent 0 or Agent 1 outputs are missing in state.")

    # Call Gemini to simulate courtroom strategy
    try:
        strategy_result = await generate_courtroom_strategy(
            workspace_meta=agent0_output, 
            agent1_analysis=agent1_output
        )
    except Exception as e:
        logger.error(f"Failed to generate Agent 2 strategy: {e}")
        raise ValueError(f"Agent 2 courtroom strategy execution failed: {e}")

    lawyer_side = state.get("lawyer_side") or "Plaintiff"

    # Formulate output structure for State inter-agent memory
    agent2_output = {
        "workspace_id": workspace_id,
        "lawyer_side": lawyer_side,
        "lawyer_arguments": strategy_result.get("lawyer_arguments", []),
        "opponent_counterarguments": strategy_result.get("opponent_counterarguments", []),
        "rebuttal_strategies": strategy_result.get("rebuttal_strategies", []),
        "courtroom_risks": strategy_result.get("courtroom_risks", []),
        "strategic_recommendations": strategy_result.get("strategic_recommendations", []),
        "argument_priorities": strategy_result.get("argument_priorities", {}),
        "evidence_utilization_strategy": strategy_result.get("evidence_utilization_strategy", []),
        "prepared_for_agent3": True
    }

    # Return updated state
    return {
        **state,
        "agent2_output": agent2_output,
        "current_stage": "agent2_completed"
    }
