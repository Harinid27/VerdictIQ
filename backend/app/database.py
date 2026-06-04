import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "VerdictIQ")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    logger.info("Initializing async MongoDB connection...")
    try:
        db_instance.client = AsyncIOMotorClient(MONGODB_URI)
        db_instance.db = db_instance.client[DATABASE_NAME]
        # Verify connection by running a command ping
        await db_instance.db.command("ping")
        logger.info("MongoDB Atlas connection established successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    if db_instance.client:
        logger.info("Closing MongoDB connection pool...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    return db_instance.db

def get_collection(collection_name: str):
    return db_instance.db[collection_name]
