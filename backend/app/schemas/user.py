# backend/app/schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Base schemas
class EducationBase(BaseModel):
    institution: str
    degree: str
    major: Optional[str] = None
    location: Optional[str] = None
    duration: str

class EducationCreate(EducationBase):
    pass

class EducationResponse(EducationBase):
    id: int
    is_confirmed: bool
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    title: str
    description: str
    techStack: str

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    is_confirmed: bool
    
    class Config:
        from_attributes = True

class ExperienceBase(BaseModel):
    role: str
    company: str
    location: Optional[str] = None
    duration: str
    description: str

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceResponse(ExperienceBase):
    id: int
    is_confirmed: bool
    
    class Config:
        from_attributes = True

class AvailabilityBase(BaseModel):
    freeTime: str
    studyDays: List[str]

class AvailabilityCreate(AvailabilityBase):
    pass

class AvailabilityResponse(AvailabilityBase):
    id: int
    
    class Config:
        from_attributes = True

# User Registration
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    fullName: str
    location: Optional[str] = None
    preferredLocations: List[str] = []
    currentStatus: str
    fieldOfInterest: str
    education: List[EducationCreate] = []
    experience: List[ExperienceCreate] = []
    projects: List[ProjectCreate] = []
    skills: dict  # {technical: [], soft: []}
    availability: AvailabilityCreate
    targetRole: str
    timeline: str
    visionStatement: str

# User Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# User Response
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    fullName: str
    location: Optional[str]
    preferredLocations: List[str]
    currentStatus: str
    fieldOfInterest: str
    targetRole: str
    timeline: str
    visionStatement: str
    readiness_level: str
    is_demo: bool
    created_at: datetime
    
    education: List[EducationResponse]
    skills: List[SkillResponse]
    projects: List[ProjectResponse]
    experience: List[ExperienceResponse]
    availability: Optional[AvailabilityResponse]
    
    class Config:
        from_attributes = True

# Resume Upload
class ResumeUpload(BaseModel):
    resumeText: str
    fileName: Optional[str] = None
    fileType: Optional[str] = None