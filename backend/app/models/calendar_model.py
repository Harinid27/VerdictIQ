from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CalendarEventInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    workspace_id: str
    title: str
    event_type: str  # hearing, reminder, deadline, meeting
    date: str  # YYYY-MM-DD format
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None  # HH:MM format
    notes: Optional[str] = ""
    reminder_enabled: bool = False
    reminder_time: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    linked_id: Optional[str] = None  # ID of the task or hearing it is linked to

    class Config:
        populate_by_name = True
