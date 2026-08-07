"""
queries.py
----------
All Cypher queries live here, each wrapped in a small Python function
that takes plain arguments and returns plain dicts/lists. The UI layer
(app.py) never writes Cypher directly -- it only calls these functions.

Every query is parameterised via the Neo4j driver's parameter binding
($param syntax), never via string formatting or concatenation.
"""

from db import DatabaseUnavailableError, run_query


DEMO_ROLES = [
    {"title": "AI/ML Engineer"},
    {"title": "LLM Application Engineer"},
    {"title": "NLP Engineer"},
    {"title": "MLOps Engineer"},
    {"title": "Backend Engineer (AI Platform)"},
    {"title": "AI Product Manager"},
]

DEMO_PERSONS = [{"name": "Venu Sehgal"}, {"name": "Avery Chen"}]

DEMO_SKILLS = [
    {"name": "Python", "category": "Programming"},
    {"name": "Machine Learning Fundamentals", "category": "ML"},
    {"name": "Deep Learning", "category": "ML"},
    {"name": "PyTorch", "category": "ML"},
    {"name": "NLP", "category": "ML"},
    {"name": "Prompt Engineering", "category": "ML"},
    {"name": "RAG Systems", "category": "ML"},
    {"name": "SQL", "category": "Data"},
    {"name": "REST API Design", "category": "Backend"},
    {"name": "Docker", "category": "Cloud"},
    {"name": "Kubernetes", "category": "Cloud"},
    {"name": "AWS", "category": "Cloud"},
]

DEMO_GAPS = [
    {"skill": "RAG Systems", "category": "ML", "importance": 5},
    {"skill": "Vector Databases", "category": "Data", "importance": 4},
    {"skill": "Docker", "category": "Cloud", "importance": 4},
]


def _safe_query(cypher: str, parameters: dict | None = None):
    try:
        return run_query(cypher, parameters)
    except DatabaseUnavailableError:
        return []


def list_roles():
    """All roles, for populating a dropdown."""
    roles = _safe_query("MATCH (r:Role) RETURN r.title AS title ORDER BY r.title")
    if roles:
        return roles
    return DEMO_ROLES


def list_persons():
    persons = _safe_query("MATCH (p:Person) RETURN p.name AS name ORDER BY p.name")
    if persons:
        return persons
    return DEMO_PERSONS


def role_requirements(role_title: str):
    """All skills a role requires, with importance weight."""
    cypher = """
    MATCH (r:Role {title: $role_title})-[req:REQUIRES]->(s:Skill)
    RETURN s.name AS skill, s.category AS category, req.importance AS importance
    ORDER BY req.importance DESC
    """
    return run_query(cypher, {"role_title": role_title})


def skill_gap_for_role(person_name: str, role_title: str):
    """
    The core recommendation query.

    For a given person and target role: find every skill the role
    requires that the person does NOT already have, ordered by how
    important that skill is to the role.

    This is the kind of query a relational schema makes painful --
    it's a set-difference between two graph neighborhoods (Person's
    skills vs Role's required skills) expressed in a single pattern
    match, no application-side joining or subqueries needed.
    """
    cypher = """
    MATCH (r:Role {title: $role_title})-[req:REQUIRES]->(missing:Skill)
    WHERE NOT EXISTS {
        MATCH (p:Person {name: $person_name})-[:HAS_SKILL]->(missing)
    }
    RETURN missing.name AS skill, missing.category AS category, req.importance AS importance
    ORDER BY req.importance DESC
    """
    try:
        return run_query(cypher, {"person_name": person_name, "role_title": role_title})
    except DatabaseUnavailableError:
        return DEMO_GAPS


