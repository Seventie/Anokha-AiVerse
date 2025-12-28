# backend/app/scripts/init_global_graphs.py

"""
Initialization script to populate Neo4j with static/global knowledge graphs.
Run this ONCE after setting up Neo4j and before starting the application.

Usage:
    python -m app.scripts.init_global_graphs
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.graph_builder import get_graph_builder
from app.services.graph_db import get_graph_db
from app.utils.graph_queries import CypherQueries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_schema():
    """Create constraints and indexes"""
    logger.info("Initializing Neo4j schema...")
    
    graph_db = get_graph_db()
    queries = CypherQueries()
    
    with graph_db.driver.session() as session:
        # Create constraints
        for query in queries.CREATE_CONSTRAINTS:
            try:
                session.run(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Constraint already exists or error: {e}")
        
        # Create indexes
        for query in queries.CREATE_INDEXES:
            try:
                session.run(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Index already exists or error: {e}")
    
    logger.info("Schema initialization completed")


def build_static_graphs():
    """Build all static knowledge graphs"""
    logger.info("Building static knowledge graphs...")
    
    builder = get_graph_builder()
    results = builder.build_all_static_graphs()
    
    logger.info("Static graphs built successfully")
    return results


def validate_graphs():
    """Validate the constructed graphs"""
    logger.info("Validating graphs...")
    
    builder = get_graph_builder()
    validation = builder.validate_static_graphs()
    
    # Check for issues
    issues = []
    
    if validation["job_roles_count"] == 0:
        issues.append("No JobRole nodes found")
    
    if validation["skills_count"] < 50:
        issues.append(f"Low skill count: {validation['skills_count']}")
    
    if validation["orphaned_skills"] > 0:
        issues.append(f"Found {validation['orphaned_skills']} orphaned skills")
    
    if issues:
        logger.warning("Validation issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("✓ All validations passed")
    
    return validation


def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("NEO4J KNOWLEDGE GRAPH INITIALIZATION")
    logger.info("=" * 80)
    
    try:
        # Step 1: Initialize schema
        logger.info("\n[1/3] Initializing schema...")
        initialize_schema()
        
        # Step 2: Build static graphs
        logger.info("\n[2/3] Building static graphs...")
        results = build_static_graphs()
        
        # Step 3: Validate
        logger.info("\n[3/3] Validating graphs...")
        validation = validate_graphs()
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("INITIALIZATION COMPLETE")
        logger.info("=" * 80)
        logger.info("\nNodes Created:")
        logger.info(f"  - JobRoles: {results.get('job_roles', 0)}")
        logger.info(f"  - Skills: {results.get('skills', 0)}")
        logger.info(f"  - Resources: {results.get('resources', 0)}")
        logger.info("\nRelationships Created:")
        logger.info(f"  - Job-Skill Mappings: {results.get('job_skill_mappings', 0)}")
        logger.info(f"  - Skill Ontology: {results.get('skill_ontology', 0)}")
        logger.info(f"  - Resource-Skill: {results.get('resource_skill_mappings', 0)}")
        logger.info("\nValidation:")
        logger.info(f"  - Total Skills: {validation['skills_count']}")
        logger.info(f"  - REQUIRES relationships: {validation['requires_count']}")
        logger.info(f"  - Orphaned skills: {validation['orphaned_skills']}")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ INITIALIZATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
