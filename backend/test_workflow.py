import asyncio
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test():
    # Import database connectivity
    from app.database import connect_to_mongo, close_mongo_connection, get_collection
    
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()
    
    try:
        # Find a valid workspace ID from workspaces collection
        workspaces_col = get_collection("workspaces")
        workspace = await workspaces_col.find_one()
        
        if not workspace:
            logger.warning("No workspaces found in 'workspaces' collection. Checking 'cases' collection...")
            cases_col = get_collection("cases")
            workspace = await cases_col.find_one()
            
        if not workspace:
            logger.error("No workspaces or cases found in the database. Please initialize a case/workspace first.")
            return
            
        workspace_id = workspace.get("workspace_id") or str(workspace.get("_id"))
        logger.info(f"Found workspace/case in DB: ID={workspace_id}, Title={workspace.get('case_title') or workspace.get('name')}")
        
        # Import LangGraph workflow
        from app.graph import app_graph
        from app.state import VerdictState
        
        initial_state: VerdictState = {
            "workspace_id": workspace_id,
            "lawyer_side": None,
            "case_context": None,
            "agent0_output": None,
            "agent1_output": None,
            "legal_research_output": None,
            "agent2_output": None,
            "agent3_output": None,
            "current_stage": "started"
        }
        
        logger.info("Executing LangGraph multi-agent workflow...")
        final_state = await app_graph.ainvoke(initial_state)
        
        logger.info("=== LANGGRAPH WORKFLOW COMPLETE ===")
        logger.info(f"Final stage: {final_state.get('current_stage')}")
        logger.info(f"Agent 0 Output Generated: {bool(final_state.get('agent0_output'))}")
        logger.info(f"Agent 3 Output Generated: {bool(final_state.get('agent3_output'))}")
        
        # Verify persistence
        logger.info("Verifying persistence in MongoDB...")
        
        a1_col = get_collection("agent1_analysis")
        a1_doc = await a1_col.find_one({"workspace_id": workspace_id})
        logger.info(f"Verified MongoDB 'agent1_analysis' document exists: {bool(a1_doc)}")
        
        a2_col = get_collection("agent2_strategy")
        a2_doc = await a2_col.find_one({"workspace_id": workspace_id})
        logger.info(f"Verified MongoDB 'agent2_strategy' document exists: {bool(a2_doc)}")

        agent3_collection = get_collection("agent3_final_reports")
        report = await agent3_collection.find_one({"workspace_id": workspace_id})
        logger.info(f"Verified MongoDB 'agent3_final_reports' document exists: {bool(report)}")
        if report:
            logger.info(f"Executive Summary: {report.get('executive_summary')[:100]}...")
            
    except Exception as e:
        logger.exception(f"Test failed with exception: {e}")
    finally:
        logger.info("Closing MongoDB connection...")
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_test())
