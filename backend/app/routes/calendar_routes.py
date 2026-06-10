from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, HTTPException
from typing import List, Optional
from app.middleware.auth_middleware import get_current_user
from app.database import get_collection
from app.schemas.hearing_schema import HearingCreate, HearingUpdate, HearingResponse, HearingAPIResponse, HearingListAPIResponse
from app.schemas.calendar_schema import CalendarAPIResponse, MergedCalendarEvent
from app.schemas.task_schema import TaskResponse, TaskListAPIResponse
from app.services.calendar_service import (
    create_hearing_record,
    get_all_hearings,
    get_upcoming_hearings,
    update_hearing_record,
    delete_hearing_record,
    search_hearings_record,
    get_calendar_month,
    get_calendar_day,
    get_calendar_upcoming,
    get_dashboard_analytics_stats,
    create_case_record,
    get_all_cases,
    delete_case_record
)
from app.services.task_service import get_all_tasks
from app.services.gemini_service import (
    generate_ai_activity_feed,
    generate_calendar_recommendations
)


router = APIRouter(tags=["Calendar, Hearings, Cases & Dashboard"])

# --- CASE / WORKSPACE ENDPOINTS ---
@router.post("/api/cases/create", status_code=status.HTTP_201_CREATED)
async def create_case(case_data: dict, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]
    new_case = await create_case_record(case_data, user_id, user_email)
    return {
        "success": True,
        "message": "Workspace initialized successfully",
        "data": new_case
    }

