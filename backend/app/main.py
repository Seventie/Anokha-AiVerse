# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.settings import settings
from app.config.database import engine
from app.models.database import Base
import logging
import numpy as np

# Import routers
from app.routes import (
    auth, 
    agents, 
    knowledge_graph, 
    interview,
    resume,
    opportunities,
    journal,
    profile,
    dashboard,
    roadmap
)
from app.routes import cold_email  # ✅ Add import

# Fix numpy deprecation warning
np.float_ = np.float64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CareerAI API",
    description="AI-powered career guidance platform with Knowledge Graphs & Roadmap Scheduler",
    version="2.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static mounts
try:
    app.mount("/interview_audio", StaticFiles(directory=settings.INTERVIEW_AUDIO_PATH), name="interview_audio")
    app.mount("/interview_recordings", StaticFiles(directory=settings.INTERVIEW_STORAGE_PATH), name="interview_recordings")
except Exception as e:
    logger.warning(f"⚠ Static file mounts failed: {e}")

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database, services, and scheduler on startup"""
    logger.info("=" * 80)
    logger.info("🚀 CAREERAI API STARTING UP")
    logger.info("=" * 80)
    
    # 1. Initialize SQL Database
    try:
        logger.info("📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # 2. Initialize Background Scheduler
    try:
        logger.info("⏰ Starting background scheduler...")
        from scheduler import start_scheduler
        start_scheduler()
        logger.info("✅ Scheduler started (Weekly emails + Daily streak checks)")
    except Exception as e:
        logger.error(f"❌ Scheduler initialization failed: {e}")
    
    # 3. Schedule heavy service initializations in background
    import asyncio as _asyncio
    
    async def init_vector_db():
        try:
            from app.services.vector_db import vector_db
            logger.info("✅ Vector database initialized")
        except Exception as e:
            logger.warning(f"⚠ Vector database initialization failed: {e}")

    async def init_graph_db():
        try:
            from app.services.graph_db import get_graph_db
            graph_db = get_graph_db()
            if graph_db.driver:
                logger.info("✅ Neo4j Knowledge Graph connected")
                
                # Verify static graphs exist
                try:
                    with graph_db.driver.session() as session:
                        skill_count = session.run("MATCH (s:Skill) RETURN count(s) as count").single()["count"]
                        role_count = session.run("MATCH (j:JobRole) RETURN count(j) as count").single()["count"]
                        
                        if skill_count == 0 or role_count == 0:
                            logger.warning("⚠ Static knowledge graphs not initialized!")
                            logger.warning("  Run: python -m app.scripts.init_global_graphs")
                        else:
                            logger.info(f"  📈 Skills: {skill_count}")
                            logger.info(f"  💼 Job Roles: {role_count}")
                except Exception as inner_e:
                    logger.warning(f"⚠ Knowledge graph verification failed: {inner_e}")
            else:
                logger.warning("⚠ Neo4j not connected - graph features disabled")
        except Exception as e:
            logger.warning(f"⚠ Knowledge Graph initialization failed: {e}")
    
    # Fire-and-forget background tasks
    try:
        _asyncio.create_task(init_vector_db())
        _asyncio.create_task(init_graph_db())
    except Exception as e:
        logger.warning(f"Failed to schedule background inits: {e}")
    
    logger.info("=" * 80)
    logger.info("✅ STARTUP COMPLETE - All systems ready")
    logger.info("=" * 80)

# ==================== SHUTDOWN EVENT ====================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down services...")
    
    # 1. Stop scheduler
    try:
        from scheduler import shutdown_scheduler
        shutdown_scheduler()
        logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.warning(f"⚠ Error stopping scheduler: {e}")
    
    # 2. Close Neo4j connection
    try:
        from app.services.graph_db import get_graph_db
        graph_db = get_graph_db()
        if graph_db.driver:
            graph_db.close()
            logger.info("✅ Neo4j connection closed")
    except Exception as e:
        logger.warning(f"⚠ Error closing Neo4j: {e}")
    
    logger.info("👋 Shutdown complete")

# ==================== INCLUDE ROUTERS ====================

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(knowledge_graph.router)
app.include_router(interview.router)
app.include_router(resume.router)
app.include_router(opportunities.router)
app.include_router(journal.router)
app.include_router(profile.router)
app.include_router(dashboard.router)
app.include_router(roadmap.router)
app.include_router(cold_email.router) 

# Compatibility WebSocket route
from app.routes import agents as agents_routes
app.websocket("/ws")(agents_routes.websocket_endpoint)

# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "status": "healthy",
        "service": "CareerAI API",
        "version": "2.1.0",
        "features": [
            "User Management",
            "AI Agents (LangChain + LangGraph)",
            "Knowledge Graphs (Neo4j)",
            "Vector Search",
            "Career Analysis",
            "AI Roadmap Scheduler",
            "Google Calendar Integration",
            "Weekly Email Summaries",
            "Smart Notifications"
        ],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "services": {}
    }
    
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()
    
    # 1. Check SQL Database
    try:
        from app.config.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["services"]["postgresql"] = "✅ connected"
    except Exception as e:
        health_status["services"]["postgresql"] = f"❌ error: {str(e)}"
        health_status["status"] = "degraded"
    
    # 2. Check Vector DB
    try:
        from app.services.vector_db import vector_db
        if vector_db:
            health_status["services"]["vector_db"] = "✅ connected"
        else:
            health_status["services"]["vector_db"] = "⚠ not initialized"
    except Exception as e:
        health_status["services"]["vector_db"] = f"❌ error: {str(e)}"
    
    # 3. Check Neo4j
    try:
        from app.services.graph_db import get_graph_db
        graph_db = get_graph_db()
        if graph_db.driver:
            graph_db.driver.verify_connectivity()
            health_status["services"]["neo4j"] = "✅ connected"
        else:
            health_status["services"]["neo4j"] = "⚠ not connected"
    except Exception as e:
        health_status["services"]["neo4j"] = f"❌ error: {str(e)}"
        health_status["status"] = "degraded"
    
    # 4. Check Scheduler
    try:
        from scheduler import scheduler
        if scheduler.running:
            health_status["services"]["scheduler"] = "✅ running"
            # Get job info
            jobs = scheduler.get_jobs()
            health_status["scheduled_jobs"] = [
                {
                    "id": job.id,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        else:
            health_status["services"]["scheduler"] = "⚠ not running"
    except Exception as e:
        health_status["services"]["scheduler"] = f"❌ error: {str(e)}"
    
    # 5. Check LLM Service
    try:
        from app.services.llm_service import llm_service
        if llm_service.client:
            health_status["services"]["groq_llm"] = "✅ connected"
        else:
            health_status["services"]["groq_llm"] = "⚠ not initialized"
    except Exception as e:
        health_status["services"]["groq_llm"] = f"❌ error: {str(e)}"
    
    return health_status

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    import platform
    
    # Avoid auto-reload on Windows (can cause subprocess issues)
    use_reload = settings.ENVIRONMENT == "development" and platform.system() != "Windows"
    
    logger.info("🚀 Starting CareerAI API Server...")
    logger.info(f"📍 Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"🔧 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔄 Auto-reload: {use_reload}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=use_reload,
        log_level="info"
    )
