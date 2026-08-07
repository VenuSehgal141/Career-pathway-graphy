from graphviz import Digraph

dot = Digraph(comment="Career Pathway Graph Data Model", format="png")
dot.attr(rankdir="LR", bgcolor="white", fontname="Helvetica")
dot.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fontsize="12")

colors = {
    "Person": "#4F8BF9",
    "Skill": "#34C759",
    "Role": "#FF9500",
    "Company": "#AF52DE",
    "Course": "#FF3B30",
    "Certification": "#00C7BE",
}

for label, color in colors.items():
    dot.node(label, label, fillcolor=color, fontcolor="white")

dot.edge("Person", "Skill", label="HAS_SKILL {proficiency}")
dot.edge("Role", "Skill", label="REQUIRES {importance}")
dot.edge("Skill", "Skill", label="PREREQUISITE_FOR")
dot.edge("Company", "Role", label="HIRING_FOR")
dot.edge("Course", "Skill", label="TEACHES")
dot.edge("Certification", "Skill", label="VALIDATES")

dot.render("/home/claude/career-graph/docs/data_model", cleanup=True)
print("done")
