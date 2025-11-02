"""
Team Member Model
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: any,
        _handler: any,
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(cls.validate),
        ], serialization=core_schema.plain_serializer_function_ser_schema(str))
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")


class TeamMemberBase(BaseModel):
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    techStack: List[str] = []
    recentProjects: List[str] = []
    experience: Optional[str] = None
    education: Optional[List[str]] = []
    skills: Optional[dict] = {}
    avatarUrl: Optional[str] = None
    resumeFilePath: Optional[str] = None


class TeamMemberCreate(TeamMemberBase):
    """Model for creating team member"""
    pass


class TeamMember(TeamMemberBase):
    """Model for team member response"""
    id: str = Field(alias="_id")
    projectId: str
    startupId: str
    createdAt: datetime
    updatedAt: datetime

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }


class TeamMemberInDB(TeamMemberBase):
    """Model for team member in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    projectId: str
    startupId: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

