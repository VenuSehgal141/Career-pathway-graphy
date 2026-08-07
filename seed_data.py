"""
seed_data.py
------------
Loads realistic seed data into CognoDB for the Career Pathway Graph.

Run this once after creating your CognoDB instance:
    python seed_data.py

Design choice: every write uses MERGE, not CREATE. This makes the
script idempotent -- you can re-run it safely (e.g. after adding a
new skill to this file) without duplicating nodes or relationships.
"""

from db import run_query, close_driver

# ---------------------------------------------------------------------------
# 1. SKILLS
# ---------------------------------------------------------------------------
SKILLS = [
    {"name": "Python", "category": "Programming"},
    {"name": "PyTorch", "category": "ML"},
    {"name": "TensorFlow", "category": "ML"},
    {"name": "LangChain", "category": "ML"},
    {"name": "Prompt Engineering", "category": "ML"},
    {"name": "RAG Systems", "category": "ML"},
    {"name": "Machine Learning Fundamentals", "category": "ML"},
    {"name": "Deep Learning", "category": "ML"},
    {"name": "NLP", "category": "ML"},
    {"name": "SQL", "category": "Data"},
    {"name": "Data Structures & Algorithms", "category": "CS Fundamentals"},
    {"name": "System Design", "category": "Backend"},
    {"name": "REST API Design", "category": "Backend"},
    {"name": "Docker", "category": "Cloud"},
    {"name": "Kubernetes", "category": "Cloud"},
    {"name": "AWS", "category": "Cloud"},
    {"name": "Google Cloud Platform", "category": "Cloud"},
    {"name": "CI/CD", "category": "Cloud"},
    {"name": "Vector Databases", "category": "Data"},
    {"name": "MLOps", "category": "ML"},
]

# ---------------------------------------------------------------------------
# 2. PREREQUISITE CHAINS (Skill -> Skill it unlocks)
#    This is what makes the graph genuinely graph-shaped: prerequisite
#    chains are naturally recursive and painful to query in SQL beyond
#    one or two hops.
# ---------------------------------------------------------------------------
SKILL_PREREQS = [
    ("Python", "PyTorch"),
    ("Python", "TensorFlow"),
    ("Python", "SQL"),
    ("Data Structures & Algorithms", "System Design"),
    ("Machine Learning Fundamentals", "Deep Learning"),
    ("Deep Learning", "PyTorch"),
    ("Deep Learning", "NLP"),
    ("NLP", "LangChain"),
    ("NLP", "Prompt Engineering"),
    ("Prompt Engineering", "RAG Systems"),
    ("LangChain", "RAG Systems"),
    ("RAG Systems", "Vector Databases"),
    ("Docker", "Kubernetes"),
    ("REST API Design", "System Design"),
    ("AWS", "MLOps"),
    ("Docker", "MLOps"),
]

# ---------------------------------------------------------------------------
# 3. ROLES and the skills they require, with an importance weight (1-5)
# ---------------------------------------------------------------------------
ROLES = [
    {"title": "AI/ML Engineer", "seniority": "Mid", "description":
        "Builds and ships ML/LLM-backed features end to end."},
    {"title": "LLM Application Engineer", "seniority": "Mid", "description":
        "Builds applications on top of foundation models: RAG, agents, prompt pipelines."},
    {"title": "NLP Engineer", "seniority": "Mid", "description":
        "Focuses on language understanding and generation systems."},
    {"title": "MLOps Engineer", "seniority": "Mid", "description":
        "Owns deployment, monitoring, and infra for ML systems in production."},
    {"title": "Backend Engineer (AI Platform)", "seniority": "Junior-Mid", "description":
        "Builds the backend services that AI products run on."},
    {"title": "AI Product Manager", "seniority": "Mid", "description":
        "Bridges ML capability and product strategy."},
]

