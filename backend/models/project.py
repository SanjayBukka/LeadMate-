"""
Project Model
Represents projects created by managers
"""
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, List, Any
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


class ProjectBase(BaseModel):
    """Base project model"""
    title: str = Field(..., min_length=2, max_length=200)
    description: str
    deadline: Optional[datetime] = None
    status: str = "active"  # active, completed, on_hold, cancelled


class ProjectCreate(ProjectBase):
    """Project creation model"""
    teamLeadId: Optional[str] = None
    documents: Optional[List[str]] = []  # List of document IDs


class ProjectUpdate(BaseModel):
    """Project update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None
    teamLeadId: Optional[str] = None
    progress: Optional[int] = None


class Project(ProjectBase):
    """Project model for responses"""
    id: str = Field(alias="_id")
    startupId: str
    managerId: str
    teamLeadId: Optional[str] = None
    teamLead: Optional[str] = None  # Team lead name for display
    progress: int = 0
    documents: List[str] = []
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }


class ProjectInDB(ProjectBase):
    """Project model as stored in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    startupId: str
    managerId: str  # User ID of manager who created
    teamLeadId: Optional[str] = None
    progress: int = 0
    documents: List[str] = []  # Document IDs
    techStackId: Optional[str] = None  # Reference to tech stack
    teamFormationId: Optional[str] = None  # Reference to team formation
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