@router.get("/api/cases/all")
async def get_cases(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    cases = await get_all_cases(user_id)
    return {
        "success": True,
        "data": cases
    }

@router.delete("/api/cases/delete/{case_id}")
async def delete_case(case_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    await delete_case_record(case_id, user_id)
    return {
        "success": True,
        "message": "Workspace deleted successfully"
    }


# --- HEARING ENDPOINTS ---
@router.post("/api/hearings/create", response_model=HearingAPIResponse, status_code=status.HTTP_201_CREATED)
async def create_hearing(hearing_data: HearingCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    user_email = current_user["email"]
    hearing = await create_hearing_record(hearing_data, user_id, user_email)
    return HearingAPIResponse(
        success=True,
        message="Hearing scheduled successfully",
        data=HearingResponse(**hearing)
    )

@router.get("/api/hearings/all", response_model=HearingListAPIResponse)
async def get_hearings(
    workspace_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    hearings = await get_all_hearings(user_id, workspace_id)
    return HearingListAPIResponse(
        success=True,
        data=[HearingResponse(**h) for h in hearings]
    )

@router.get("/api/hearings/upcoming", response_model=HearingListAPIResponse)
async def get_upcoming(
    limit: int = Query(5, ge=1),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    hearings = await get_upcoming_hearings(user_id, limit)
    return HearingListAPIResponse(
        success=True,
        data=[HearingResponse(**h) for h in hearings]
    )

@router.put("/api/hearings/update/{hearing_id}", response_model=HearingAPIResponse)
async def update_hearing(
    hearing_id: str,
    hearing_data: HearingUpdate,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    hearing = await update_hearing_record(hearing_id, hearing_data, user_id)
    return HearingAPIResponse(
        success=True,
        message="Hearing updated successfully",
        data=HearingResponse(**hearing)
    )

@router.delete("/api/hearings/delete/{hearing_id}")
async def delete_hearing(hearing_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    await delete_hearing_record(hearing_id, user_id)
    return {
        "success": True,
        "message": "Hearing deleted successfully"
    }

@router.get("/api/hearings/search", response_model=HearingListAPIResponse)
async def search_hearings(
    q: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    hearings = await search_hearings_record(q, user_id)
    return HearingListAPIResponse(
        success=True,
        data=[HearingResponse(**h) for h in hearings]
    )


# --- CALENDAR ENDPOINTS ---
@router.get("/api/calendar/month", response_model=CalendarAPIResponse)
async def get_month_events(
    month: Optional[str] = Query(None, description="Format: YYYY-MM"),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    events = await get_calendar_month(user_id, month)
    return CalendarAPIResponse(
        success=True,
        data=[MergedCalendarEvent(**ev) for ev in events]
    )

@router.get("/api/calendar/day/{date}", response_model=CalendarAPIResponse)
async def get_day_events(
    date: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    events = await get_calendar_day(user_id, date)
    return CalendarAPIResponse(
        success=True,
        data=[MergedCalendarEvent(**ev) for ev in events]
    )

@router.get("/api/calendar/upcoming", response_model=CalendarAPIResponse)
async def get_upcoming_events(
    limit: int = Query(10, ge=1),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    events = await get_calendar_upcoming(user_id, limit)
    return CalendarAPIResponse(
        success=True,
        data=[MergedCalendarEvent(**ev) for ev in events]
    )


# --- DASHBOARD ENDPOINTS ---
@router.get("/api/dashboard/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    stats = await get_dashboard_analytics_stats(user_id)
    return {
        "success": True,
        "data": stats
    }

@router.get("/api/dashboard/recent-cases")
async def get_recent_cases(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    cases = await get_all_cases(user_id)
    # Take first 5 recent
    recent = cases[:5]
    return {
        "success": True,
        "data": recent
    }

@router.get("/api/dashboard/upcoming-hearings", response_model=HearingListAPIResponse)
async def get_dashboard_upcoming_hearings(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    hearings = await get_upcoming_hearings(user_id, limit=5)
    return HearingListAPIResponse(
        success=True,
        data=[HearingResponse(**h) for h in hearings]
    )

@router.get("/api/dashboard/pending-tasks", response_model=TaskListAPIResponse)
async def get_dashboard_pending_tasks(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    tasks = await get_all_tasks(user_id, completed=False)
    # limit to 5
    recent_pending = tasks[:5]
    return TaskListAPIResponse(
        success=True,
        data=[TaskResponse(**t) for t in recent_pending]
    )

@router.get("/api/dashboard/ai-activity-feed")
async def get_ai_activity_feed(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Fetch user's cases
    cases = await get_all_cases(user_id)
    case_ids = [c["_id"] for c in cases]
    
    # Fetch tasks
    tasks = await get_all_tasks(user_id)
    
    # Fetch evidence files
    evidence_files = await get_collection("evidence_files").find({"workspace_id": {"$in": case_ids}}).to_list(length=1000)
    
    feed = await generate_ai_activity_feed(cases, tasks, evidence_files)
    return {
        "success": True,
        "data": feed
    }

@router.get("/api/calendar/recommendations")
async def get_calendar_recs(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Fetch user's cases
    cases = await get_all_cases(user_id)
    case_ids = [c["_id"] for c in cases]
    
    # Fetch hearings and filter out completed ones (where date/time is in the past)
    all_hearings = await get_all_hearings(user_id)
    now = datetime.utcnow()
    hearings = []
    for h in all_hearings:
        h_date = h.get("hearing_date")
        h_time = h.get("hearing_time") or "00:00"
        try:
            h_dt = datetime.strptime(f"{h_date} {h_time}", "%Y-%m-%d %H:%M")
            if h_dt >= now:
                hearings.append(h)
        except Exception:
            hearings.append(h)
    
    # Fetch evidence files
    evidence_files = await get_collection("evidence_files").find({"workspace_id": {"$in": case_ids}}).to_list(length=1000)
    
    recs = await generate_calendar_recommendations(cases, hearings, evidence_files)
    return {
        "success": True,
        "data": recs
    }

@router.get("/api/debug/db")
async def debug_db():
    from app.database import db_instance, DATABASE_NAME, MONGODB_URI
    collections = await db_instance.db.list_collection_names()
    counts = {}
    for col_name in collections:
        col = db_instance.db[col_name]
        count = await col.count_documents({})
        counts[col_name] = count
    return {
        "database_name": DATABASE_NAME,
        "mongodb_uri_masked": MONGODB_URI[:30] + "...",
        "collections": collections,
        "document_counts": counts
    }

