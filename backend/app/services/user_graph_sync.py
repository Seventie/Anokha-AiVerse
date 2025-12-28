# backend/app/services/user_graph_sync.py

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.database import User, Skill, Project, Experience, CareerGoal
from app.services.graph_db import get_graph_db
from app.utils.graph_queries import CypherQueries

logger = logging.getLogger(__name__)


class UserGraphSync:
    """
    Synchronizes user data from PostgreSQL to Neo4j.
    Handles user-centric knowledge graph updates.
    """
    
    def __init__(self):
        self.graph_db = get_graph_db()
        self.queries = CypherQueries()
    
    # ========================
    # SYNC USER NODE
    # ========================
    
    def sync_user_node(self, user: User) -> bool:
        """Create or update User node in Neo4j"""
        if not self.graph_db.driver:
            logger.warning("GraphDB not available")
            return False
        
        try:
            with self.graph_db.driver.session() as session:
                session.run(
                    self.queries.MERGE_USER,
                    id=user.id,
                    name=user.full_name or user.username,
                    email=user.email,
                    target_role=None  # Will be set separately
                )
            logger.info(f"Synced user node: {user.id}")
            return True
        except Exception as e:
            logger.error(f"Error syncing user node: {e}")
            return False
    
    # ========================
    # SYNC USER SKILLS
    # ========================
    
    def sync_user_skills(self, user_id: str, db: Session) -> int:
        """Sync user skills from SQL to Neo4j"""
        if not self.graph_db.driver:
            return 0
        
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        
        count = 0
        with self.graph_db.driver.session() as session:
            for skill in skills:
                try:
                    session.run(
                        self.queries.CREATE_USER_HAS_SKILL,
                        user_id=user_id,
                        skill=skill.skill,
                        level=skill.level.value if skill.level else "intermediate",
                        verified=skill.verified
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error syncing skill {skill.skill}: {e}")
        
        logger.info(f"Synced {count} skills for user {user_id}")
        return count
    
    # ========================
    # SYNC USER PROJECTS
    # ========================
    
    def sync_user_projects(self, user_id: str, db: Session) -> int:
        """Sync user projects from SQL to Neo4j"""
        if not self.graph_db.driver:
            return 0
        
        projects = db.query(Project).filter(Project.user_id == user_id).all()
        
        count = 0
        with self.graph_db.driver.session() as session:
            for project in projects:
                try:
                    # Create project node
                    session.run(
                        self.queries.MERGE_PROJECT,
                        id=str(project.id),
                        user_id=user_id,
                        title=project.title,
                        description=project.description or ""
                    )
                    
                    # Link user to project
                    session.run(
                        self.queries.CREATE_USER_BUILT_PROJECT,
                        user_id=user_id,
                        project_id=str(project.id)
                    )
                    
                    # Link project to skills
                    if project.tech_stack:
                        tech_skills = [s.strip() for s in project.tech_stack.split(',')]
                        for skill in tech_skills:
                            if skill:
                                session.run(
                                    self.queries.CREATE_PROJECT_USES_SKILL,
                                    project_id=str(project.id),
                                    skill=skill
                                )
                    
                    count += 1
                except Exception as e:
                    logger.error(f"Error syncing project {project.title}: {e}")
        
        logger.info(f"Synced {count} projects for user {user_id}")
        return count
    
    # ========================
    # SYNC CAREER GOALS
    # ========================
    
    def sync_career_goals(self, user_id: str, db: Session) -> int:
        """Sync career goals from SQL to Neo4j"""
        if not self.graph_db.driver:
            return 0
        
        career_goal = db.query(CareerGoal).filter(CareerGoal.user_id == user_id).first()
        
        if not career_goal:
            return 0
        
        count = 0
        with self.graph_db.driver.session() as session:
            # Create career goal node
            try:
                session.run(
                    self.queries.MERGE_CAREER_GOAL,
                    id=str(career_goal.id),
                    user_id=user_id,
                    target_roles=career_goal.target_roles or [],
                    timeline=career_goal.target_timeline or "6 Months"
                )
                
                # Link user to goal
                session.run(
                    self.queries.CREATE_USER_HAS_GOAL,
                    user_id=user_id,
                    goal_id=str(career_goal.id)
                )
                
                # Link user to target roles
                for role in career_goal.target_roles or []:
                    session.run(
                        self.queries.CREATE_USER_ASPIRES_TO_ROLE,
                        user_id=user_id,
                        job_role=role,
                        timeline=career_goal.target_timeline or "6 Months",
                        priority=1
                    )
                    count += 1
                
            except Exception as e:
                logger.error(f"Error syncing career goals: {e}")
        
        logger.info(f"Synced {count} career goals for user {user_id}")
        return count
    
    # ========================
    # COMPLETE USER SYNC
    # ========================
    
    def sync_complete_user(self, user_id: str, db: Session) -> Dict[str, int]:
        """Complete synchronization of user data to Neo4j"""
        logger.info(f"Starting complete sync for user: {user_id}")
        
        results = {}
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return results
        
        # Sync user node
        if self.sync_user_node(user):
            results["user"] = 1
        
        # Sync skills
        results["skills"] = self.sync_user_skills(user_id, db)
        
        # Sync projects
        results["projects"] = self.sync_user_projects(user_id, db)
        
        # Sync career goals
        results["goals"] = self.sync_career_goals(user_id, db)
        
        logger.info(f"Sync completed for user {user_id}: {results}")
        return results
    
    # ========================
    # BATCH SYNC
    # ========================
    
    def sync_all_users(self, db: Session) -> Dict[str, Any]:
        """Sync all users from SQL to Neo4j"""
        logger.info("Starting batch sync of all users...")
        
        users = db.query(User).all()
        results = {
            "total_users": len(users),
            "synced": 0,
            "failed": 0
        }
        
        for user in users:
            try:
                self.sync_complete_user(user.id, db)
                results["synced"] += 1
            except Exception as e:
                logger.error(f"Failed to sync user {user.id}: {e}")
                results["failed"] += 1
        
        logger.info(f"Batch sync completed: {results}")
        return results
    
    # ========================
    # DELETE USER
    # ========================
    
    def delete_user_graph(self, user_id: str) -> bool:
        """Delete user and all related nodes from Neo4j"""
        if not self.graph_db.driver:
            return False
        
        try:
            with self.graph_db.driver.session() as session:
                session.run(
                    self.queries.DELETE_USER_GRAPH,
                    user_id=user_id
                )
            logger.info(f"Deleted user graph: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user graph: {e}")
            return False


# Singleton instance
_user_graph_sync: Optional[UserGraphSync] = None

def get_user_graph_sync() -> UserGraphSync:
    """Get singleton UserGraphSync instance"""
    global _user_graph_sync
    if _user_graph_sync is None:
        _user_graph_sync = UserGraphSync()
    return _user_graph_sync
