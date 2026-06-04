from fastapi import APIRouter, Depends, status
from app.schemas.auth_schema import UserSignup, UserLogin, AuthAPIResponse, UserResponse
from app.services.auth_service import create_user_record, verify_user_credentials
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=AuthAPIResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup):
    result = await create_user_record(user_data)
    return AuthAPIResponse(
        success=True,
        message="Workspace node provisioned successfully.",
        token=result["token"],
        user=UserResponse(**result["user"])
    )

@router.post("/login", response_model=AuthAPIResponse)
async def login(credentials: UserLogin):
    result = await verify_user_credentials(credentials)
    return AuthAPIResponse(
        success=True,
        message="Platform handshake successful. Welcome to VerdictIQ.",
        token=result["token"],
        user=UserResponse(**result["user"])
    )

@router.get("/me", response_model=AuthAPIResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return AuthAPIResponse(
        success=True,
        message="Active session payload verified.",
        user=UserResponse(**current_user)
    )
