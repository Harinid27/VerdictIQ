from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import datetime
from typing import Optional, Any

class UserSignup(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    organization: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)

    @model_validator(mode='after')
    def verify_passwords_match(self) -> 'UserSignup':
        pw = self.password
        pw_confirm = self.confirm_password
        if pw != pw_confirm:
            raise ValueError("passwords do not match")
        return self

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str = Field(..., alias="_id")
    full_name: str
    organization: str
    role: str
    email: EmailStr
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AuthAPIResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[UserResponse] = None
