from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from app.database import get_collection
from app.schemas.hearing_schema import HearingCreate, HearingUpdate
from app.models.hearing_model import HearingInDB
from app.schemas.calendar_schema import MergedCalendarEvent

# Convert MongoDB document to dictionary representation with serializable IDs
def serialize_mongo_doc(doc) -> dict:
    if not doc:
        return {}
    doc["_id"] = str(doc["_id"])
    return doc

# Cases / Workspaces CRUD helper services
async def create_case_record(case_data: dict, user_id: str, user_email: str) -> dict:
    cases_collection = get_collection("cases")
    
    case_dict = {
        "name": case_data.get("name"),
        "caseType": case_data.get("caseType"),
        "lawyerSide": case_data.get("lawyerSide"),
        "lastUpdated": "Just now",
        "riskLevel": case_data.get("riskLevel", "Medium"),
        "evidenceCount": case_data.get("evidenceCount", 0),
        "status": case_data.get("status", "Pre-Trial Audit"),
        "client": case_data.get("client"),
        "opposingParty": case_data.get("opposingParty"),
        "incidentDate": case_data.get("incidentDate"),
        "user_id": user_id,
        "created_by": user_email,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    client_id = case_data.get("id")
    if client_id:
        try:
            case_dict["_id"] = ObjectId(client_id)
        except Exception:
            case_dict["_id"] = client_id

    result = await cases_collection.insert_one(case_dict)
    case_dict["_id"] = str(case_dict["_id"])
    return serialize_mongo_doc(case_dict)

async def get_all_cases(user_id: str) -> List[dict]:
    cases_collection = get_collection("cases")
    cursor = cases_collection.find({"user_id": user_id}).sort("updated_at", -1)
    docs = await cursor.to_list(length=1000)
    return [serialize_mongo_doc(doc) for doc in docs]

async def delete_case_record(case_id: str, user_id: str) -> bool:
    cases_collection = get_collection("cases")
    
    # 1. Prepare ID filters (handling both ObjectId and string representations)
    try:
        oid = ObjectId(case_id)
        case_filter = {"$or": [{"_id": oid, "user_id": user_id}, {"_id": case_id, "user_id": user_id}]}
    except Exception:
        case_filter = {"_id": case_id, "user_id": user_id}
        
    # Delete from cases collection
    result = await cases_collection.delete_one(case_filter)
    if result.deleted_count == 0:
        return False

    # 2. Delete from workspaces
    await get_collection("workspaces").delete_many({"workspace_id": case_id})

    # 3. Fetch hearings to delete their calendar events
    hearings_cursor = get_collection("hearings").find({"workspace_id": case_id, "user_id": user_id})
    hearings = await hearings_cursor.to_list(length=1000)
    hearing_ids = [str(h["_id"]) for h in hearings]
    await get_collection("hearings").delete_many({"workspace_id": case_id, "user_id": user_id})

    # 4. Fetch tasks to delete their calendar events
    tasks_cursor = get_collection("tasks").find({"workspace_id": case_id, "user_id": user_id})
    tasks = await tasks_cursor.to_list(length=1000)
    task_ids = [str(t["_id"]) for t in tasks]
    await get_collection("tasks").delete_many({"workspace_id": case_id, "user_id": user_id})

    # 5. Delete all linked calendar events (matching workspace_id or linked to task/hearing)
    await get_collection("calendar_events").delete_many({
        "user_id": user_id,
        "$or": [
            {"workspace_id": case_id},
            {"linked_id": {"$in": hearing_ids + task_ids}}
        ]
    })

    # 6. Delete evidence files and clean up Cloudinary assets
    evidence_cursor = get_collection("evidence").find({"workspace_id": case_id, "user_id": user_id})
    evidence_docs = await evidence_cursor.to_list(length=1000)
    for ev in evidence_docs:
        public_id = ev.get("public_id")
        if public_id:
            try:
                from app.utils.cloudinary_helper import delete_file_from_cloudinary
                delete_file_from_cloudinary(public_id)
            except Exception:
                pass
    
    await get_collection("evidence").delete_many({"workspace_id": case_id, "user_id": user_id})
    await get_collection("evidence_files").delete_many({"workspace_id": case_id})

    # 7. Delete extraction and agent analysis documents
    await get_collection("document_extractions").delete_many({"workspace_id": case_id})
    await get_collection("structured_case_context").delete_many({"workspace_id": case_id})
    await get_collection("agent1_analysis").delete_many({"workspace_id": case_id})
    await get_collection("agent2_strategy").delete_many({"workspace_id": case_id})
    await get_collection("agent3_final_reports").delete_many({"workspace_id": case_id})

    # 8. Delete workspace chat history
    await get_collection("workspace_chats").delete_many({"workspace_id": case_id})

    return True

# Hearings CRUD Services
async def create_hearing_record(hearing_data: HearingCreate, user_id: str, user_email: str) -> dict:
    hearings_collection = get_collection("hearings")
    calendar_collection = get_collection("calendar_events")

    # Store hearing dict
    hearing_dict = hearing_data.model_dump()
    hearing_dict["created_by"] = user_email
    hearing_dict["user_id"] = user_id
    hearing_dict["created_at"] = datetime.utcnow()
    hearing_dict["updated_at"] = datetime.utcnow()

    # Insert into hearings collection
    result = await hearings_collection.insert_one(hearing_dict)
    hearing_id = str(result.inserted_id)
    hearing_dict["_id"] = hearing_id

    # Create linked event in calendar
    calendar_event = {
        "workspace_id": hearing_data.workspace_id,
        "title": f"Hearing: {hearing_data.title}",
        "event_type": "hearing",
        "date": hearing_data.hearing_date, # Date portion YYYY-MM-DD
        "start_time": hearing_data.hearing_time or "09:00",
        "notes": hearing_data.notes or f"Court: {hearing_data.court_name}",
        "reminder_enabled": hearing_data.reminder_enabled or False,
        "reminder_time": hearing_data.reminder_time,
        "created_by": user_email,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "linked_id": hearing_id,
        "priority": hearing_data.priority,
        "court_name": hearing_data.court_name,
        "case_name": hearing_data.case_name
    }
    await calendar_collection.insert_one(calendar_event)

    return hearing_dict

async def get_all_hearings(user_id: str, workspace_id: Optional[str] = None) -> List[dict]:
    hearings_collection = get_collection("hearings")
    query = {"user_id": user_id}
    if workspace_id:
        query["workspace_id"] = workspace_id
        
    cursor = hearings_collection.find(query).sort("hearing_date", 1)
    docs = await cursor.to_list(length=1000)
    return [serialize_mongo_doc(doc) for doc in docs]

async def get_upcoming_hearings(user_id: str, limit: int = 5) -> List[dict]:
    hearings_collection = get_collection("hearings")
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    query = {
        "user_id": user_id,
        "hearing_date": {"$gte": today_str}
    }
    cursor = hearings_collection.find(query).sort("hearing_date", 1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [serialize_mongo_doc(doc) for doc in docs]

async def update_hearing_record(hearing_id: str, hearing_data: HearingUpdate, user_id: str) -> dict:
    hearings_collection = get_collection("hearings")
    calendar_collection = get_collection("calendar_events")

    try:
        oid = ObjectId(hearing_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid hearing ID format")

    existing_hearing = await hearings_collection.find_one({"_id": oid, "user_id": user_id})
    if not existing_hearing:
        raise HTTPException(status_code=404, detail="Hearing not found")

    update_fields = {k: v for k, v in hearing_data.model_dump(exclude_unset=True).items()}
    if not update_fields:
        return serialize_mongo_doc(existing_hearing)

    update_fields["updated_at"] = datetime.utcnow()

    # Update in DB
    await hearings_collection.update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": update_fields}
    )

    # Sync updates to linked calendar event
    calendar_updates = {}
    if "title" in update_fields:
        calendar_updates["title"] = f"Hearing: {update_fields['title']}"
    if "hearing_date" in update_fields:
        calendar_updates["date"] = update_fields["hearing_date"]
    if "hearing_time" in update_fields:
        calendar_updates["start_time"] = update_fields["hearing_time"]
    if "notes" in update_fields:
        calendar_updates["notes"] = update_fields["notes"]
    if "court_name" in update_fields:
        calendar_updates["court_name"] = update_fields["court_name"]
    if "priority" in update_fields:
        calendar_updates["priority"] = update_fields["priority"]

    if calendar_updates:
        await calendar_collection.update_one(
            {"linked_id": hearing_id, "user_id": user_id},
            {"$set": calendar_updates}
        )

    updated_hearing = await hearings_collection.find_one({"_id": oid, "user_id": user_id})
    return serialize_mongo_doc(updated_hearing)

async def delete_hearing_record(hearing_id: str, user_id: str) -> bool:
    hearings_collection = get_collection("hearings")
    calendar_collection = get_collection("calendar_events")

    try:
        oid = ObjectId(hearing_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid hearing ID format")

    existing_hearing = await hearings_collection.find_one({"_id": oid, "user_id": user_id})
    if not existing_hearing:
        raise HTTPException(status_code=404, detail="Hearing not found")

    # Delete hearing
    await hearings_collection.delete_one({"_id": oid, "user_id": user_id})

    # Delete calendar event
    await calendar_collection.delete_one({"linked_id": hearing_id, "user_id": user_id})

    return True

async def search_hearings_record(query: str, user_id: str) -> List[dict]:
    hearings_collection = get_collection("hearings")
    search_query = {
        "user_id": user_id,
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"case_name": {"$regex": query, "$options": "i"}},
            {"court_name": {"$regex": query, "$options": "i"}},
            {"notes": {"$regex": query, "$options": "i"}}
        ]
    }
    cursor = hearings_collection.find(search_query)
    docs = await cursor.to_list(length=100)
    return [serialize_mongo_doc(doc) for doc in docs]


# Calendar Merging Services
async def get_calendar_month(user_id: str, month: Optional[str] = None) -> List[dict]:
    # We fetch all events from calendar_events.
    # Note that tasks and hearings are synced into calendar_events automatically.
    # Let's enrich the results with extra fields to match MergedCalendarEvent schema.
    calendar_collection = get_collection("calendar_events")
    tasks_collection = get_collection("tasks")
    
    query = {"user_id": user_id}
    # Optional filtering by month regex (YYYY-MM)
    if month:
        query["date"] = {"$regex": f"^{month}"}
        
    cursor = calendar_collection.find(query).sort("date", 1)
    events = await cursor.to_list(length=1000)
    
    merged_events = []
    for ev in events:
        ev_id = str(ev["_id"])
        linked_id = ev.get("linked_id")
        
        # Build structure matching MergedCalendarEvent
        merged_ev = {
            "id": ev_id,
            "workspace_id": ev.get("workspace_id"),
            "title": ev.get("title"),
            "event_type": ev.get("event_type", "meeting"),
            "date": ev.get("date"),
            "start_time": ev.get("start_time"),
            "end_time": ev.get("end_time"),
            "priority": ev.get("priority", "Medium"),
            "completed": False,
            "court_name": ev.get("court_name"),
            "notes": ev.get("notes", ""),
            "case_name": ev.get("case_name")
        }
        
        # If it is a task, retrieve active completion status
        if ev.get("event_type") == "deadline" and linked_id:
            try:
                task = await tasks_collection.find_one({"_id": ObjectId(linked_id)})
                if task:
                    merged_ev["completed"] = task.get("completed", False)
                    merged_ev["priority"] = task.get("priority", "Medium")
                    merged_ev["case_name"] = task.get("case_name")
            except Exception:
                pass
                
        merged_events.append(merged_ev)
        
    return merged_events

async def get_calendar_day(user_id: str, date_str: str) -> List[dict]:
    calendar_collection = get_collection("calendar_events")
    tasks_collection = get_collection("tasks")
    
    query = {"user_id": user_id, "date": date_str}
    cursor = calendar_collection.find(query).sort("start_time", 1)
    events = await cursor.to_list(length=100)
    
    merged_events = []
    for ev in events:
        ev_id = str(ev["_id"])
        linked_id = ev.get("linked_id")
        
        merged_ev = {
            "id": ev_id,
            "workspace_id": ev.get("workspace_id"),
            "title": ev.get("title"),
            "event_type": ev.get("event_type", "meeting"),
            "date": ev.get("date"),
            "start_time": ev.get("start_time"),
            "end_time": ev.get("end_time"),
            "priority": ev.get("priority", "Medium"),
            "completed": False,
            "court_name": ev.get("court_name"),
            "notes": ev.get("notes", ""),
            "case_name": ev.get("case_name")
        }
        
        if ev.get("event_type") == "deadline" and linked_id:
            try:
                task = await tasks_collection.find_one({"_id": ObjectId(linked_id)})
                if task:
                    merged_ev["completed"] = task.get("completed", False)
                    merged_ev["priority"] = task.get("priority")
                    merged_ev["case_name"] = task.get("case_name")
            except Exception:
                pass
                
        merged_events.append(merged_ev)
        
    return merged_events

async def get_calendar_upcoming(user_id: str, limit: int = 10) -> List[dict]:
    calendar_collection = get_collection("calendar_events")
    tasks_collection = get_collection("tasks")
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    query = {
        "user_id": user_id,
        "date": {"$gte": today_str}
    }
    cursor = calendar_collection.find(query).sort("date", 1).limit(limit)
    events = await cursor.to_list(length=limit)
    
    merged_events = []
    for ev in events:
        ev_id = str(ev["_id"])
        linked_id = ev.get("linked_id")
        
        merged_ev = {
            "id": ev_id,
            "workspace_id": ev.get("workspace_id"),
            "title": ev.get("title"),
            "event_type": ev.get("event_type"),
            "date": ev.get("date"),
            "start_time": ev.get("start_time"),
            "end_time": ev.get("end_time"),
            "priority": ev.get("priority", "Medium"),
            "completed": False,
            "court_name": ev.get("court_name"),
            "notes": ev.get("notes", ""),
            "case_name": ev.get("case_name")
        }
        
        if ev.get("event_type") == "deadline" and linked_id:
            try:
                task = await tasks_collection.find_one({"_id": ObjectId(linked_id)})
                if task:
                    merged_ev["completed"] = task.get("completed", False)
                    merged_ev["priority"] = task.get("priority")
                    merged_ev["case_name"] = task.get("case_name")
            except Exception:
                pass
        merged_events.append(merged_ev)
        
    return merged_events


# Dashboard Analytics Integration
async def get_dashboard_analytics_stats(user_id: str) -> dict:
    cases_collection = get_collection("cases")
    tasks_collection = get_collection("tasks")
    hearings_collection = get_collection("hearings")
    
    # 1. Total cases
    total_cases = await cases_collection.count_documents({"user_id": user_id})
    
    # 2. Total tasks
    total_tasks = await tasks_collection.count_documents({"user_id": user_id})
    
    # 3. Completed tasks
    completed_tasks = await tasks_collection.count_documents({"user_id": user_id, "completed": True})
    
    # 4. Pending tasks
    pending_tasks = await tasks_collection.count_documents({"user_id": user_id, "completed": False})
    
    # 5. Upcoming hearings
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    upcoming_hearings = await hearings_collection.count_documents({
        "user_id": user_id,
        "hearing_date": {"$gte": today_str}
    })
    
    # 6. High risk cases
    high_risk_cases = await cases_collection.count_documents({
        "user_id": user_id,
        "riskLevel": "High"
    })
    
    # 7. Reports generated from workspaces belonging to this user
    cases_cursor = cases_collection.find({"user_id": user_id})
    cases_list = await cases_cursor.to_list(length=1000)
    workspace_ids = [str(c["_id"]) for c in cases_list]
    
    generated_reports = await get_collection("agent3_final_reports").count_documents({
        "workspace_id": {"$in": workspace_ids}
    })
    
    return {
        "total_cases": total_cases,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "upcoming_hearings": upcoming_hearings,
        "high_risk_cases": high_risk_cases,
        "generated_reports": generated_reports
    }
