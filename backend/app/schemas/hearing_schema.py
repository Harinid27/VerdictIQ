from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class HearingCreate(BaseModel):
    workspace_id: str
    case_name: str
    title: str = Field(..., min_length=1, max_length=150)
    court_name: str = Field(..., min_length=1, max_length=150)
    hearing_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    hearing_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")  # HH:MM
    priority: str = Field("High", pattern=r"^(Low|Medium|High|Critical)$")
    notes: Optional[str] = ""
    reminder_enabled: Optional[bool] = False
    reminder_time: Optional[str] = None

class HearingUpdate(BaseModel):
    title: Optional[str] = None
    court_name: Optional[str] = None
    hearing_date: Optional[str] = None
    hearing_time: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None

class HearingResponse(BaseModel):
    id: str = Field(..., alias="_id")
    workspace_id: str
    case_name: str
    title: str
    court_name: str
    hearing_date: str
    hearing_time: Optional[str] = None
    priority: str
    notes: str
    reminder_enabled: bool
    reminder_time: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HearingAPIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[HearingResponse] = None

class HearingListAPIResponse(BaseModel):
    success: bool
    data: List[HearingResponse]
