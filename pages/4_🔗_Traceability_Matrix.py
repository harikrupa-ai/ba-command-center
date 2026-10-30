import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from traceability import build_matrix

st.set_page_config(page_title="Traceability Matrix", page_icon="🔗", layout="wide")

st.title("🔗 Requirements Traceability Matrix")
st.caption(
    "The artifact every stakeholder review and audit asks for: proof that what's on the "
    "dashboard actually traces back to the requirement that was asked for."
)

scenario = st.session_state.get("active_scenario")
if not scenario:
    st.warning("No requirement loaded yet. Go to **Requirements Workspace** first.")
    st.stop()

matrix_df = build_matrix(scenario)
st.dataframe(matrix_df, use_container_width=True, hide_index=True)

st.markdown("### Chain of custody")
st.markdown(f"""
```
Business Ask
  └── "{scenario['ask'][:90]}{'...' if len(scenario['ask']) > 90 else ''}"
        └── BRD / FRD  (Requirements Workspace)
              └── {len(scenario.get('user_stories', []))} User Stories with Gherkin Acceptance Criteria
                    └── {len(scenario.get('metrics', []))} Metrics validated as real SQL  (Data Validation)
                          └── {len(scenario.get('metrics', []))} Charts rendered from query results  (Live Dashboard)
```
""")

st.info(
    "This is the end-to-end chain: every chart on the Live Dashboard page can be traced "
    "back through a validated SQL query, a user story with acceptance criteria, to the "
    "original plain-English business ask.",
    icon="✅",
)

csv = matrix_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download traceability matrix (CSV)", csv, "traceability_matrix.csv", "text/csv")
