from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class TaskCreate(BaseModel):
    workspace_id: str
    case_name: str
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = ""
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    priority: str = Field("Medium", pattern=r"^(Low|Medium|High|Critical)$")
    task_type: str = Field("Miscellaneous", pattern=r"^(Evidence Collection|Court Preparation|Documentation|Client Meeting|Research|Filing|Miscellaneous)$")
    reminder_enabled: Optional[bool] = False
    reminder_time: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    task_type: Optional[str] = None
    completed: Optional[bool] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None

class TaskResponse(BaseModel):
    id: str = Field(..., alias="_id")
    workspace_id: str
    case_name: str
    title: str
    description: str
    due_date: str
    priority: str
    completed: bool
    task_type: str
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

class TaskAPIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[TaskResponse] = None

class TaskListAPIResponse(BaseModel):
    success: bool
    data: List[TaskResponse]