ROLE_REQUIRES = [
    ("AI/ML Engineer", "Python", 5), ("AI/ML Engineer", "Machine Learning Fundamentals", 5),
    ("AI/ML Engineer", "Deep Learning", 4), ("AI/ML Engineer", "PyTorch", 4),
    ("AI/ML Engineer", "System Design", 3), ("AI/ML Engineer", "AWS", 3),

    ("LLM Application Engineer", "Python", 5), ("LLM Application Engineer", "LangChain", 5),
    ("LLM Application Engineer", "Prompt Engineering", 5), ("LLM Application Engineer", "RAG Systems", 5),
    ("LLM Application Engineer", "Vector Databases", 4), ("LLM Application Engineer", "REST API Design", 3),

    ("NLP Engineer", "Python", 5), ("NLP Engineer", "NLP", 5),
    ("NLP Engineer", "Deep Learning", 4), ("NLP Engineer", "PyTorch", 4),
    ("NLP Engineer", "Machine Learning Fundamentals", 4),

    ("MLOps Engineer", "Docker", 5), ("MLOps Engineer", "Kubernetes", 4),
    ("MLOps Engineer", "AWS", 4), ("MLOps Engineer", "CI/CD", 4), ("MLOps Engineer", "MLOps", 5),

    ("Backend Engineer (AI Platform)", "Python", 4), ("Backend Engineer (AI Platform)", "REST API Design", 5),
    ("Backend Engineer (AI Platform)", "SQL", 4), ("Backend Engineer (AI Platform)", "System Design", 4),
    ("Backend Engineer (AI Platform)", "Docker", 3),

    ("AI Product Manager", "Machine Learning Fundamentals", 3), ("AI Product Manager", "Prompt Engineering", 3),
    ("AI Product Manager", "SQL", 2),
]

# ---------------------------------------------------------------------------
# 4. COMPANIES and which roles they hire for
# ---------------------------------------------------------------------------
COMPANIES = [
    {"name": "Sarvam AI", "industry": "Foundation Models / Indic AI"},
    {"name": "Krutrim", "industry": "Foundation Models / Cloud"},
    {"name": "Neysa", "industry": "AI Infra / GPU Cloud"},
    {"name": "Yellow.ai", "industry": "Conversational AI"},
    {"name": "SuperAGI", "industry": "Autonomous AI Agents"},
]

COMPANY_HIRES = [
    ("Sarvam AI", "AI/ML Engineer"), ("Sarvam AI", "NLP Engineer"),
    ("Krutrim", "AI/ML Engineer"), ("Krutrim", "MLOps Engineer"),
    ("Neysa", "MLOps Engineer"), ("Neysa", "Backend Engineer (AI Platform)"),
    ("Yellow.ai", "LLM Application Engineer"), ("Yellow.ai", "NLP Engineer"),
    ("SuperAGI", "LLM Application Engineer"), ("SuperAGI", "AI/ML Engineer"),
]

# ---------------------------------------------------------------------------
# 5. COURSES / CERTIFICATIONS and what skill they teach/validate
# ---------------------------------------------------------------------------
COURSES = [
    {"name": "Deep Learning Specialization", "provider": "Coursera (deeplearning.ai)", "duration_weeks": 16},
    {"name": "LangChain for LLM Application Development", "provider": "DeepLearning.AI", "duration_weeks": 2},
    {"name": "AWS Machine Learning Specialty Prep", "provider": "AWS Skill Builder", "duration_weeks": 6},
    {"name": "Docker & Kubernetes: The Practical Guide", "provider": "Udemy", "duration_weeks": 4},
    {"name": "Vector Databases in Practice", "provider": "Pinecone Learning Center", "duration_weeks": 2},
]
COURSE_TEACHES = [
    ("Deep Learning Specialization", "Deep Learning"),
    ("Deep Learning Specialization", "Machine Learning Fundamentals"),
    ("LangChain for LLM Application Development", "LangChain"),
    ("LangChain for LLM Application Development", "RAG Systems"),
    ("AWS Machine Learning Specialty Prep", "AWS"),
    ("AWS Machine Learning Specialty Prep", "MLOps"),
    ("Docker & Kubernetes: The Practical Guide", "Docker"),
    ("Docker & Kubernetes: The Practical Guide", "Kubernetes"),
    ("Vector Databases in Practice", "Vector Databases"),
]

