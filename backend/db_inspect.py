import asyncio
import logging
from app.database import connect_to_mongo, get_collection, close_mongo_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def inspect():
    await connect_to_mongo()
    
    print("\n=== Inspecting Workspaces ===")
    ws_col = get_collection("workspaces")
    workspaces = await ws_col.find({}).to_list(length=10)
    for ws in workspaces:
        print(f"Workspace ID: {ws.get('workspace_id')}, Title: {ws.get('case_title')}")
        
    print("\n=== Inspecting Evidence ===")
    ev_col = get_collection("evidence")
    ev_docs = await ev_col.find({}).to_list(length=50)
    print(f"Total documents in 'evidence': {len(ev_docs)}")
    for ev in ev_docs:
        extracted = ev.get("extracted_text")
        extracted_len = len(extracted) if extracted else 0
        print(f"Evidence ID: {ev['_id']}, File Name: {ev.get('file_name')}, Workspace ID: {ev.get('workspace_id')}, Extracted Text Length: {extracted_len}, URL: {ev.get('file_url')}")
        
    print("\n=== Inspecting Evidence Files ===")
    ef_col = get_collection("evidence_files")
    ef_docs = await ef_col.find({}).to_list(length=50)
    print(f"Total documents in 'evidence_files': {len(ef_docs)}")
    for ef in ef_docs:
        extracted = ef.get("extracted_text")
        extracted_len = len(extracted) if extracted else 0
        print(f"EF File ID: {ef['_id']}, File Name: {ef.get('file_name')}, Workspace ID: {ef.get('workspace_id')}, Extracted Text Length: {extracted_len}, URL: {ef.get('file_url')}")
        
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(inspect())
