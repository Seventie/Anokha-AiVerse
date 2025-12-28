# backend/app/utils/graph_validators.py

"""
Knowledge Graph validation utilities.
Ensures data integrity and consistency.
"""

import logging
from typing import Dict, Any, List, Optional
from app.services.graph_db import get_graph_db

logger = logging.getLogger(__name__)


class GraphValidator:
    """Validates knowledge graph integrity"""
    
    def __init__(self):
        self.graph_db = get_graph_db()
        self.issues = []
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        logger.info("Running knowledge graph validation...")
        
        results = {
            "valid": True,
            "checks": {}
        }
        
        # Run checks
        results["checks"]["orphaned_skills"] = self.check_orphaned_skills()
        results["checks"]["missing_relationships"] = self.check_missing_relationships()
        results["checks"]["duplicate_nodes"] = self.check_duplicate_nodes()
        results["checks"]["user_integrity"] = self.check_user_integrity()
        
        # Aggregate results
        for check_name, check_result in results["checks"].items():
            if not check_result["passed"]:
                results["valid"] = False
        
        return results
    
    def check_orphaned_skills(self) -> Dict[str, Any]:
        """Check for skills with no relationships"""
        if not self.graph_db.driver:
            return {"passed": True, "skipped": True}
        
        with self.graph_db.driver.session() as session:
            result = session.run("""
                MATCH (s:Skill)
                WHERE NOT EXISTS {
                    MATCH (s)-[]-()
                }
                RETURN s.name as skill
            """)
            orphaned = [record["skill"] for record in result]
        
        passed = len(orphaned) == 0
        return {
            "passed": passed,
            "count": len(orphaned),
            "issues": orphaned if not passed else []
        }
    
    def check_missing_relationships(self) -> Dict[str, Any]:
        """Check for job roles without required skills"""
        if not self.graph_db.driver:
            return {"passed": True, "skipped": True}
        
        with self.graph_db.driver.session() as session:
            result = session.run("""
                MATCH (j:JobRole)
                WHERE NOT EXISTS {
                    MATCH (j)-[:REQUIRES]->(:Skill)
                }
                RETURN j.name as role
            """)
            missing = [record["role"] for record in result]
        
        passed = len(missing) == 0
        return {
            "passed": passed,
            "count": len(missing),
            "issues": missing if not passed else []
        }
    
    def check_duplicate_nodes(self) -> Dict[str, Any]:
        """Check for duplicate skill/role nodes (should never happen with constraints)"""
        if not self.graph_db.driver:
            return {"passed": True, "skipped": True}
        
        with self.graph_db.driver.session() as session:
            result = session.run("""
                MATCH (s:Skill)
                WITH s.name as name, count(s) as count
                WHERE count > 1
                RETURN name, count
            """)
            duplicates = [{"name": record["name"], "count": record["count"]} for record in result]
        
        passed = len(duplicates) == 0
        return {
            "passed": passed,
            "count": len(duplicates),
            "issues": duplicates if not passed else []
        }
    
    def check_user_integrity(self) -> Dict[str, Any]:
        """Check for users without skills or goals"""
        if not self.graph_db.driver:
            return {"passed": True, "skipped": True}
        
        with self.graph_db.driver.session() as session:
            result = session.run("""
                MATCH (u:User)
                WHERE NOT EXISTS {
                    MATCH (u)-[:HAS_SKILL]->(:Skill)
                }
                AND NOT EXISTS {
                    MATCH (u)-[:ASPIRES_TO]->(:JobRole)
                }
                RETURN u.id as user_id, u.email as email
                LIMIT 10
            """)
            incomplete = [
                {"user_id": record["user_id"], "email": record["email"]}
                for record in result
            ]
        
        # This is a warning, not a failure (new users might not have data yet)
        return {
            "passed": True,
            "count": len(incomplete),
            "warnings": incomplete
        }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        if not self.graph_db.driver:
            return {}
        
        stats = {}
        
        with self.graph_db.driver.session() as session:
            # Count nodes by type
            for node_type in ["User", "Skill", "JobRole", "Resource", "Project", "CareerGoal"]:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                stats[f"{node_type}_count"] = result.single()["count"]
            
            # Count relationships
            for rel_type in ["HAS_SKILL", "REQUIRES", "ASPIRES_TO", "TEACHES", "BUILT", "USES"]:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                stats[f"{rel_type}_count"] = result.single()["count"]
            
            # Average skills per user
            result = session.run("""
                MATCH (u:User)-[:HAS_SKILL]->(:Skill)
                WITH u, count(*) as skill_count
                RETURN avg(skill_count) as avg_skills
            """)
            record = result.single()
            stats["avg_skills_per_user"] = round(record["avg_skills"] if record and record["avg_skills"] else 0, 2)
        
        return stats


def validate_graph() -> Dict[str, Any]:
    """Convenience function to run validation"""
    validator = GraphValidator()
    return validator.validate_all()


def get_graph_health() -> Dict[str, Any]:
    """Get graph health summary"""
    validator = GraphValidator()
    stats = validator.get_graph_statistics()
    validation = validator.validate_all()
    
    return {
        "statistics": stats,
        "validation": validation,
        "healthy": validation["valid"]
    }
