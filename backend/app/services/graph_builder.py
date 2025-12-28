# backend/app/services/graph_builder.py

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from app.services.graph_db import get_graph_db
from app.utils.graph_queries import CypherQueries

logger = logging.getLogger(__name__)

class GraphBuilder:
    """
    Builds static/global knowledge graphs from JSON files.
    Handles batch processing and transaction management.
    """
    
    def __init__(self):
        self.graph_db = get_graph_db()
        self.queries = CypherQueries()
        self.knowledge_dir = Path(__file__).parent.parent / "knowledgeFiles"
        
    # ========================
    # FILE LOADERS
    # ========================
    
    def load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """Load and parse JSON file"""
        file_path = self.knowledge_dir / filename
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return [data]
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []
    
    # ========================
    # STATIC GRAPH BUILDERS
    # ========================
    
    def build_job_roles(self) -> int:
        """Build JobRole nodes from jobRoles.json"""
        logger.info("Building JobRole nodes...")
        job_roles = self.load_json_file("jobRoles.json")
        
        if not job_roles:
            logger.warning("No job roles found")
            return 0
        
        count = 0
        with self.graph_db.driver.session() as session:
            for job in job_roles:
                try:
                    session.run(
                        self.queries.MERGE_JOB_ROLE,
                        name=job["name"],
                        short_description=job["short_description"],
                        industry=job["industry"],
                        seniority_levels=job["seniority_levels"]
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error creating JobRole {job.get('name')}: {e}")
        
        logger.info(f"Created {count} JobRole nodes")
        return count
    
    def build_skills(self) -> int:
        """Build Skill nodes from skillCatalog.json"""
        logger.info("Building Skill nodes...")
        skills = self.load_json_file("skillCatalog.json")
        
        if not skills:
            logger.warning("No skills found")
            return 0
        
        count = 0
        with self.graph_db.driver.session() as session:
            for skill in skills:
                try:
                    session.run(
                        self.queries.MERGE_SKILL,
                        name=skill["name"],
                        category=skill["category"],
                        description=skill["description"]
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error creating Skill {skill.get('name')}: {e}")
        
        logger.info(f"Created {count} Skill nodes")
        return count
    
    def build_resources(self) -> int:
        """Build Resource nodes from resourceSkill.json"""
        logger.info("Building Resource nodes...")
        resources = self.load_json_file("resourceSkill.json")
        
        if not resources:
            logger.warning("No resources found")
            return 0
        
        count = 0
        with self.graph_db.driver.session() as session:
            for resource in resources:
                try:
                    session.run(
                        self.queries.MERGE_RESOURCE,
                        title=resource["resource_title"],
                        resource_type=resource["resource_type"],
                        url=resource["url"]
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error creating Resource {resource.get('resource_title')}: {e}")
        
        logger.info(f"Created {count} Resource nodes")
        return count
    
    # ========================
    # RELATIONSHIP BUILDERS
    # ========================
    
    def build_job_skill_requirements(self) -> int:
        """Build JobRole -> Skill relationships from jobSkill.json"""
        logger.info("Building Job-Skill requirement relationships...")
        mappings = self.load_json_file("jobSkill.json")
        
        if not mappings:
            logger.warning("No job-skill mappings found")
            return 0
        
        count = 0
        with self.graph_db.driver.session() as session:
            for mapping in mappings:
                job_role = mapping["job_role"]
                
                # Core skills (REQUIRES)
                for skill in mapping.get("core_skills", []):
                    try:
                        session.run(
                            self.queries.CREATE_JOB_REQUIRES_SKILL,
                            job_role=job_role,
                            skill=skill
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f"Error linking {job_role} -> {skill}: {e}")
                
                # Nice-to-have skills (NICE_TO_HAVE)
                for skill in mapping.get("nice_to_have_skills", []):
                    try:
                        session.run(
                            self.queries.CREATE_JOB_NICE_TO_HAVE_SKILL,
                            job_role=job_role,
                            skill=skill
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f"Error linking {job_role} -> {skill}: {e}")
        
        logger.info(f"Created {count} Job-Skill relationships")
        return count
    
    def build_skill_ontology(self) -> int:
        """Build Skill -> Skill relationships from skillOntology.json"""
        logger.info("Building Skill ontology relationships...")
        ontology = self.load_json_file("skillOntology.json")
        
        if not ontology:
            logger.warning("No skill ontology found")
            return 0
        
        count = 0
        with self.graph_db.driver.session() as session:
            for entry in ontology:
                skill = entry["skill"]
                
                # Prerequisites
                for prereq in entry.get("prerequisites", []):
                    try:
                        session.run(
                            self.queries.CREATE_SKILL_PREREQUISITE,
                            skill_from=prereq,
                            skill_to=skill
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f"Error linking prerequisite {prereq} -> {skill}: {e}")
                
                # Related skills (bidirectional)
                for related in entry.get("related_skills", []):
                    try:
                        session.run(
                            self.queries.CREATE_SKILL_RELATED,
                            skill1=skill,
                            skill2=related
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f"Error linking related {skill} <-> {related}: {e}")
        
        logger.info(f"Created {count} Skill ontology relationships")
        return count
    
    def build_resource_skill_mappings(self) -> int:
        """Build Resource -> Skill relationships from resourceSkill.json"""
        logger.info("Building Resource-Skill mappings...")
        resources = self.load_json_file("resourceSkill.json")
        
        if not resources:
            logger.warning("No resource-skill mappings found")
            return 0
        
        count = 0
        with self.graph_db.driver.session() as session:
            for resource in resources:
                resource_title = resource["resource_title"]
                
                for skill in resource.get("teaches_skills", []):
                    try:
                        session.run(
                            self.queries.CREATE_RESOURCE_TEACHES_SKILL,
                            resource_title=resource_title,
                            skill=skill
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f"Error linking {resource_title} -> {skill}: {e}")
        
        logger.info(f"Created {count} Resource-Skill relationships")
        return count
    
    # ========================
    # MASTER BUILD FUNCTION
    # ========================
    
    def build_all_static_graphs(self) -> Dict[str, int]:
        """Build all static/global knowledge graphs"""
        logger.info("=" * 60)
        logger.info("Starting static knowledge graph construction")
        logger.info("=" * 60)
        
        results = {}
        
        try:
            # Step 1: Create nodes
            results["job_roles"] = self.build_job_roles()
            results["skills"] = self.build_skills()
            results["resources"] = self.build_resources()
            
            # Step 2: Create relationships
            results["job_skill_mappings"] = self.build_job_skill_requirements()
            results["skill_ontology"] = self.build_skill_ontology()
            results["resource_skill_mappings"] = self.build_resource_skill_mappings()
            
            logger.info("=" * 60)
            logger.info("Static graph construction completed successfully")
            logger.info(f"Summary: {results}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during graph construction: {e}")
            raise
        
        return results
    
    # ========================
    # VALIDATION
    # ========================
    
    def validate_static_graphs(self) -> Dict[str, Any]:
        """Validate the constructed graphs"""
        logger.info("Validating static graphs...")
        
        validation_results = {}
        
        with self.graph_db.driver.session() as session:
            # Count nodes
            result = session.run("MATCH (j:JobRole) RETURN count(j) as count")
            validation_results["job_roles_count"] = result.single()["count"]
            
            result = session.run("MATCH (s:Skill) RETURN count(s) as count")
            validation_results["skills_count"] = result.single()["count"]
            
            result = session.run("MATCH (r:Resource) RETURN count(r) as count")
            validation_results["resources_count"] = result.single()["count"]
            
            # Count relationships
            result = session.run("MATCH ()-[r:REQUIRES]->() RETURN count(r) as count")
            validation_results["requires_count"] = result.single()["count"]
            
            result = session.run("MATCH ()-[r:NICE_TO_HAVE]->() RETURN count(r) as count")
            validation_results["nice_to_have_count"] = result.single()["count"]
            
            result = session.run("MATCH ()-[r:PREREQUISITE_OF]->() RETURN count(r) as count")
            validation_results["prerequisites_count"] = result.single()["count"]
            
            result = session.run("MATCH ()-[r:TEACHES]->() RETURN count(r) as count")
            validation_results["teaches_count"] = result.single()["count"]
            
            # Check for orphaned nodes
            result = session.run("""
                MATCH (s:Skill)
                WHERE NOT EXISTS {
                    MATCH (s)-[]-()
                }
                RETURN count(s) as count
            """)
            validation_results["orphaned_skills"] = result.single()["count"]
        
        logger.info(f"Validation results: {validation_results}")
        return validation_results


# Singleton instance
_graph_builder: GraphBuilder = None

def get_graph_builder() -> GraphBuilder:
    """Get singleton GraphBuilder instance"""
    global _graph_builder
    if _graph_builder is None:
        _graph_builder = GraphBuilder()
    return _graph_builder
