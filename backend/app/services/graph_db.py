from neo4j import GraphDatabase
from typing import Dict, Any, List, Optional
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class GraphDBService:
    """
    Neo4j Knowledge Graph Service
    Stores relationships: Skills → Roles → Jobs → Gaps → Learning Paths
    """

    def __init__(self):
        # Connect to Neo4j (direct bolt connection)
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Verify connection
            self.driver.verify_connectivity()
            self._initialize_schema()
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}. Graph features will be disabled.")
            self.driver = None

    # =========================
    # SCHEMA INITIALIZATION
    # =========================
    def _initialize_schema(self):
        """Create indexes and constraints"""
        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE"
            )
            session.run(
                "CREATE INDEX IF NOT EXISTS FOR (j:Job) ON (j.id)"
            )
            logger.info("Graph database schema initialized")

    def close(self):
        if self.driver:
            self.driver.close()

    # =========================
    # USER OPERATIONS
    # =========================
    def create_user_node(self, user_id: str, user_data: Dict[str, Any]):
        """Create user node in graph (gracefully fails if driver unavailable)"""
        if not self.driver:
            logger.warning("GraphDB driver not available, skipping user node creation")
            return
        with self.driver.session() as session:
            session.run(
                """
                MERGE (u:User {id: $user_id})
                SET u.name = $name,
                    u.email = $email,
                    u.target_role = $target_role,
                    u.created_at = datetime()
                """,
                user_id=user_id,
                **user_data,
            )

    # =========================
    # SKILL OPERATIONS
    # =========================
    def add_user_skill(
        self,
        user_id: str,
        skill: str,
        level: str = "intermediate",
        verified: bool = False,
    ):
        if not self.driver:
            logger.warning("GraphDB driver not available, skipping skill addition")
            return
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MERGE (s:Skill {name: $skill})
                MERGE (u)-[r:HAS_SKILL]->(s)
                SET r.level = $level,
                    r.verified = $verified,
                    r.added_at = datetime()
                """,
                user_id=user_id,
                skill=skill,
                level=level,
                verified=verified,
            )

    def get_user_skills(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.driver:
            return []
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[r:HAS_SKILL]->(s:Skill)
                RETURN s.name as skill, r.level as level, r.verified as verified
                """,
                user_id=user_id,
            )
            return [dict(record) for record in result]

    # =========================
    # ROLE & JOB OPERATIONS
    # =========================
    def create_target_role(
        self,
        user_id: str,
        role_name: str,
        target_company: Optional[str] = None,
    ):
        if not self.driver:
            logger.warning("GraphDB driver not available, skipping role creation")
            return
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MERGE (r:Role {name: $role_name})
                MERGE (u)-[rel:TARGETS]->(r)
                SET rel.created_at = datetime(),
                    rel.company = $company
                """,
                user_id=user_id,
                role_name=role_name,
                company=target_company,
            )

    def add_job_opportunity(
        self,
        job_id: str,
        title: str,
        company: str,
        required_skills: List[str],
        user_id: str,
        compatibility_score: float,
    ):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (j:Job {id: $job_id})
                SET j.title = $title,
                    j.company = $company,
                    j.discovered_at = datetime(),
                    j.compatibility_score = $score
                """,
                job_id=job_id,
                title=title,
                company=company,
                score=compatibility_score,
            )

            for skill in required_skills:
                session.run(
                    """
                    MATCH (j:Job {id: $job_id})
                    MERGE (s:Skill {name: $skill})
                    MERGE (j)-[:REQUIRES]->(s)
                    """,
                    job_id=job_id,
                    skill=skill,
                )

            session.run(
                """
                MATCH (u:User {id: $user_id}), (j:Job {id: $job_id})
                MERGE (u)-[r:DISCOVERED]->(j)
                SET r.discovered_at = datetime()
                """,
                user_id=user_id,
                job_id=job_id,
            )

    def get_skill_gaps_for_job(self, user_id: str, job_id: str) -> List[str]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id}), (j:Job {id: $job_id})
                MATCH (j)-[:REQUIRES]->(required:Skill)
                WHERE NOT EXISTS {
                    MATCH (u)-[:HAS_SKILL]->(required)
                }
                RETURN required.name as skill
                """,
                user_id=user_id,
                job_id=job_id,
            )
            return [record["skill"] for record in result]

    # =========================
    # LEARNING PATH OPERATIONS
    # =========================
    def create_learning_path(
        self,
        user_id: str,
        skill: str,
        resources: List[str],
        estimated_hours: int,
        priority: str = "medium",
    ):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MERGE (s:Skill {name: $skill})
                MERGE (u)-[r:LEARNING]->(s)
                SET r.resources = $resources,
                    r.estimated_hours = $hours,
                    r.priority = $priority,
                    r.started_at = datetime(),
                    r.progress = 0
                """,
                user_id=user_id,
                skill=skill,
                resources=resources,
                hours=estimated_hours,
                priority=priority,
            )

    def update_learning_progress(self, user_id: str, skill: str, progress: int):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})-[r:LEARNING]->(s:Skill {name: $skill})
                SET r.progress = $progress,
                    r.last_updated = datetime()
                """,
                user_id=user_id,
                skill=skill,
                progress=progress,
            )

    # =========================
    # PROJECT OPERATIONS
    # =========================
    def add_project_with_skills(
        self,
        user_id: str,
        project_id: str,
        title: str,
        skills_used: List[str],
    ):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MERGE (p:Project {id: $project_id})
                SET p.title = $title
                MERGE (u)-[:BUILT]->(p)
                """,
                user_id=user_id,
                project_id=project_id,
                title=title,
            )

            for skill in skills_used:
                session.run(
                    """
                    MATCH (p:Project {id: $project_id})
                    MERGE (s:Skill {name: $skill})
                    MERGE (p)-[:USES]->(s)
                    """,
                    project_id=project_id,
                    skill=skill,
                )

    # =========================
    # REASONING / RECOMMENDATION
    # =========================
    def get_recommended_skills(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:TARGETS]->(r:Role)
                MATCH (r)<-[:PREPARES_FOR]-(s:Skill)
                WHERE NOT EXISTS {
                    MATCH (u)-[:HAS_SKILL]->(s)
                }
                RETURN s.name as skill,
                       COUNT(*) as relevance
                ORDER BY relevance DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit,
            )
            return [dict(record) for record in result]

    # =========================
    # GRAPH VISUALIZATION
    # =========================
    def get_career_path_graph(self, user_id: str) -> Dict[str, Any]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})
                OPTIONAL MATCH path = (u)-[*1..3]-(n)
                RETURN u, collect(distinct n) as nodes, collect(distinct path) as paths
                """,
                user_id=user_id,
            )

            record = result.single()
            if not record:
                return {"nodes": [], "edges": []}

            return self._format_graph_data(record)

    def _format_graph_data(self, record) -> Dict[str, Any]:
        # Placeholder for frontend graph transformation
        return {"nodes": [], "edges": []}

    # =========================
    # DELETE
    # =========================
    def delete_user_graph(self, user_id: str):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                DETACH DELETE u
                """,
                user_id=user_id,
            )


# =========================
# LAZY SINGLETON (SAFE)
# =========================
_graph_db: Optional[GraphDBService] = None


def get_graph_db() -> GraphDBService:
    """Lazy-load graph database instance"""
    global _graph_db
    if _graph_db is None:
        _graph_db = GraphDBService()
    return _graph_db

# Export function for lazy loading
graph_db = get_graph_db
