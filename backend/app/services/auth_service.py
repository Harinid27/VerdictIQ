from datetime import datetime
from fastapi import HTTPException, status
from app.database import get_collection
from app.schemas.auth_schema import UserSignup, UserLogin
from app.utils.password_handler import hash_password, verify_password
from app.utils.jwt_handler import create_access_token

async def create_user_record(user_data: UserSignup) -> dict:
    users_collection = get_collection("users")
    
    # Check if duplicate email exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this work email address already exists"
        )
        
    # Encrypt password
    hashed_pw = hash_password(user_data.password)
    
    # Construct document
    new_user = {
        "full_name": user_data.full_name,
        "organization": user_data.organization,
        "role": user_data.role,
        "email": user_data.email,
        "hashed_password": hashed_pw,
        "created_at": datetime.utcnow()
    }
    
    result = await users_collection.insert_one(new_user)
    
    # Attach inserted id
    new_user["_id"] = str(result.inserted_id)
    
    # Generate token
    access_token = create_access_token(data={"sub": new_user["email"]})
    
    return {
        "token": access_token,
        "user": new_user
    }

async def verify_user_credentials(credentials: UserLogin) -> dict:
    users_collection = get_collection("users")
    
    # Look up user
    user = await users_collection.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials or invalid access key"
        )
        
    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials or invalid access key"
        )
        
    user["_id"] = str(user["_id"])
    
    # Generate token
    access_token = create_access_token(data={"sub": user["email"]})
    
    return {
        "token": access_token,
        "user": user
    }
