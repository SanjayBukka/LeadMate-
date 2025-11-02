"""
Startup/Company Model
Represents a company that registers on the platform
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


class StartupBase(BaseModel):
    """Base startup model"""
    companyName: str = Field(..., min_length=2, max_length=200)
    companyEmail: EmailStr
    industry: Optional[str] = None
    companySize: Optional[str] = None  # "1-10", "11-50", "51-200", "201-500", "500+"
    website: Optional[str] = None
    description: Optional[str] = None


class StartupCreate(StartupBase):
    """Startup creation model (for registration)"""
    managerName: str = Field(..., min_length=2, max_length=100)
    managerEmail: EmailStr
    managerPassword: str = Field(..., min_length=8)


class Startup(StartupBase):
    """Startup model for responses"""
    id: str = Field(alias="_id")
    registrationDate: datetime
    status: str = "active"  # active, suspended, inactive
    totalUsers: int = 0
    totalProjects: int = 0
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }


class StartupInDB(StartupBase):
    """Startup model as stored in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    registrationDate: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"
    totalUsers: int = 0
    totalProjects: int = 0
    createdBy: Optional[str] = None  # User ID of the manager who registered
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

