"""
queries.py
----------
All Cypher queries live here, each wrapped in a small Python function
that takes plain arguments and returns plain dicts/lists. The UI layer
(app.py) never writes Cypher directly -- it only calls these functions.

Every query is parameterised via the Neo4j driver's parameter binding
($param syntax), never via string formatting or concatenation.
"""

from db import run_query


def list_roles():
    """All roles, for populating a dropdown."""
    return run_query("MATCH (r:Role) RETURN r.title AS title ORDER BY r.title")


def list_persons():
    return run_query("MATCH (p:Person) RETURN p.name AS name ORDER BY p.name")


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
    return run_query(cypher, {"person_name": person_name, "role_title": role_title})


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
    return run_query(cypher, {"person_name": person_name})


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
    return run_query(cypher, {"start_skill": start_skill, "target_skill": target_skill})


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
    return run_query(cypher, {"person_name": person_name, "role_title": role_title})


def companies_hiring_for_role(role_title: str):
    cypher = """
    MATCH (c:Company)-[:HIRING_FOR]->(r:Role {title: $role_title})
    RETURN c.name AS company, c.industry AS industry
    ORDER BY c.name
    """
    return run_query(cypher, {"role_title": role_title})


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
    return run_query(cypher)


def all_skills():
    return run_query("MATCH (s:Skill) RETURN s.name AS name ORDER BY s.name")
