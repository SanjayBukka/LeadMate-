"""
User Model
Represents managers and team leads in the system
"""
from pydantic import BaseModel, EmailStr, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ], serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}


class UserBase(BaseModel):
    """Base user model"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: str = Field(..., pattern="^(manager|teamlead)$")  # Only manager or teamlead


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8)
    startupId: str


class UserUpdate(BaseModel):
    """User update model"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    isActive: Optional[bool] = None


class User(UserBase):
    """User model for responses"""
    id: str = Field(alias="_id")
    startupId: str
    initials: str
    isActive: bool = True
    createdAt: datetime
    lastLogin: Optional[datetime] = None
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }


class UserInDB(UserBase):
    """User model as stored in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    startupId: str
    hashedPassword: str
    initials: str
    isActive: bool = True
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    lastLogin: Optional[datetime] = None
    createdBy: Optional[str] = None  # User ID who created this user
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    user_id: Optional[str] = None
    startup_id: Optional[str] = None
    role: Optional[str] = None

