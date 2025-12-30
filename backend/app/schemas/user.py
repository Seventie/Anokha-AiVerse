# backend/app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional, Dict
from datetime import datetime


# Base schemas with camelCase aliases for API
class EducationBase(BaseModel):
    institution: str
    degree: str
    major: Optional[str] = None
    location: Optional[str] = None
    duration: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None


class EducationCreate(EducationBase):
    model_config = ConfigDict(populate_by_name=True)


class EducationResponse(EducationBase):
    id: int
    is_confirmed: bool
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SkillBase(BaseModel):
    skill: str
    category: str = "technical"
    level: str = "intermediate"


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int
    verified: bool
    is_confirmed: bool
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProjectBase(BaseModel):
    title: str
    description: str = ""
    tech_stack: str = Field(default="", alias="techStack")
    link: Optional[str] = None


class ProjectCreate(ProjectBase):
    model_config = ConfigDict(populate_by_name=True)


class ProjectResponse(ProjectBase):
    id: int
    is_confirmed: bool
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)


class ExperienceBase(BaseModel):
    role: str
    company: str
    location: Optional[str] = None
    duration: str = ""
    description: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ExperienceCreate(ExperienceBase):
    model_config = ConfigDict(populate_by_name=True)


class ExperienceResponse(ExperienceBase):
    id: int
    is_confirmed: bool
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AvailabilityBase(BaseModel):
    free_time: str = Field(alias="freeTime")
    study_days: List[str] = Field(default_factory=list, alias="studyDays")


class AvailabilityCreate(AvailabilityBase):
    model_config = ConfigDict(populate_by_name=True)


class AvailabilityResponse(AvailabilityBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# User Registration
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str
    location: Optional[str] = None
    preferred_locations: List[str] = Field(default_factory=list, alias="preferredLocations")
    current_status: Optional[str] = Field(default="Working Professional", alias="currentStatus")
    field_of_interest: Optional[str] = Field(default="Software Engineering", alias="fieldOfInterest")
    education: List[EducationCreate] = Field(default_factory=list)
    experience: List[ExperienceCreate] = Field(default_factory=list)
    projects: List[ProjectCreate] = Field(default_factory=list)
    skills: Optional[Dict[str, List[str]]] = Field(default_factory=lambda: {"technical": [], "soft": []})
    availability: AvailabilityCreate
    target_role: Optional[str] = Field(default="Software Engineer", alias="targetRole")
    timeline: Optional[str] = Field(default="6 Months")
    vision_statement: Optional[str] = Field(default="", alias="visionStatement")
    
    model_config = ConfigDict(populate_by_name=True)


# User Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# User Response (returns camelCase to frontend)
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str = Field(alias="fullName")
    location: Optional[str] = Field(default="")
    preferred_locations: List[str] = Field(default_factory=list, alias="preferredLocations")
    current_status: str = Field(default="beginner", alias="currentStatus")
    field_of_interest: str = Field(default="Software Engineering", alias="fieldOfInterest")
    target_role: str = Field(default="Software Engineer", alias="targetRole")
    timeline: str = Field(default="6 Months")
    vision_statement: str = Field(default="", alias="visionStatement")
    readiness_level: str = Field(default="beginner")
    is_demo: bool = Field(default=False)
    created_at: datetime
    
    education: List[EducationResponse] = Field(default_factory=list)
    skills: List[SkillResponse] = Field(default_factory=list)
    projects: List[ProjectResponse] = Field(default_factory=list)
    experience: List[ExperienceResponse] = Field(default_factory=list)
    availability: Optional[AvailabilityResponse] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Registration Response (includes token)
class UserRegisterResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# Resume Upload
class ResumeUpload(BaseModel):
    resume_text: str = Field(alias="resumeText")
    file_name: Optional[str] = Field(default=None, alias="fileName")
    file_type: Optional[str] = Field(default=None, alias="fileType")
    
    model_config = ConfigDict(populate_by_name=True)
