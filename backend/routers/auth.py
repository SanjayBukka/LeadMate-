"""
Authentication and User Management Router
Handles startup registration, user login, and user management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from datetime import datetime
from bson import ObjectId

from database import get_database
from models.startup import StartupCreate, Startup
from models.user import UserCreate, User, UserLogin, Token, UserUpdate
from utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_initials
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()


# ============================================================================
# STARTUP REGISTRATION
# ============================================================================

@router.post("/register-startup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_startup(startup_data: StartupCreate):
    """
    Register a new startup/company with initial manager account
    """
    db = get_database()
    
    # Check if company email already exists
    existing_startup = await db.startups.find_one({"companyEmail": startup_data.companyEmail})
    if existing_startup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company email already registered"
        )
    
    # Check if manager email already exists
    existing_user = await db.users.find_one({"email": startup_data.managerEmail})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manager email already registered"
        )
    
    # Create startup document
    startup_doc = {
        "companyName": startup_data.companyName,
        "companyEmail": startup_data.companyEmail,
        "industry": startup_data.industry,
        "companySize": startup_data.companySize,
        "website": startup_data.website,
        "description": startup_data.description,
        "registrationDate": datetime.utcnow(),
        "status": "active",
        "totalUsers": 1,
        "totalProjects": 0
    }
    
    # Insert startup
    startup_result = await db.startups.insert_one(startup_doc)
    startup_id = str(startup_result.inserted_id)
    
    # Create manager user
    user_doc = {
        "name": startup_data.managerName,
        "email": startup_data.managerEmail,
        "role": "manager",
        "startupId": startup_id,
        "hashedPassword": get_password_hash(startup_data.managerPassword),
        "initials": get_initials(startup_data.managerName),
        "isActive": True,
        "createdAt": datetime.utcnow(),
        "lastLogin": None,
        "createdBy": None  # Self-registered
    }
    
    # Insert manager user
    user_result = await db.users.insert_one(user_doc)
    user_id = str(user_result.inserted_id)
    
    # Update startup with createdBy
    await db.startups.update_one(
        {"_id": startup_result.inserted_id},
        {"$set": {"createdBy": user_id}}
    )
    
    return {
        "message": "Startup registered successfully",
        "startupId": startup_id,
        "userId": user_id,
        "companyName": startup_data.companyName,
        "managerEmail": startup_data.managerEmail
    }


# ============================================================================
# USER LOGIN
# ============================================================================

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """
    Login user and return JWT token
    """
    db = get_database()
    
    # Find user by email
    user = await db.users.find_one({"email": user_credentials.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user["hashedPassword"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get("isActive", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"lastLogin": datetime.utcnow()}}
    )
    
    # Create access token
    token_data = {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "startup_id": user["startupId"],
        "role": user["role"]
    }
    access_token = create_access_token(data=token_data)
    
    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================================
# GET CURRENT USER
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user from token
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.get("/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    user_data = {
        "_id": str(current_user["_id"]),
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "startupId": current_user["startupId"],
        "initials": current_user["initials"],
        "isActive": current_user.get("isActive", True),
        "createdAt": current_user["createdAt"],
        "lastLogin": current_user.get("lastLogin")
    }
    return user_data


# ============================================================================
# USER MANAGEMENT (Manager Only)
# ============================================================================

async def require_manager(current_user: dict = Depends(get_current_user)):
    """
    Dependency to ensure user is a manager
    """
    if current_user["role"] != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )
    return current_user


@router.post("/users/add-lead", response_model=User, status_code=status.HTTP_201_CREATED)
async def add_team_lead(
    user_data: UserCreate,
    current_user: dict = Depends(require_manager)
):
    """
    Manager adds a new team lead to their startup
    """
    db = get_database()
    
    # Ensure role is teamlead
    if user_data.role != "teamlead":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only add team leads using this endpoint"
        )
    
    # Ensure startup ID matches current user's startup
    if user_data.startupId != current_user["startupId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add users to a different startup"
        )
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_doc = {
        "name": user_data.name,
        "email": user_data.email,
        "role": "teamlead",
        "startupId": user_data.startupId,
        "hashedPassword": get_password_hash(user_data.password),
        "initials": get_initials(user_data.name),
        "isActive": True,
        "createdAt": datetime.utcnow(),
        "lastLogin": None,
        "createdBy": str(current_user["_id"])
    }
    
    # Insert user
    result = await db.users.insert_one(user_doc)
    
    # Update startup user count
    await db.startups.update_one(
        {"_id": ObjectId(user_data.startupId)},
        {"$inc": {"totalUsers": 1}}
    )
    
    # Return created user
    user_doc["_id"] = str(result.inserted_id)
    return user_doc


@router.get("/users/team-leads", response_model=List[User])
async def get_team_leads(current_user: dict = Depends(require_manager)):
    """
    Get all team leads for the manager's startup
    """
    db = get_database()
    
    cursor = db.users.find({
        "startupId": current_user["startupId"],
        "role": "teamlead"
    })
    
    team_leads = []
    async for user in cursor:
        user_data = {
            "_id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "startupId": user["startupId"],
            "initials": user["initials"],
            "isActive": user.get("isActive", True),
            "createdAt": user["createdAt"],
            "lastLogin": user.get("lastLogin")
        }
        team_leads.append(user_data)
    
    return team_leads


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def remove_user(
    user_id: str,
    current_user: dict = Depends(require_manager)
):
    """
    Manager removes a user from their startup (soft delete)
    """
    db = get_database()
    
    # Find user to remove
    user_to_remove = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Ensure user belongs to same startup
    if user_to_remove["startupId"] != current_user["startupId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove users from a different startup"
        )
    
    # Prevent manager from removing themselves
    if str(user_to_remove["_id"]) == str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )
    
    # Soft delete (deactivate user)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"isActive": False}}
    )
    
    # Update startup user count
    await db.startups.update_one(
        {"_id": ObjectId(current_user["startupId"])},
        {"$inc": {"totalUsers": -1}}
    )
    
    return {"message": "User removed successfully", "userId": user_id}


@router.put("/users/{user_id}/activate", status_code=status.HTTP_200_OK)
async def activate_user(
    user_id: str,
    current_user: dict = Depends(require_manager)
):
    """
    Manager reactivates a deactivated user
    """
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Ensure user belongs to same startup
    if user["startupId"] != current_user["startupId"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot activate users from a different startup"
        )
    
    # Activate user
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"isActive": True}}
    )
    
    # Update startup user count
    if not user.get("isActive", True):
        await db.startups.update_one(
            {"_id": ObjectId(current_user["startupId"])},
            {"$inc": {"totalUsers": 1}}
        )
    
    return {"message": "User activated successfully", "userId": user_id}

