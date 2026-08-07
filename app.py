"""
app.py
------
Streamlit UI for the Career Pathway Graph.

This file only handles presentation: layout, loading/empty/error
states, and passing user selections into the functions in queries.py.
It never contains Cypher itself.
"""

import streamlit as st
from db import DatabaseUnavailableError
import queries as q

st.set_page_config(page_title="Career Pathway Graph", page_icon="🧭", layout="wide")

st.title("🧭 Career Pathway Graph")
st.caption(
    "Explore how skills, roles, companies, and courses connect — "
    "backed by CognoDB when available, with a polished fallback demo when it is not."
)

# ---------------------------------------------------------------------------
# Try the database first, but fall back to a built-in demo dataset if the
# connection is unavailable. The UI should still render in either mode.
# ---------------------------------------------------------------------------
try:
    roles = q.list_roles()
    persons = q.list_persons()
except DatabaseUnavailableError as e:
    st.info(
        "Using the built-in demo dataset because the CognoDB connection is unavailable. "
        f"Details: {e}"
    )
    roles = q.list_roles()
    persons = q.list_persons()

if not roles or not persons:
    st.warning(
        "No data is currently available. "
        "Run `python seed_data.py` once you have a live CognoDB instance configured."
    )
    st.stop()

role_titles = [r["title"] for r in roles]
person_names = [p["name"] for p in persons]

tab1, tab2, tab3 = st.tabs(["🎯 Skill Gap Explorer", "🏢 Roles & Companies", "📈 Market Demand"])

# ---------------------------------------------------------------------------
# TAB 1: Skill gap explorer -- the core feature
# ---------------------------------------------------------------------------
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        person = st.selectbox("Who are you?", person_names)
    with col2:
        target_role = st.selectbox("Target role", role_titles)

    st.divider()

    st.subheader(f"Fit for every role, ranked")
    fit_data = q.skill_match_percentage(person)
    if fit_data:
        display_rows = [
            {
                "Role": row["role"],
                "Skills Required": row["total_required"],
                "Skills You Have": row["matched"],
                "Match %": row["match_pct"],
            }
            for row in fit_data
        ]
        st.dataframe(display_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No role-fit data available yet.")

    st.divider()

    st.subheader(f"Skill gap: {person} → {target_role}")
    gaps = q.skill_gap_for_role(person, target_role)
    if not gaps:
        st.success(f"🎉 {person} already has every skill required for {target_role}!")
    else:
        gap_rows = [
            {
                "Missing Skill": row["skill"],
                "Category": row["category"],
                "Importance (1-5)": row["importance"],
            }
            for row in gaps
        ]
        st.dataframe(gap_rows, use_container_width=True, hide_index=True)

        st.subheader("📚 Recommended courses to close this gap")
        recs = q.recommend_course_for_gap(person, target_role)
        if recs:
            for r in recs:
                with st.container(border=True):
                    st.markdown(f"**{r['course']}** — *{r['provider']}* ({r['duration_weeks']} weeks)")
                    st.caption(f"Covers: {', '.join(r['covers_skills'])}")
        else:
            st.info("No matching courses found for the missing skills.")

    st.divider()
    st.subheader("🔗 Learning path between two skills")
    st.caption("Multi-hop traversal along prerequisite chains.")
    all_skill_names = [s["name"] for s in q.all_skills()]
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        start_skill = st.selectbox("I know...", all_skill_names, index=all_skill_names.index("Python") if "Python" in all_skill_names else 0)
    with pcol2:
        end_skill = st.selectbox("I want to reach...", all_skill_names, index=all_skill_names.index("RAG Systems") if "RAG Systems" in all_skill_names else 0)

    if st.button("Find path"):
        path_result = q.learning_path_to_skill(start_skill, end_skill)
        if path_result and path_result[0]["path_skills"]:
            st.success(" → ".join(path_result[0]["path_skills"]) + f"  ({path_result[0]['hops']} hops)")
        else:
            st.warning("No prerequisite path found between those two skills.")

# ---------------------------------------------------------------------------
# TAB 2: Roles & companies
# ---------------------------------------------------------------------------
with tab2:
    role_for_companies = st.selectbox("Explore a role", role_titles, key="role_tab2")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Required skills")
        reqs = q.role_requirements(role_for_companies)
        if reqs:
            req_rows = [
                {
                    "Skill": row["skill"],
                    "Category": row["category"],
                    "Importance": row["importance"],
                }
                for row in reqs
            ]
            st.dataframe(req_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No requirements recorded for this role.")

    with col2:
        st.subheader("Companies hiring for this role")
        companies = q.companies_hiring_for_role(role_for_companies)
        if companies:
            for c in companies:
                st.markdown(f"- **{c['company']}** ({c['industry']})")
        else:
            st.info("No companies currently linked to this role in the dataset.")

# ---------------------------------------------------------------------------
# TAB 3: Market demand
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Most in-demand skills across all hiring companies")
    demand = q.most_in_demand_skills()
    if demand:
        demand_rows = [
            {"Skill": row["skill"], "Companies wanting it": row["companies_wanting_it"]}
            for row in demand
        ]
        st.dataframe(demand_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No demand data available yet.")

st.divider()
st.caption("Data layer: CognoDB (graph database) · Driver: official Neo4j Python driver · UI: Streamlit")
