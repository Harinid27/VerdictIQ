import sys
import subprocess

# Ensure pymongo is installed for this test
try:
    import pymongo
except ImportError:
    print("Installing pymongo for test script...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo", "dnspython"])
    import pymongo

from pymongo import MongoClient

# Test different common usernames
usernames = ["harinid772_db_user", "verdictiq", "admin", "db_user"]
password = "%40A1.a2.a3."  # URL-encoded '@A1.a2.a3.'
host = "verdictiq.gl7tt8x.mongodb.net/?appName=VerdictIQ"

print("Starting MongoDB Atlas credential tests...")

for username in usernames:
    uri = f"mongodb+srv://{username}:{password}@{host}"
    print(f"Testing connection with username: '{username}'...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        # Force a command call to trigger authorization
        db = client["VerdictIQ"]
        db.command("ping")
        print(f"SUCCESS: MongoDB Atlas connected and authenticated with username: '{username}'!")
        
        # Output the correct .env line
        print("\n=== CORRECT .env LINE ===")
        print(f"MONGODB_URI=mongodb+srv://{username}:%40A1.a2.a3.@verdictiq.gl7tt8x.mongodb.net/VerdictIQ?retryWrites=true&w=majority")
        sys.exit(0)
    except Exception as e:
        print(f"FAILED with username '{username}': {e}\n")

print("All common usernames failed to connect. Please check credentials or host name.")
sys.exit(1)
