# backend/app/utils/graph_queries.py

from typing import Dict, Any, List

class CypherQueries:
    """
    All Cypher query templates for Neo4j knowledge graphs.
    Organized by graph type.
    """
    
    # ========================
    # SCHEMA SETUP
    # ========================
    
    CREATE_CONSTRAINTS = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (j:JobRole) REQUIRE j.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Resource) REQUIRE r.title IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Interview) REQUIRE i.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Feedback) REQUIRE f.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (cg:CareerGoal) REQUIRE cg.id IS UNIQUE",
    ]
    
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS FOR (j:JobRole) ON (j.industry)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Skill) ON (s.category)",
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.email)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Project) ON (p.user_id)",
    ]
    
    # ========================
    # STATIC GRAPH: Job-Skill Requirements
    # ========================
    
    MERGE_JOB_ROLE = """
        MERGE (j:JobRole {name: $name})
        SET j.short_description = $short_description,
            j.industry = $industry,
            j.seniority_levels = $seniority_levels,
            j.updated_at = datetime()
        RETURN j
    """
    
    MERGE_SKILL = """
        MERGE (s:Skill {name: $name})
        SET s.category = $category,
            s.description = $description,
            s.updated_at = datetime()
        RETURN s
    """
    
    CREATE_JOB_REQUIRES_SKILL = """
        MATCH (j:JobRole {name: $job_role})
        MATCH (s:Skill {name: $skill})
        MERGE (j)-[r:REQUIRES]->(s)
        SET r.importance = 'core',
            r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    CREATE_JOB_NICE_TO_HAVE_SKILL = """
        MATCH (j:JobRole {name: $job_role})
        MATCH (s:Skill {name: $skill})
        MERGE (j)-[r:NICE_TO_HAVE]->(s)
        SET r.importance = 'optional',
            r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    # ========================
    # STATIC GRAPH: Skill Ontology
    # ========================
    
    CREATE_SKILL_PREREQUISITE = """
        MATCH (s1:Skill {name: $skill_from})
        MATCH (s2:Skill {name: $skill_to})
        MERGE (s1)-[r:PREREQUISITE_OF]->(s2)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    CREATE_SKILL_RELATED = """
        MATCH (s1:Skill {name: $skill1})
        MATCH (s2:Skill {name: $skill2})
        MERGE (s1)-[r:RELATED_TO]->(s2)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    # ========================
    # STATIC GRAPH: Resource-Skill Mapping
    # ========================
    
    MERGE_RESOURCE = """
        MERGE (r:Resource {title: $title})
        SET r.resource_type = $resource_type,
            r.url = $url,
            r.updated_at = datetime()
        RETURN r
    """
    
    CREATE_RESOURCE_TEACHES_SKILL = """
        MATCH (r:Resource {title: $resource_title})
        MATCH (s:Skill {name: $skill})
        MERGE (r)-[rel:TEACHES]->(s)
        SET rel.created_at = coalesce(rel.created_at, datetime())
        RETURN rel
    """
    
    # ========================
    # USER GRAPH: User-Skill
    # ========================
    
    MERGE_USER = """
        MERGE (u:User {id: $id})
        SET u.name = $name,
            u.email = $email,
            u.target_role = $target_role,
            u.updated_at = datetime(),
            u.created_at = coalesce(u.created_at, datetime())
        RETURN u
    """
    
    CREATE_USER_HAS_SKILL = """
        MATCH (u:User {id: $user_id})
        MERGE (s:Skill {name: $skill})
        MERGE (u)-[r:HAS_SKILL]->(s)
        SET r.level = $level,
            r.verified = $verified,
            r.added_at = coalesce(r.added_at, datetime()),
            r.updated_at = datetime()
        RETURN r
    """
    
    CREATE_USER_LEARNING_SKILL = """
        MATCH (u:User {id: $user_id})
        MERGE (s:Skill {name: $skill})
        MERGE (u)-[r:LEARNING_SKILL]->(s)
        SET r.progress = $progress,
            r.started_at = coalesce(r.started_at, datetime()),
            r.estimated_hours = $estimated_hours,
            r.resources = $resources,
            r.updated_at = datetime()
        RETURN r
    """
    
    # ========================
    # USER GRAPH: User-Goal
    # ========================
    
    CREATE_USER_ASPIRES_TO_ROLE = """
        MATCH (u:User {id: $user_id})
        MERGE (j:JobRole {name: $job_role})
        MERGE (u)-[r:ASPIRES_TO]->(j)
        SET r.timeline = $timeline,
            r.created_at = coalesce(r.created_at, datetime()),
            r.priority = $priority
        RETURN r
    """
    
    MERGE_CAREER_GOAL = """
        MERGE (cg:CareerGoal {id: $id})
        SET cg.user_id = $user_id,
            cg.target_roles = $target_roles,
            cg.timeline = $timeline,
            cg.updated_at = datetime(),
            cg.created_at = coalesce(cg.created_at, datetime())
        RETURN cg
    """
    
    CREATE_USER_HAS_GOAL = """
        MATCH (u:User {id: $user_id})
        MATCH (cg:CareerGoal {id: $goal_id})
        MERGE (u)-[r:HAS_GOAL]->(cg)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    # ========================
    # USER GRAPH: User-Project
    # ========================
    
    MERGE_PROJECT = """
        MERGE (p:Project {id: $id})
        SET p.user_id = $user_id,
            p.title = $title,
            p.description = $description,
            p.updated_at = datetime(),
            p.created_at = coalesce(p.created_at, datetime())
        RETURN p
    """
    
    CREATE_USER_BUILT_PROJECT = """
        MATCH (u:User {id: $user_id})
        MATCH (p:Project {id: $project_id})
        MERGE (u)-[r:BUILT]->(p)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    CREATE_PROJECT_USES_SKILL = """
        MATCH (p:Project {id: $project_id})
        MERGE (s:Skill {name: $skill})
        MERGE (p)-[r:USES]->(s)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    # ========================
    # USER GRAPH: Feedback-Outcome
    # ========================
    
    MERGE_INTERVIEW = """
        MERGE (i:Interview {id: $id})
        SET i.user_id = $user_id,
            i.job_role = $job_role,
            i.company = $company,
            i.conducted_at = $conducted_at,
            i.overall_score = $overall_score,
            i.updated_at = datetime()
        RETURN i
    """
    
    MERGE_FEEDBACK = """
        MERGE (f:Feedback {id: $id})
        SET f.interview_id = $interview_id,
            f.content = $content,
            f.sentiment = $sentiment,
            f.created_at = $created_at,
            f.updated_at = datetime()
        RETURN f
    """
    
    CREATE_INTERVIEW_HAS_FEEDBACK = """
        MATCH (i:Interview {id: $interview_id})
        MATCH (f:Feedback {id: $feedback_id})
        MERGE (i)-[r:HAS_FEEDBACK]->(f)
        SET r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    CREATE_FEEDBACK_INDICATES_WEAKNESS = """
        MATCH (f:Feedback {id: $feedback_id})
        MERGE (s:Skill {name: $skill})
        MERGE (f)-[r:INDICATES_WEAKNESS]->(s)
        SET r.severity = $severity,
            r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    CREATE_FEEDBACK_INDICATES_STRENGTH = """
        MATCH (f:Feedback {id: $feedback_id})
        MERGE (s:Skill {name: $skill})
        MERGE (f)-[r:INDICATES_STRENGTH]->(s)
        SET r.confidence = $confidence,
            r.created_at = coalesce(r.created_at, datetime())
        RETURN r
    """
    
    # ========================
    # HYBRID GRAPH: Skill Gap Analysis
    # ========================
    
    GET_SKILL_GAPS = """
        MATCH (u:User {id: $user_id})
        MATCH (j:JobRole {name: $job_role})
        MATCH (j)-[:REQUIRES]->(required:Skill)
        WHERE NOT EXISTS {
            MATCH (u)-[:HAS_SKILL]->(required)
        }
        RETURN required.name as missing_skill,
               required.category as category,
               required.description as description
    """
    
    GET_USER_SKILLS_FOR_ROLE = """
        MATCH (u:User {id: $user_id})
        MATCH (j:JobRole {name: $job_role})
        MATCH (j)-[:REQUIRES]->(required:Skill)
        MATCH (u)-[r:HAS_SKILL]->(required)
        RETURN required.name as skill,
               r.level as level,
               r.verified as verified
    """
    
    GET_NICE_TO_HAVE_SKILLS = """
        MATCH (j:JobRole {name: $job_role})-[:NICE_TO_HAVE]->(s:Skill)
        RETURN s.name as skill,
               s.category as category,
               s.description as description
    """
    
    # ========================
    # HYBRID GRAPH: Readiness Scoring
    # ========================
    
    CALCULATE_READINESS = """
        MATCH (u:User {id: $user_id})
        MATCH (j:JobRole {name: $job_role})
        MATCH (j)-[:REQUIRES]->(required:Skill)
        WITH u, j, collect(required.name) as required_skills
        MATCH (u)-[:HAS_SKILL]->(has:Skill)
        WHERE has.name IN required_skills
        WITH u, j, required_skills, collect(has.name) as user_skills
        RETURN size(user_skills) * 100.0 / size(required_skills) as coverage_percentage,
               size(user_skills) as matched_skills,
               size(required_skills) as total_required,
               [skill IN required_skills WHERE NOT skill IN user_skills] as missing_skills
    """
    
    # ========================
    # HYBRID GRAPH: Learning Plan
    # ========================
    
    GET_LEARNING_RECOMMENDATIONS = """
        MATCH (u:User {id: $user_id})
        MATCH (u)-[:ASPIRES_TO]->(j:JobRole)
        MATCH (j)-[:REQUIRES]->(s:Skill)
        WHERE NOT EXISTS {
            MATCH (u)-[:HAS_SKILL]->(s)
        }
        MATCH (r:Resource)-[:TEACHES]->(s)
        RETURN s.name as skill,
               s.category as category,
               collect({
                   title: r.title,
                   type: r.resource_type,
                   url: r.url
               }) as resources
        ORDER BY s.category, s.name
        LIMIT 20
    """
    
    GET_PREREQUISITE_CHAIN = """
        MATCH (s:Skill {name: $skill})
        MATCH path = (prereq:Skill)-[:PREREQUISITE_OF*1..3]->(s)
        RETURN prereq.name as prerequisite,
               length(path) as depth
        ORDER BY depth
    """
    
    # ========================
    # UTILITY QUERIES
    # ========================
    
    DELETE_USER_GRAPH = """
        MATCH (u:User {id: $user_id})
        OPTIONAL MATCH (u)-[r]-()
        DELETE r, u
    """
    
    GET_ALL_JOB_ROLES = """
        MATCH (j:JobRole)
        RETURN j.name as name,
               j.industry as industry,
               j.seniority_levels as seniority_levels
        ORDER BY j.industry, j.name
    """
    
    GET_ALL_SKILLS = """
        MATCH (s:Skill)
        RETURN s.name as name,
               s.category as category,
               s.description as description
        ORDER BY s.category, s.name
    """
    
    GET_USER_CAREER_GRAPH = """
        MATCH (u:User {id: $user_id})
        OPTIONAL MATCH (u)-[r1:HAS_SKILL]->(s:Skill)
        OPTIONAL MATCH (u)-[r2:ASPIRES_TO]->(j:JobRole)
        OPTIONAL MATCH (u)-[r3:BUILT]->(p:Project)
        OPTIONAL MATCH (p)-[r4:USES]->(ps:Skill)
        RETURN u, 
               collect(DISTINCT s) as skills,
               collect(DISTINCT j) as target_roles,
               collect(DISTINCT p) as projects,
               collect(DISTINCT ps) as project_skills
    """
