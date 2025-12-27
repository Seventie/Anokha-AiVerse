# backend/app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.database import User, Education, Skill, Project, Experience, Availability, CareerGoal, CareerIntent, PreferredLocation
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse
from app.utils.auth import verify_password, get_password_hash, create_access_token
from app.services.vector_db import vector_db
import uuid

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and populate both SQL and Vector DB"""
    
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create user
    user_id = str(uuid.uuid4())
    db_user = User(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.fullName,
        location=user_data.location,
        is_demo=False
    )
    db.add(db_user)
    db.flush()
    
    # Add Education
    for edu in user_data.education:
        db_edu = Education(
            user_id=user_id,
            institution=edu.institution,
            degree=edu.degree,
            major=edu.major,
            location=edu.location,
            duration=edu.duration,
            is_confirmed=True
        )
        db.add(db_edu)
    
    # Add Skills
    for skill_name in user_data.skills.get("technical", []):
        db_skill = Skill(
            user_id=user_id,
            skill=skill_name,
            category="technical",
            is_confirmed=True
        )
        db.add(db_skill)
    
    for skill_name in user_data.skills.get("soft", []):
        db_skill = Skill(
            user_id=user_id,
            skill=skill_name,
            category="soft",
            is_confirmed=True
        )
        db.add(db_skill)
    
    # Add Projects
    for proj in user_data.projects:
        db_proj = Project(
            user_id=user_id,
            title=proj.title,
            description=proj.description,
            tech_stack=proj.techStack,
            is_confirmed=True
        )
        db.add(db_proj)
        db.flush()
        
        # Add project description to Vector DB
        if proj.description:
            vector_db.add_project_context(user_id, db_proj.id, proj.description)
    
    # Add Experience
    for exp in user_data.experience:
        db_exp = Experience(
            user_id=user_id,
            role=exp.role,
            company=exp.company,
            location=exp.location,
            duration=exp.duration,
            description=exp.description,
            is_confirmed=True
        )
        db.add(db_exp)
        db.flush()
        
        # Add experience description to Vector DB
        if exp.description:
            vector_db.add_experience_context(user_id, db_exp.id, exp.description)
    
    # Add Preferred Locations
    for idx, loc in enumerate(user_data.preferredLocations):
        db_loc = PreferredLocation(
            user_id=user_id,
            location=loc,
            priority=idx
        )
        db.add(db_loc)
    
    # Add Availability
    db_avail = Availability(
        user_id=user_id,
        free_time=user_data.availability.freeTime,
        study_days=user_data.availability.studyDays
    )
    db.add(db_avail)
    
    # Add Career Goals
    db_goal = CareerGoal(
        user_id=user_id,
        target_roles=[user_data.targetRole],
        target_timeline=user_data.timeline
    )
    db.add(db_goal)
    
    # Add Career Intent (HIGH PRIORITY for Vector DB)
    if user_data.visionStatement:
        db_intent = CareerIntent(
            user_id=user_id,
            intent_text=user_data.visionStatement,
            is_confirmed=True
        )
        db.add(db_intent)
        
        # Add to Vector DB with high priority
        vector_db.add_career_intent(user_id, user_data.visionStatement)
    
    db.commit()
    db.refresh(db_user)
    
    # Return user data
    return await get_user_profile(user_id, db)

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and return JWT token"""
    
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str, db: Session = Depends(get_db)):
    """Get current user profile"""
    from app.utils.auth import decode_access_token
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    return await get_user_profile(user_id, db)

async def get_user_profile(user_id: str, db: Session):
    """Helper to get complete user profile"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get preferred locations
    preferred_locs = db.query(PreferredLocation).filter(
        PreferredLocation.user_id == user_id
    ).order_by(PreferredLocation.priority).all()
    
    # Build response
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        fullName=user.full_name,
        location=user.location,
        preferredLocations=[loc.location for loc in preferred_locs],
        currentStatus=user.readiness_level.value if user.readiness_level else "beginner",
        fieldOfInterest="Software Engineering",  # TODO: Store this
        targetRole=user.career_goals.target_roles[0] if user.career_goals and user.career_goals.target_roles else "",
        timeline=user.career_goals.target_timeline if user.career_goals else "",
        visionStatement=user.career_intent.intent_text if user.career_intent else "",
        readiness_level=user.readiness_level.value if user.readiness_level else "beginner",
        is_demo=user.is_demo,
        created_at=user.created_at,
        education=[],  # TODO: Map from relationships
        skills=[],
        projects=[],
        experience=[],
        availability=None
    )