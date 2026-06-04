from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from app.database import get_collection
from app.schemas.task_schema import TaskCreate, TaskUpdate
from app.models.task_model import TaskInDB

# Convert MongoDB document to dictionary representation with serializable IDs
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    doc["_id"] = str(doc["_id"])
    return doc

async def create_task_record(task_data: TaskCreate, user_id: str, user_email: str) -> dict:
    tasks_collection = get_collection("tasks")
    calendar_collection = get_collection("calendar_events")

    # Create task DB model dict
    task_dict = task_data.model_dump()
    task_dict["completed"] = False
    task_dict["created_by"] = user_email
    task_dict["user_id"] = user_id  # Strict user isolation
    task_dict["created_at"] = datetime.utcnow()
    task_dict["updated_at"] = datetime.utcnow()

    # Insert into tasks collection
    result = await tasks_collection.insert_one(task_dict)
    task_id = str(result.inserted_id)
    task_dict["_id"] = task_id

    # Sync to calendar_events collection
    calendar_event = {
        "workspace_id": task_data.workspace_id,
        "title": f"Task Due: {task_data.title}",
        "event_type": "deadline",
        "date": task_data.due_date,
        "notes": task_data.description or f"Task priority: {task_data.priority}",
        "reminder_enabled": task_data.reminder_enabled or False,
        "reminder_time": task_data.reminder_time,
        "created_by": user_email,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "linked_id": task_id
    }
    await calendar_collection.insert_one(calendar_event)

    return task_dict

async def get_all_tasks(
    user_id: str,
    workspace_id: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    completed: Optional[bool] = None,
    sort_by: str = "latest"
) -> List[dict]:
    tasks_collection = get_collection("tasks")

    # Build query
    query = {"user_id": user_id}
    if workspace_id:
        query["workspace_id"] = workspace_id
    if due_date:
        query["due_date"] = due_date
    if priority:
        query["priority"] = priority
    if completed is not None:
        query["completed"] = completed

    # Determine sort
    sort_direction = -1 if sort_by == "latest" else 1
    cursor = tasks_collection.find(query).sort("created_at", sort_direction)
    
    docs = await cursor.to_list(length=1000)
    return [serialize_mongo_doc(doc) for doc in docs]

async def get_task_by_id(task_id: str, user_id: str) -> dict:
    tasks_collection = get_collection("tasks")
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    task = await tasks_collection.find_one({"_id": oid, "user_id": user_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return serialize_mongo_doc(task)

async def update_task_record(task_id: str, task_data: TaskUpdate, user_id: str) -> dict:
    tasks_collection = get_collection("tasks")
    calendar_collection = get_collection("calendar_events")

    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    # Verify task ownership
    existing_task = await tasks_collection.find_one({"_id": oid, "user_id": user_id})
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_fields = {k: v for k, v in task_data.model_dump(exclude_unset=True).items()}
    if not update_fields:
        return serialize_mongo_doc(existing_task)

    update_fields["updated_at"] = datetime.utcnow()

    # Update in DB
    await tasks_collection.update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": update_fields}
    )

    # Sync updates to linked calendar event
    calendar_updates = {}
    if "title" in update_fields:
        calendar_updates["title"] = f"Task Due: {update_fields['title']}"
    if "due_date" in update_fields:
        calendar_updates["date"] = update_fields["due_date"]
    if "description" in update_fields:
        calendar_updates["notes"] = update_fields["description"]
    if "reminder_enabled" in update_fields:
        calendar_updates["reminder_enabled"] = update_fields["reminder_enabled"]
    if "reminder_time" in update_fields:
        calendar_updates["reminder_time"] = update_fields["reminder_time"]

    if calendar_updates:
        await calendar_collection.update_one(
            {"linked_id": task_id, "user_id": user_id},
            {"$set": calendar_updates}
        )

    updated_task = await tasks_collection.find_one({"_id": oid, "user_id": user_id})
    return serialize_mongo_doc(updated_task)

async def delete_task_record(task_id: str, user_id: str) -> bool:
    tasks_collection = get_collection("tasks")
    calendar_collection = get_collection("calendar_events")

    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    # Verify task ownership
    existing_task = await tasks_collection.find_one({"_id": oid, "user_id": user_id})
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Delete task
    await tasks_collection.delete_one({"_id": oid, "user_id": user_id})

    # Delete linked calendar event
    await calendar_collection.delete_one({"linked_id": task_id, "user_id": user_id})

    return True

async def complete_task_record(task_id: str, user_id: str) -> dict:
    tasks_collection = get_collection("tasks")
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    # Verify task ownership
    existing_task = await tasks_collection.find_one({"_id": oid, "user_id": user_id})
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_completion_status = not existing_task.get("completed", False)
    
    await tasks_collection.update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": {
            "completed": new_completion_status,
            "updated_at": datetime.utcnow()
        }}
    )

    updated_task = await tasks_collection.find_one({"_id": oid, "user_id": user_id})
    return serialize_mongo_doc(updated_task)

async def search_tasks_record(query: str, user_id: str) -> List[dict]:
    tasks_collection = get_collection("tasks")
    
    search_query = {
        "user_id": user_id,
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"case_name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    }
    
    cursor = tasks_collection.find(search_query)
    docs = await cursor.to_list(length=100)
    return [serialize_mongo_doc(doc) for doc in docs]
