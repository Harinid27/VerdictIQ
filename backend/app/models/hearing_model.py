from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class HearingInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    workspace_id: str
    case_name: str
    title: str
    court_name: str
    hearing_date: str  # YYYY-MM-DD format
    hearing_time: Optional[str] = None  # HH:MM format
    priority: str  # Low, Medium, High, Critical
    notes: Optional[str] = ""
    reminder_enabled: bool = False
    reminder_time: Optional[str] = None  # in minutes before event
    created_by: str  # user email or user id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "workspace_id": "case-1",
                "case_name": "Acme Corp vs. Stark Industries LLC",
                "title": "Motion to Dismiss Hearing",
                "court_name": "U.S. District Court, N.D. Cal.",
                "hearing_date": "2026-06-05",
                "hearing_time": "09:30",
                "priority": "High",
                "notes": "Pre-trial briefing files need compilation.",
                "reminder_enabled": True,
                "reminder_time": "120"
            }
        }
