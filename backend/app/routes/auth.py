# backend/app/routes/auth.py - COMPLETE FIXED VERSION

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.database import (
    User, Education, Skill, Project, Experience, Availability, 
    CareerGoal, CareerIntent, PreferredLocation, SkillCategory, SkillLevel
)
from app.schemas.user import (
    UserRegister, UserLogin, Token, UserResponse, UserRegisterResponse,
    EducationResponse, SkillResponse, ProjectResponse, ExperienceResponse, AvailabilityResponse
)
from app.utils.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    decode_access_token,
    get_current_user_dict  # ✅ Import the dict version for Google OAuth
)
from app.services.vector_db import get_vector_db
from app.services.graph_db import get_graph_db
from app.services.user_graph_sync import get_user_graph_sync
from app.services.google_oauth import google_oauth  # ✅ Import here
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


def sync_user_to_graph_background(user_id: str):
    """Background task to sync user to knowledge graph"""
    try:
        from app.config.database import SessionLocal
        db = SessionLocal()
        sync_service = get_user_graph_sync()
        results = sync_service.sync_complete_user(user_id, db)
        db.close()
        logger.info(f"✓ Background graph sync completed for user {user_id}: {results}")
    except Exception as e:
        logger.error(f"✗ Background graph sync failed for user {user_id}: {e}")


@router.post("/register", response_model=UserRegisterResponse)
async def register(
    user_data: UserRegister, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user - ENHANCED with background graph sync"""
    
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
        full_name=user_data.full_name,
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
            start_date=edu.start_date,
            end_date=edu.end_date,
            grade=edu.grade,
            is_confirmed=True
        )
        db.add(db_edu)
    
    # Add Skills to SQL and Graph (immediate sync for skills)
    for skill_name in user_data.skills.get("technical", []):
        db_skill = Skill(
            user_id=user_id,
            skill=skill_name,
            category=SkillCategory.TECHNICAL,
            level=SkillLevel.INTERMEDIATE,
            is_confirmed=True
        )
        db.add(db_skill)
        
        # Immediate graph sync for skills (lightweight operation)
        try:
            get_graph_db().add_user_skill(user_id, skill_name, level="intermediate")
        except Exception as e:
            logger.warning(f"Failed to add skill to graph: {e}")
    
    for skill_name in user_data.skills.get("soft", []):
        db_skill = Skill(
            user_id=user_id,
            skill=skill_name,
            category=SkillCategory.SOFT,
            level=SkillLevel.INTERMEDIATE,
            is_confirmed=True
        )
        db.add(db_skill)
    
    # Add Projects
    for proj in user_data.projects:
        if not proj.title:
            continue
        db_proj = Project(
            user_id=user_id,
            title=proj.title,
            description=proj.description or "",
            tech_stack=proj.tech_stack or "",
            link=proj.link,
            is_confirmed=True
        )
        db.add(db_proj)
        db.flush()
        
        # Add to vector DB
        if proj.description:
            try:
                get_vector_db().add_project_context(user_id, db_proj.id, proj.description)
            except Exception as e:
                logger.warning(f"Failed to add project to vector DB: {e}")
    
    # Add Experience
    for exp in user_data.experience:
        if not exp.role or not exp.company:
            continue
        db_exp = Experience(
            user_id=user_id,
            role=exp.role,
            company=exp.company,
            location=exp.location or "",
            duration=exp.duration or "",
            description=exp.description or "",
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_confirmed=True
        )
        db.add(db_exp)
        db.flush()
        
        if exp.description:
            try:
                get_vector_db().add_experience_context(user_id, db_exp.id, exp.description)
            except Exception as e:
                logger.warning(f"Failed to add experience to vector DB: {e}")
    
    # Add Preferred Locations
    for idx, loc in enumerate(user_data.preferred_locations):
        db_loc = PreferredLocation(
            user_id=user_id,
            location=loc,
            priority=idx
        )
        db.add(db_loc)
    
    # Add Availability (always present now due to schema)
    db_avail = Availability(
        user_id=user_id,
        free_time=user_data.availability.free_time,
        study_days=user_data.availability.study_days
    )
    db.add(db_avail)
    
    # Add Career Goals
    db_goal = CareerGoal(
        user_id=user_id,
        target_roles=[user_data.target_role] if user_data.target_role else ["Software Engineer"],
        target_timeline=user_data.timeline or "6 Months"
    )
    db.add(db_goal)
    
    # Immediate graph sync for user node and target role (lightweight)
    try:
        graph = get_graph_db()
        if graph.driver:
            graph.create_user_node(user_id, {
                "name": user_data.full_name,
                "email": user_data.email,
                "target_role": user_data.target_role or "Software Engineer"
            })
            if user_data.target_role:
                graph.create_target_role(user_id, user_data.target_role)
    except Exception as e:
        logger.warning(f"Failed to add user to graph DB: {e}")
    
    # Add Career Intent
    if user_data.vision_statement:
        db_intent = CareerIntent(
            user_id=user_id,
            intent_text=user_data.vision_statement,
            is_confirmed=True
        )
        db.add(db_intent)
        
        try:
            get_vector_db().add_career_intent(user_id, user_data.vision_statement)
        except Exception as e:
            logger.warning(f"Failed to add career intent to vector DB: {e}")
    
    db.commit()
    db.refresh(db_user)
    
    # Schedule complete graph sync in background
    background_tasks.add_task(sync_user_to_graph_background, user_id)
    logger.info(f"📊 Scheduled complete graph sync for user {user_id}")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id, "email": user_data.email})
    
    # Get user profile
    user_profile = await get_user_profile(user_id, db)
    
    return UserRegisterResponse(
        user=user_profile,
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and return JWT token"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    return await get_user_profile(user_id, db)


async def get_user_profile(user_id: str, db: Session) -> UserResponse:
    """Helper to get complete user profile"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all related data
    education = db.query(Education).filter(Education.user_id == user_id).all()
    skills = db.query(Skill).filter(Skill.user_id == user_id).all()
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    experience = db.query(Experience).filter(Experience.user_id == user_id).all()
    availability = db.query(Availability).filter(Availability.user_id == user_id).first()
    career_goals = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
    career_intent = db.query(CareerIntent).filter(CareerIntent.user_id == user_id).first()
    preferred_locs = db.query(PreferredLocation).filter(
        PreferredLocation.user_id == user_id
    ).order_by(PreferredLocation.priority).all()
    
    # Build response
    email_username = user.email.split('@')[0] if user.email and '@' in user.email else "user"
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username or email_username,
        full_name=user.full_name or email_username.title(),
        location=user.location or "",
        preferred_locations=[loc.location for loc in preferred_locs] if preferred_locs else [],
        current_status=user.readiness_level.value if user.readiness_level else "beginner",
        field_of_interest="Software Engineering",
        target_role=career_goals.target_roles[0] if career_goals and career_goals.target_roles and len(career_goals.target_roles) > 0 else "Software Engineer",
        timeline=career_goals.target_timeline if career_goals and career_goals.target_timeline else "6 Months",
        vision_statement=career_intent.intent_text if career_intent and career_intent.intent_text else "",
        readiness_level=user.readiness_level.value if user.readiness_level else "beginner",
        is_demo=user.is_demo if user.is_demo is not None else False,
        created_at=user.created_at,
        education=[
            EducationResponse(
                id=e.id,
                institution=e.institution,
                degree=e.degree,
                major=e.major,
                location=e.location,
                duration=e.duration,
                start_date=e.start_date,
                end_date=e.end_date,
                grade=e.grade,
                is_confirmed=e.is_confirmed
            ) for e in education
        ] if education else [],
        skills=[
            SkillResponse(
                id=s.id,
                skill=s.skill,
                category=s.category.value if s.category else "technical",
                level=s.level.value if s.level else "intermediate",
                verified=s.verified,
                is_confirmed=s.is_confirmed
            ) for s in skills
        ] if skills else [],
        projects=[
            ProjectResponse(
                id=p.id,
                title=p.title,
                description=p.description or "",
                tech_stack=p.tech_stack or "",
                link=p.link,
                is_confirmed=p.is_confirmed
            ) for p in projects
        ] if projects else [],
        experience=[
            ExperienceResponse(
                id=e.id,
                role=e.role,
                company=e.company,
                location=e.location,
                duration=e.duration,
                description=e.description or "",
                start_date=e.start_date,
                end_date=e.end_date,
                is_confirmed=e.is_confirmed
            ) for e in experience
        ] if experience else [],
        availability=AvailabilityResponse(
            id=availability.id,
            free_time=availability.free_time or "",
            study_days=availability.study_days or []
        ) if availability else None
    )


