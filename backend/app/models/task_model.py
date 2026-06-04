from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TaskInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    workspace_id: str
    case_name: str
    title: str
    description: Optional[str] = ""
    due_date: str  # YYYY-MM-DD format
    priority: str  # Low, Medium, High, Critical
    completed: bool = False
    task_type: str  # Evidence Collection, Court Preparation, Documentation, Client Meeting, Research, Filing, Miscellaneous
    reminder_enabled: bool = False
    reminder_time: Optional[str] = None  # HH:MM format
    created_by: str  # user email or user id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
