import asyncio
import requests
from app.database import connect_to_mongo, get_collection, close_mongo_connection
from app.utils.jwt_handler import create_access_token
from bson import ObjectId

async def test():
    await connect_to_mongo()
    
    # 1. Find a valid workspace
    workspace_col = get_collection("workspaces")
    ws = await workspace_col.find_one({})
    if not ws:
        # Check in cases
        try:
            cases_col = get_collection("cases")
            ws = await cases_col.find_one({})
        except Exception as e:
            print("Error finding case:", e)
            
    if not ws:
        print("No workspace or case found in database to run API test.")
        await close_mongo_connection()
        return
        
    workspace_id = ws.get("workspace_id") or str(ws.get("_id"))
    creator = ws.get("created_by") or ws.get("user_id") or "harinid772@gmail.com"
    print(f"Workspace found! ID: {workspace_id}, Created by: {creator}")
    
    # 2. Find or create user info
    users_col = get_collection("users")
    user = await users_col.find_one({"email": creator})
    if not user:
        # Create a mock user or find any user
        user = await users_col.find_one({})
        if user:
            print(f"Creator user {creator} not found in 'users', using existing user: {user.get('email')}")
            creator = user.get("email")
        else:
            creator = "testuser@example.com"

    # 3. Create access token
    token = create_access_token({"sub": creator})
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "http://localhost:5173",
        "Content-Type": "application/json"
    }
    
    # 4. Hit Agent 0 Process Route
    print(f"\n--- Testing Agent 0 Process Route for {workspace_id} ---")
    url = f"http://localhost:8000/api/agent0/process/{workspace_id}"
    try:
        res = requests.post(url, headers=headers, json={})
        print("STATUS:", res.status_code)
        print("BODY:", res.json().get("success"), res.json().get("message"))
    except Exception as e:
        print("REQUEST ERROR Agent 0:", e)

    # 5. Hit Agent 1 Analyze Route
    print(f"\n--- Testing Agent 1 Analyze Route for {workspace_id} ---")
    url = f"http://localhost:8000/api/agent1/analyze/{workspace_id}"
    try:
        res = requests.post(url, headers=headers, json={})
        print("STATUS:", res.status_code)
        print("BODY:", res.json().get("success"), res.json().get("message"))
    except Exception as e:
        print("REQUEST ERROR Agent 1:", e)

    # 6. Hit Agent 2 Generate Strategy Route
    print(f"\n--- Testing Agent 2 Generate Strategy Route for {workspace_id} ---")
    url = f"http://localhost:8000/api/agent2/generate-strategy/{workspace_id}"
    try:
        res = requests.post(url, headers=headers, json={})
        print("STATUS:", res.status_code)
        print("BODY:", res.json().get("success"), res.json().get("message"))
    except Exception as e:
        print("REQUEST ERROR Agent 2:", e)

    # 7. Hit Agent 3 Generate Report Route
    print(f"\n--- Testing Agent 3 Generate Report Route for {workspace_id} ---")
    url = f"http://localhost:8000/api/agent3/generate-report/{workspace_id}"
    try:
        res = requests.post(url, headers=headers, json={})
        print("STATUS:", res.status_code)
        print("BODY:")
        body = res.json()
        print("  Success:", body.get("success"))
        print("  Message:", body.get("message"))
        if "report" in body:
            r = body["report"]
            print("  Executive Summary:", r.get("executive_summary")[:100] + "..." if r.get("executive_summary") else "None")
            print("  Case Strength Score:", r.get("case_strength_score"))
            print("  Final Report length:", len(r.get("final_legal_intelligence_report", "")))
    except Exception as e:
        print("REQUEST ERROR Agent 3:", e)

    # 8. Hit Chat Ask Route
    print(f"\n--- Testing Chat Ask Route for {workspace_id} ---")
    url = f"http://localhost:8000/api/chat/ask/{workspace_id}"
    try:
        res = requests.post(url, headers=headers, json={"message": "What are the strongest pieces of evidence in our case?"})
        print("STATUS:", res.status_code)
        print("BODY:")
        body = res.json()
        print("  Success:", body.get("success"))
        if body.get("success"):
            data = body.get("data", {})
            print("  Sender:", data.get("sender"))
            print("  Agent Name:", data.get("agent_name"))
            print("  Reply Text:", data.get("text")[:200] + "...")
    except Exception as e:
        print("REQUEST ERROR Chat:", e)

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test())
