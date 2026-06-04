from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    full_name: str
    organization: str
    role: str
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "full_name": "Alexander Vance",
                "organization": "Vance & Associates LLP",
                "role": "lawyer",
                "email": "attorney@verdictiq.ai",
                "hashed_password": "bcrypt_hashed_string",
                "created_at": "2026-06-03T14:44:29Z"
            }
        }