CERTS = [
    {"name": "AWS Certified Cloud Practitioner", "issuer": "AWS"},
    {"name": "IBM AI Engineering Professional Certificate", "issuer": "IBM"},
    {"name": "Google Cloud Digital Leader", "issuer": "Google Cloud"},
]
CERT_VALIDATES = [
    ("AWS Certified Cloud Practitioner", "AWS"),
    ("IBM AI Engineering Professional Certificate", "Machine Learning Fundamentals"),
    ("IBM AI Engineering Professional Certificate", "Deep Learning"),
    ("Google Cloud Digital Leader", "Google Cloud Platform"),
]

# ---------------------------------------------------------------------------
# 6. PERSON (your own profile -- doubles as a real self-assessment tool)
# ---------------------------------------------------------------------------
PERSON = {"name": "Venu Sehgal"}
PERSON_HAS_SKILL = [
    ("Python", 4), ("Machine Learning Fundamentals", 3), ("Deep Learning", 3),
    ("PyTorch", 2), ("NLP", 3), ("Prompt Engineering", 4), ("RAG Systems", 3),
    ("SQL", 3), ("Data Structures & Algorithms", 3), ("REST API Design", 2),
    ("AWS", 2), ("Google Cloud Platform", 2),
]


def seed():
    print("Seeding skills...")
    for s in SKILLS:
        run_query(
            "MERGE (s:Skill {name: $name}) SET s.category = $category",
            s,
        )

    print("Seeding skill prerequisite chains...")
    for a, b in SKILL_PREREQS:
        run_query(
            """
            MATCH (a:Skill {name: $a}), (b:Skill {name: $b})
            MERGE (a)-[:PREREQUISITE_FOR]->(b)
            """,
            {"a": a, "b": b},
        )

    print("Seeding roles...")
    for r in ROLES:
        run_query(
            """
            MERGE (r:Role {title: $title})
            SET r.seniority = $seniority, r.description = $description
            """,
            r,
        )

    print("Seeding role -> skill requirements...")
    for role, skill, importance in ROLE_REQUIRES:
        run_query(
            """
            MATCH (r:Role {title: $role}), (s:Skill {name: $skill})
            MERGE (r)-[rel:REQUIRES]->(s)
            SET rel.importance = $importance
            """,
            {"role": role, "skill": skill, "importance": importance},
        )

    print("Seeding companies...")
    for c in COMPANIES:
        run_query(
            "MERGE (c:Company {name: $name}) SET c.industry = $industry",
            c,
        )

    print("Seeding company -> role hiring links...")
    for company, role in COMPANY_HIRES:
        run_query(
            """
            MATCH (c:Company {name: $company}), (r:Role {title: $role})
            MERGE (c)-[:HIRING_FOR]->(r)
            """,
            {"company": company, "role": role},
        )

    print("Seeding courses...")
    for c in COURSES:
        run_query(
            """
            MERGE (c:Course {name: $name})
            SET c.provider = $provider, c.duration_weeks = $duration_weeks
            """,
            c,
        )

    print("Seeding course -> skill links...")
    for course, skill in COURSE_TEACHES:
        run_query(
            """
            MATCH (c:Course {name: $course}), (s:Skill {name: $skill})
            MERGE (c)-[:TEACHES]->(s)
            """,
            {"course": course, "skill": skill},
        )

    print("Seeding certifications...")
    for c in CERTS:
        run_query(
            "MERGE (c:Certification {name: $name}) SET c.issuer = $issuer",
            c,
        )

    print("Seeding certification -> skill links...")
    for cert, skill in CERT_VALIDATES:
        run_query(
            """
            MATCH (c:Certification {name: $cert}), (s:Skill {name: $skill})
            MERGE (c)-[:VALIDATES]->(s)
            """,
            {"cert": cert, "skill": skill},
        )

    print("Seeding person node...")
    run_query("MERGE (p:Person {name: $name})", PERSON)

    print("Seeding person -> skill links...")
    for skill, proficiency in PERSON_HAS_SKILL:
        run_query(
            """
            MATCH (p:Person {name: $person}), (s:Skill {name: $skill})
            MERGE (p)-[rel:HAS_SKILL]->(s)
            SET rel.proficiency = $proficiency
            """,
            {"person": PERSON["name"], "skill": skill, "proficiency": proficiency},
        )

    print("Done. Seed data loaded into CognoDB.")


if __name__ == "__main__":
    seed()
    close_driver()