# ========================================
# 🔗 GOOGLE OAUTH ENDPOINTS
# ========================================

@router.get("/google/connect")
async def connect_google(
    current_user: dict = Depends(get_current_user_dict)  # ✅ Use dict version
):
    """Generate Google OAuth URL"""
    try:
        # Check if Google OAuth is configured
        if not google_oauth:
            logger.error("Google OAuth service not initialized")
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured. Please check server settings."
            )
        
        user_id = current_user["user_id"]  # ✅ Dict access
        logger.info(f"🔗 Generating OAuth URL for user {user_id}")
        
        auth_url = google_oauth.get_authorization_url(user_id)
        
        return {
            "success": True,
            "auth_url": auth_url,
            "message": "Redirect user to approve Google Calendar + Gmail access"
        }
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,  # This is user_id
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        user_id = state  # Extract user_id from state
        logger.info(f"🔄 Processing Google callback for user {user_id}")
        
        # Exchange code for token
        tokens = google_oauth.exchange_code_for_token(code, user_id, db)
        
        logger.info(f"✅ Google connected successfully for user {user_id}")
        
        # Redirect to frontend dashboard
        return RedirectResponse(
            url="http://localhost:3000/dashboard?google_connected=true",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Google callback failed: {e}", exc_info=True)
        return RedirectResponse(
            url=f"http://localhost:3000/dashboard?google_error={str(e)}",
            status_code=302
        )


@router.get("/google/status")
async def google_status(
    current_user: dict = Depends(get_current_user_dict),  # ✅ Use dict version
    db: Session = Depends(get_db)
):
    """Check if user has connected Google"""
    user_id = current_user["user_id"]  # ✅ Dict access
    user = db.query(User).filter(User.id == user_id).first()
    
    connected = user and user.google_access_token is not None
    
    return {
        "connected": connected,
        "has_calendar_access": connected,
        "has_gmail_access": connected
    }


@router.post("/google/disconnect")
async def disconnect_google(
    current_user: dict = Depends(get_current_user_dict),  # ✅ Use dict version
    db: Session = Depends(get_db)
):
    """Disconnect Google account"""
    user_id = current_user["user_id"]  # ✅ Dict access
    user = db.query(User).filter(User.id == user_id).first()
    
    if user:
        user.google_access_token = None
        user.google_refresh_token = None
        user.google_token_expiry = None
        db.commit()
        logger.info(f"🔌 Google disconnected for user {user_id}")
    
    return {"success": True, "message": "Google account disconnected"}