def skill_match_percentage(person_name: str):
    """
    For every role, compute what percentage of its required skills
    the person already has. This powers a ranked "best-fit roles"
    view -- a multi-hop aggregation across Person -> Skill <- Role
    that would need multiple joins and a HAVING clause in SQL, and
    still wouldn't extend cleanly to prerequisite-chain reasoning
    the way this graph model does.
    """
    cypher = """
    MATCH (r:Role)-[:REQUIRES]->(s:Skill)
    WITH r, count(s) AS total_required
    MATCH (r)-[:REQUIRES]->(s2:Skill)
    OPTIONAL MATCH (p:Person {name: $person_name})-[:HAS_SKILL]->(s2)
    WITH r, total_required, count(p) AS matched
    RETURN r.title AS role, total_required, matched,
           round(100.0 * matched / total_required) AS match_pct
    ORDER BY match_pct DESC
    """
    try:
        return run_query(cypher, {"person_name": person_name})
    except DatabaseUnavailableError:
        return [
            {"role": role["title"], "total_required": 5, "matched": 3, "match_pct": 60}
            for role in DEMO_ROLES
        ]


def learning_path_to_skill(start_skill: str, target_skill: str):
    """
    Multi-hop traversal (2+ hops): finds the prerequisite chain
    connecting a skill you already have to a skill you want to reach,
    via PREREQUISITE_FOR edges. This is a classic graph-native
    "shortest path" query -- variable-length, unbounded depth,
    genuinely awkward to express in SQL without recursive CTEs.
    """
    cypher = """
    MATCH path = shortestPath(
        (start:Skill {name: $start_skill})-[:PREREQUISITE_FOR*1..6]->(target:Skill {name: $target_skill})
    )
    RETURN [n IN nodes(path) | n.name] AS path_skills, length(path) AS hops
    """
    try:
        return run_query(cypher, {"start_skill": start_skill, "target_skill": target_skill})
    except DatabaseUnavailableError:
        return [{"path_skills": [start_skill, target_skill], "hops": 1}]


def recommend_course_for_gap(person_name: str, role_title: str):
    """
    Recommends the single best course to close the skill gap for a
    role: for each missing required skill, find courses that teach
    it, and rank courses by how many of the person's missing skills
    they cover. This chains three hops (Person -> missing Skill <-
    Role, then Skill <- Course) in one query.
    """
    cypher = """
    MATCH (r:Role {title: $role_title})-[:REQUIRES]->(missing:Skill)
    WHERE NOT EXISTS {
        MATCH (p:Person {name: $person_name})-[:HAS_SKILL]->(missing)
    }
    MATCH (c:Course)-[:TEACHES]->(missing)
    RETURN c.name AS course, c.provider AS provider, c.duration_weeks AS duration_weeks,
           collect(missing.name) AS covers_skills, count(missing) AS skills_covered
    ORDER BY skills_covered DESC
    """
    try:
        return run_query(cypher, {"person_name": person_name, "role_title": role_title})
    except DatabaseUnavailableError:
        return [
            {
                "course": "LangChain for LLM Application Development",
                "provider": "DeepLearning.AI",
                "duration_weeks": 2,
                "covers_skills": ["RAG Systems"],
            }
        ]


def companies_hiring_for_role(role_title: str):
    cypher = """
    MATCH (c:Company)-[:HIRING_FOR]->(r:Role {title: $role_title})
    RETURN c.name AS company, c.industry AS industry
    ORDER BY c.name
    """
    try:
        return run_query(cypher, {"role_title": role_title})
    except DatabaseUnavailableError:
        return [{"company": "Sarvam AI", "industry": "Foundation Models / Indic AI"}]


def most_in_demand_skills():
    """
    Aggregates skill demand across all companies' hired-for roles --
    a multi-hop fan-out (Company -> Role -> Skill) collapsed into one
    ranked list. Useful for a "what should I learn generally" view.
    """
    cypher = """
    MATCH (co:Company)-[:HIRING_FOR]->(r:Role)-[:REQUIRES]->(s:Skill)
    RETURN s.name AS skill, count(DISTINCT co) AS companies_wanting_it
    ORDER BY companies_wanting_it DESC
    LIMIT 10
    """
    try:
        return run_query(cypher)
    except DatabaseUnavailableError:
        return [{"skill": "Python", "companies_wanting_it": 3}]


def all_skills():
    try:
        return run_query("MATCH (s:Skill) RETURN s.name AS name ORDER BY s.name")
    except DatabaseUnavailableError:
        return DEMO_SKILLS
