# backend/app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Base schemas
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
    pass

class EducationResponse(BaseModel):
    id: int
    institution: str
    degree: str
    major: Optional[str] = None
    location: Optional[str] = None
    duration: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None
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
    description: str = ""
    techStack: str = ""
    link: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str = ""
    techStack: str = Field(default="")
    link: Optional[str] = None
    is_confirmed: bool
    
    class Config:
        from_attributes = True

class ExperienceBase(BaseModel):
    role: str
    company: str
    location: Optional[str] = None
    duration: str = ""
    description: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceResponse(BaseModel):
    id: int
    role: str
    company: str
    location: Optional[str] = None
    duration: str = ""
    description: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_confirmed: bool
    
    class Config:
        from_attributes = True

class AvailabilityBase(BaseModel):
    freeTime: str
    studyDays: List[str]

class AvailabilityCreate(AvailabilityBase):
    pass

class AvailabilityResponse(BaseModel):
    id: int
    freeTime: str
    studyDays: List[str]
    
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
    currentStatus: Optional[str] = "Working Professional"
    fieldOfInterest: Optional[str] = "Software Engineering"
    education: List[EducationCreate] = []
    experience: List[ExperienceCreate] = []
    projects: List[ProjectCreate] = []
    skills: Optional[dict] = Field(default_factory=lambda: {"technical": [], "soft": []})  # {technical: [], soft: []}
    availability: Optional[AvailabilityCreate] = None
    targetRole: Optional[str] = "Software Engineer"
    timeline: Optional[str] = "6 Months"
    visionStatement: Optional[str] = ""

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
    location: Optional[str] = Field(default="")
    preferredLocations: List[str] = Field(default_factory=list)
    currentStatus: str = Field(default="beginner")
    fieldOfInterest: str = Field(default="Software Engineering")
    targetRole: str = Field(default="Software Engineer")
    timeline: str = Field(default="6 Months")
    visionStatement: str = Field(default="")
    readiness_level: str = Field(default="beginner")
    is_demo: bool = Field(default=False)
    created_at: datetime
    
    education: List[EducationResponse] = Field(default_factory=list)
    skills: List[SkillResponse] = Field(default_factory=list)
    projects: List[ProjectResponse] = Field(default_factory=list)
    experience: List[ExperienceResponse] = Field(default_factory=list)
    availability: Optional[AvailabilityResponse] = Field(default=None)
    
    class Config:
        from_attributes = True

# Registration Response (includes token)
class UserRegisterResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

# Resume Upload
class ResumeUpload(BaseModel):
    resumeText: str
    fileName: Optional[str] = None
    fileType: Optional[str] = None