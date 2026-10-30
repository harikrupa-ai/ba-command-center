import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

st.set_page_config(
    page_title="BA Command Center",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root { --teal:#2E6F6E; --accent:#E8955D; --ink:#1A2B2A; }
.hero {
    background: linear-gradient(135deg, #1A2B2A 0%, #2E6F6E 100%);
    padding: 2.5rem 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: 2.1rem; margin-bottom: 0.4rem; }
.hero p { font-size: 1.05rem; opacity: 0.92; max-width: 760px; line-height: 1.5; }
.pill {
    display:inline-block; background: rgba(255,255,255,0.14); color:white;
    padding: 4px 12px; border-radius: 999px; font-size: 0.82rem; margin-right: 8px;
    margin-bottom: 6px; border: 1px solid rgba(255,255,255,0.25);
}
.stage-card {
    border: 1px solid #e3e8e7; border-radius: 12px; padding: 1.1rem 1.3rem;
    background: white; height: 100%;
}
.stage-num {
    display:inline-flex; align-items:center; justify-content:center;
    width: 28px; height: 28px; border-radius: 50%; background: var(--teal);
    color: white; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.5rem;
}
.stage-title { font-weight: 700; font-size: 1.02rem; margin-bottom: 0.3rem; color: var(--ink); }
.stage-desc { font-size: 0.88rem; color: #555; line-height: 1.45; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <span class="pill">🧭 BA Command Center</span>
  <span class="pill">Requirements → Data → Decision</span>
  <h1>From a plain-English business ask to a validated, live dashboard —
  with full traceability, in one pipeline.</h1>
  <p>This is the tool a Business Analyst would build for themselves: describe a business
  problem the way a stakeholder actually says it, and watch it move through requirements
  (BRD/FRD/user stories), real SQL validation against a 120K-row claims database, an
  auto-generated dashboard, and a full requirements traceability matrix — the artifact
  every BA produces by hand, generated and linked automatically here.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### How it works")
cols = st.columns(5)
stages = [
    ("1", "Business Ask", "A stakeholder describes a problem in plain English — no ticket template, no jargon required."),
    ("2", "Requirements", "A BRD, FRD, user stories with Gherkin acceptance criteria, and a RAID log are generated."),
    ("3", "Data Validation", "Each requirement's metric is run as real SQL against a 120,000-row claims database, with data-quality checks."),
    ("4", "Live Dashboard", "Validated metrics render as live charts — not mockups, the actual query results."),
    ("5", "Traceability", "Every requirement is linked end-to-end: ask → story → SQL → chart, the matrix every audit asks for."),
]
for col, (num, title, desc) in zip(cols, stages):
    with col:
        st.markdown(f"""
        <div class="stage-card">
          <div class="stage-num">{num}</div>
          <div class="stage-title">{title}</div>
          <div class="stage-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")
st.info(
    "👉 Start in **Requirements Workspace** in the sidebar — pick one of four real "
    "claims-operations scenarios, or type your own business ask.",
    icon="🧭",
)

st.markdown("### Why this exists")
st.markdown("""
Most portfolio dashboards start from a dataset. This starts from a **business problem**,
because that's the actual job: a Business Analyst's output isn't a chart — it's a
requirement that's traceable, validated against real data, and defensible in a
stakeholder review.

This tool runs the full chain itself:
- **Requirements** are structured (BRD, FRD, Gherkin-style acceptance criteria, RAID log) — not a paragraph of prose.
- **Data validation** executes real SQL against a normalized, 120,000-row relational database
  (claims, providers, payers, denials) — not a static CSV.
- **The dashboard** is generated from the requirement's declared metrics, so what's on screen
  is provably tied to what was asked for.
- **The traceability matrix** is the artifact every audit, every stakeholder review, and every
  BA interview question ("walk me through a requirement you delivered") actually needs.
""")

st.caption(
    "Built by Hari Krupa Cheguri — Business Analyst with 5+ years across health insurance, "
    "banking, and enterprise analytics. [LinkedIn](https://www.linkedin.com/in/krupa-ch-57308220b/) · "
    "[GitHub](https://github.com/harikrupa-ai)"
)
