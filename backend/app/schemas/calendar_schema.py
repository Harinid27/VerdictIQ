from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class CalendarEventCreate(BaseModel):
    workspace_id: str
    title: str = Field(..., min_length=1, max_length=150)
    event_type: str = Field("meeting", pattern=r"^(hearing|reminder|deadline|meeting)$")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None  # HH:MM format
    notes: Optional[str] = ""
    reminder_enabled: Optional[bool] = False
    reminder_time: Optional[str] = None

class MergedCalendarEvent(BaseModel):
    id: str
    workspace_id: str
    case_name: Optional[str] = None
    title: str
    event_type: str  # hearing, task, reminder, deadline, meeting
    date: str  # YYYY-MM-DD
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    priority: Optional[str] = None  # Low, Medium, High, Critical
    completed: Optional[bool] = None
    court_name: Optional[str] = None
    notes: Optional[str] = None

class CalendarAPIResponse(BaseModel):
    success: bool
    data: List[MergedCalendarEvent]
