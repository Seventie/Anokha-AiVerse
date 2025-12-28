# backend/app/main.py

from app.routes import auth, agents, knowledge_graph, interview
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.config.database import engine
from app.models.database import Base
import logging
from app.routes import resume 


import numpy as np
np.float_ = np.float64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CareerAI API",
    description="AI-powered career guidance platform with Knowledge Graphs",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("=" * 80)
    logger.info("CAREERAI API STARTING UP")
    logger.info("=" * 80)
    
    # Initialize SQL Database
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created successfully")
    # Schedule heavy service initializations in background to avoid blocking startup
    async def init_vector_db():
        try:
            from app.services.vector_db import vector_db
            logger.info("✓ Vector database initialized")
        except Exception as e:
            logger.warning(f"⚠ Vector database initialization failed: {e}")

    async def init_graph_db():
        try:
            from app.services.graph_db import get_graph_db
            graph_db = get_graph_db()
            if graph_db.driver:
                logger.info("✓ Neo4j Knowledge Graph connected")

                # Verify static graphs exist (run in background)
                try:
                    with graph_db.driver.session() as session:
                        skill_count = session.run("MATCH (s:Skill) RETURN count(s) as count").single()["count"]
                        role_count = session.run("MATCH (j:JobRole) RETURN count(j) as count").single()["count"]

                        if skill_count == 0 or role_count == 0:
                            logger.warning("⚠ Static knowledge graphs not initialized!")
                            logger.warning("  Run: python -m app.scripts.init_global_graphs")
                        else:
                            logger.info(f"  - Skills: {skill_count}")
                            logger.info(f"  - Job Roles: {role_count}")
                except Exception as inner_e:
                    logger.warning(f"⚠ Knowledge graph verification failed: {inner_e}")
            else:
                logger.warning("⚠ Neo4j not connected - graph features disabled")
        except Exception as e:
            logger.warning(f"⚠ Knowledge Graph initialization failed: {e}")

    # Fire-and-forget initialization tasks
    try:
        import asyncio as _asyncio
        _asyncio.create_task(init_vector_db())
        _asyncio.create_task(init_graph_db())
    except Exception as e:
        logger.warning(f"Failed to schedule background inits: {e}")
    
    logger.info("=" * 80)
    logger.info("STARTUP COMPLETE - All systems ready")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down services...")
    
    try:
        from app.services.graph_db import get_graph_db
        graph_db = get_graph_db()
        if graph_db.driver:
            graph_db.close()
            logger.info("✓ Neo4j connection closed")
    except Exception as e:
        logger.warning(f"Error closing Neo4j: {e}")

# Include routers
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(knowledge_graph.router) 
app.include_router(interview.router) 
app.include_router(resume.router) # NEW: Knowledge Graph routes

# Compatibility WebSocket route: support legacy clients connecting to '/ws'
from app.routes import agents as agents_routes
app.websocket("/ws")(agents_routes.websocket_endpoint)

# Health check endpoint
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "CareerAI API",
        "version": "2.0.0",
        "features": [
            "User Management",
            "AI Agents",
            "Knowledge Graphs",
            "Vector Search",
            "Career Analysis"
        ]
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check SQL Database
    try:
        from app.config.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["services"]["postgresql"] = "connected"
    except Exception as e:
        health_status["services"]["postgresql"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Vector DB
    try:
        from app.services.vector_db import vector_db
        if vector_db:
            health_status["services"]["vector_db"] = "connected"
        else:
            health_status["services"]["vector_db"] = "not initialized"
    except Exception as e:
        health_status["services"]["vector_db"] = f"error: {str(e)}"
    
    # Check Neo4j
    try:
        from app.services.graph_db import get_graph_db
        graph_db = get_graph_db()
        if graph_db.driver:
            graph_db.driver.verify_connectivity()
            health_status["services"]["neo4j"] = "connected"
        else:
            health_status["services"]["neo4j"] = "not connected"
    except Exception as e:
        health_status["services"]["neo4j"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    import platform
    # Avoid using uvicorn auto-reload on Windows (can cause subprocess stdin issues)
    use_reload = settings.ENVIRONMENT == "development" and platform.system() != "Windows"

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=use_reload
    )
