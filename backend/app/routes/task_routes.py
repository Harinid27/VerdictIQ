from fastapi import APIRouter, Depends, Query, status, HTTPException
from typing import List, Optional
from app.middleware.auth_middleware import get_current_user
from app.schemas.task_schema import TaskCreate, TaskUpdate, TaskResponse, TaskAPIResponse, TaskListAPIResponse
from app.services.task_service import (
    create_task_record,
    get_all_tasks,
    get_task_by_id,
    update_task_record,
    delete_task_record,
    complete_task_record,
    search_tasks_record
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.post("/create", response_model=TaskAPIResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]
    task = await create_task_record(task_data, user_id, user_email)
    return TaskAPIResponse(
        success=True,
        message="Task created successfully",
        data=TaskResponse(**task)
    )

@router.get("/all", response_model=TaskListAPIResponse)
async def get_tasks(
    workspace_id: Optional[str] = Query(None),
    due_date: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    sort_by: str = Query("latest", pattern="^(latest|oldest)$"),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    tasks = await get_all_tasks(user_id, workspace_id, due_date, priority, completed, sort_by)
    return TaskListAPIResponse(
        success=True,
        data=[TaskResponse(**t) for t in tasks]
    )

@router.get("/search", response_model=TaskListAPIResponse)
async def search_tasks(
    q: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    tasks = await search_tasks_record(q, user_id)
    return TaskListAPIResponse(
        success=True,
        data=[TaskResponse(**t) for t in tasks]
    )

@router.get("/{task_id}", response_model=TaskAPIResponse)
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    task = await get_task_by_id(task_id, user_id)
    return TaskAPIResponse(
        success=True,
        message="Task retrieved successfully",
        data=TaskResponse(**task)
    )

@router.put("/update/{task_id}", response_model=TaskAPIResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    task = await update_task_record(task_id, task_data, user_id)
    return TaskAPIResponse(
        success=True,
        message="Task updated successfully",
        data=TaskResponse(**task)
    )

@router.delete("/delete/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    await delete_task_record(task_id, user_id)
    return {
        "success": True,
        "message": "Task deleted successfully"
    }

@router.put("/complete/{task_id}", response_model=TaskAPIResponse)
async def complete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    task = await complete_task_record(task_id, user_id)
    return TaskAPIResponse(
        success=True,
        message="Task completion state updated",
        data=TaskResponse(**task)
    )
