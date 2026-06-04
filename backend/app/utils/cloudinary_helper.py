import os
import logging
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Initialize Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

def upload_file_to_cloudinary(file_bytes: bytes, filename: str) -> dict:
    """
    Uploads a file to Cloudinary.
    Falls back to a mock URL if placeholder credentials are used.
    """
    # Check for placeholder or unset credentials to use safe mock fallback
    is_placeholder = (
        not CLOUDINARY_CLOUD_NAME 
        or CLOUDINARY_CLOUD_NAME == "verdictiq_cloud"
        or not CLOUDINARY_API_KEY
        or CLOUDINARY_API_KEY.startswith("12345")
    )
    
    if is_placeholder:
        mock_id = f"mock_{os.urandom(8).hex()}"
        logger.warning(f"Using mock Cloudinary fallback for file: {filename}")
        return {
            "secure_url": f"https://res.cloudinary.com/verdictiq/image/upload/{mock_id}/{filename}",
            "public_id": mock_id,
            "is_mock": True
        }

    try:
        # Resource type 'auto' allows PDF, images, TXT, DOCX
        response = cloudinary.uploader.upload(
            file_bytes,
            public_id=f"verdictiq_{os.urandom(4).hex()}_{filename.split('.')[0]}",
            resource_type="auto"
        )
        return {
            "secure_url": response["secure_url"],
            "public_id": response["public_id"],
            "is_mock": False
        }
    except Exception as e:
        logger.warning(f"Cloudinary upload error: {e}. Falling back to mock URL.")
        mock_id = f"mock_{os.urandom(8).hex()}"
        return {
            "secure_url": f"https://res.cloudinary.com/verdictiq/image/upload/{mock_id}/{filename}",
            "public_id": mock_id,
            "is_mock": True
        }

def delete_file_from_cloudinary(public_id: str) -> bool:
    """
    Deletes a file from Cloudinary using its public_id.
    """
    if not public_id or public_id.startswith("mock_"):
        return True

    try:
        result = cloudinary.uploader.destroy(public_id)
        status = result.get("result")
        if status == "ok":
            logger.info(f"Cloudinary file deleted successfully: {public_id}")
            return True
        else:
            logger.warning(f"Cloudinary returned non-ok result for deletion: {result}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file from Cloudinary: {e}")
        return False
