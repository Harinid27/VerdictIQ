import asyncio
import requests
from app.database import connect_to_mongo, get_collection
from app.utils.jwt_handler import create_access_token

async def test():
    # 1. Connect to mongo and fetch a user
    await connect_to_mongo()
    users_collection = get_collection("users")
    user = await users_collection.find_one({})
    if not user:
        print("No user found in DB!")
        return
    
    print(f"Testing with user: {user['email']}")
    
    # 2. Create access token
    token = create_access_token({"sub": user["email"]})
    
    # 3. Hit the process route
    url = "http://localhost:8000/api/agent0/process/35d82dfc5c0c29f93ad1c583"
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "http://localhost:5173",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url, headers=headers, json={})
        print("STATUS:", res.status_code)
        print("HEADERS:", res.headers)
        print("BODY:", res.text[:2000])
    except Exception as e:
        print("REQUEST ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
