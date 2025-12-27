# backend/init_db.py

"""
Database initialization script
Run this to create tables and add demo user
"""

from app.config.database import engine
from app.models.database import Base, User, Education, Skill, Project, Experience, CareerGoal, CareerIntent, Availability, PreferredLocation
from app.utils.auth import get_password_hash
from sqlalchemy.orm import Session
import uuid

def init_database():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

def create_demo_user():
    """Create demo user with sample data"""
    from app.config.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Check if demo user exists
        existing = db.query(User).filter(User.email == "demo@adviceguide.ai").first()
        if existing:
            print("✓ Demo user already exists")
            return
        
        # Create demo user
        demo_id = str(uuid.uuid4())
        demo_user = User(
            id=demo_id,
            email="demo@adviceguide.ai",
            username="demo_user",
            hashed_password=get_password_hash("demo"),
            full_name="Alex Demo",
            location="San Francisco, CA",
            readiness_level="intermediate",
            is_demo=True
        )
        db.add(demo_user)
        
        # Add education
        edu = Education(
            user_id=demo_id,
            institution="Stanford University",
            degree="Bachelor of Science",
            major="Computer Science",
            location="Stanford, CA",
            duration="Sep 2018 - Jun 2022",
            is_confirmed=True
        )
        db.add(edu)
        
        # Add skills
        skills_data = [
            ("Python", "technical"),
            ("React", "technical"),
            ("Machine Learning", "technical"),
            ("Leadership", "soft"),
            ("Communication", "soft")
        ]
        for skill_name, category in skills_data:
            skill = Skill(
                user_id=demo_id,
                skill=skill_name,
                category=category,
                level="advanced",
                verified=True,
                is_confirmed=True
            )
            db.add(skill)
        
        # Add project
        project = Project(
            user_id=demo_id,
            title="AI Career Assistant",
            description="Built an AI-powered career guidance platform using React, Python, and GPT-4. Implemented resume parsing, job matching, and personalized learning paths.",
            tech_stack="React, Python, FastAPI, PostgreSQL, ChromaDB",
            is_confirmed=True
        )
        db.add(project)
        
        # Add experience
        exp = Experience(
            user_id=demo_id,
            role="Software Engineer Intern",
            company="Tech Corp",
            location="San Francisco, CA",
            duration="Jun 2021 - Aug 2021",
            description="Developed full-stack features for user dashboard. Improved query performance by 40%. Collaborated with cross-functional teams.",
            is_confirmed=True
        )
        db.add(exp)
        
        # Add preferred locations
        locations = ["San Francisco, CA", "New York, NY", "Austin, TX"]
        for idx, loc in enumerate(locations):
            pref_loc = PreferredLocation(
                user_id=demo_id,
                location=loc,
                priority=idx
            )
            db.add(pref_loc)
        
        # Add availability
        avail = Availability(
            user_id=demo_id,
            free_time="2-4 hours",
            study_days=["Mon", "Wed", "Fri"]
        )
        db.add(avail)
        
        # Add career goals
        goal = CareerGoal(
            user_id=demo_id,
            target_roles=["Senior Software Engineer", "ML Engineer"],
            target_timeline="6 Months",
            short_term_goal="Master system design and ML fundamentals",
            long_term_goal="Lead AI engineering teams at top tech companies"
        )
        db.add(goal)
        
        # Add career intent
        intent = CareerIntent(
            user_id=demo_id,
            intent_text="I am passionate about building AI systems that solve real-world problems. My goal is to transition into a senior ML engineering role where I can lead innovative projects and mentor junior engineers.",
            is_confirmed=True
        )
        db.add(intent)
        
        db.commit()
        print("✓ Demo user created successfully")
        print(f"  Email: demo@adviceguide.ai")
        print(f"  Password: demo")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating demo user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    create_demo_user()
    print("\n✓ Database initialization complete!")