import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import connect_to_mongo, close_mongo_connection
from app.routes.auth_routes import router as auth_router
from app.routes.task_routes import router as task_router
from app.routes.calendar_routes import router as calendar_router
from app.routes.file_routes import router as file_router
from app.routes.workspace_routes import router as workspace_router
from app.routes.agent0_routes import router as agent0_router
from app.routes.agent1_routes import router as agent1_router
from app.routes.agent2_routes import router as agent2_router
from app.routes.agent3_routes import router as agent3_router
from app.routes.chat_routes import router as chat_router, debug_router as debug_router
from app.routes.export_routes import router as export_router
from app.routes.analysis_routes import router as analysis_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Trigger reload to load updated .env keys

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start database connection
    await connect_to_mongo()
    yield
    # Close database connection
    await close_mongo_connection()

app = FastAPI(
    title="VerdictIQ Authentication API",
    description="Enterprise-grade AI legal operating system authentication backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for HTTPExceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail
        }
    )

# Exception handler for RequestValidationErrors (Pydantic schemas validation checks)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=422,
            content={"success": False, "message": "Input validation error"}
        )
    
    first_error = errors[0]
    error_msg = first_error.get("msg", "Invalid field inputs")
    loc = first_error.get("loc", [])
    field = loc[-1] if loc else "field"
    
    # Prettify the error message
    if "Value error," in error_msg:
        cleaned_msg = error_msg.replace("Value error, ", "")
    elif "field required" in error_msg:
        cleaned_msg = f"The '{field}' field is required."
    else:
        cleaned_msg = f"Invalid '{field}': {error_msg}"
        
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": cleaned_msg
        }
    )

# Register routes
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(calendar_router)
app.include_router(file_router)
app.include_router(workspace_router)
app.include_router(agent0_router)
app.include_router(agent1_router)
app.include_router(agent2_router)
app.include_router(agent3_router)
app.include_router(chat_router)
app.include_router(debug_router)
app.include_router(export_router)
app.include_router(analysis_router)


@app.get("/")
async def root():
    return {
        "success": True,
        "message": "VerdictIQ Legal Intelligence OS Auth Server Online."
    }
