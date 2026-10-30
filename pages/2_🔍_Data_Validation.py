import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from sql_validator import run_metric, get_sql_text, data_quality_report

st.set_page_config(page_title="Data Validation", page_icon="🔍", layout="wide")

st.title("🔍 Data Validation Console")
st.caption("Every requirement's metric is run as a real SQL query against a 120,000-row relational claims database — not a mockup.")

scenario = st.session_state.get("active_scenario")
if not scenario:
    st.warning("No requirement loaded yet. Go to **Requirements Workspace** first.")
    st.stop()

st.info(f"Validating metrics for: **{scenario['title'].strip()}**")

metrics = scenario.get("metrics", [])
if not metrics:
    st.warning("This requirement has no metrics defined.")
    st.stop()

for m in metrics:
    with st.container(border=True):
        st.subheader(f"{m['id']} — {m['name']}")
        metric_key = m.get("metric_key")

        df = run_metric(metric_key)
        st.session_state.setdefault("validated_data", {})[metric_key] = df

        col_sql, col_dq = st.columns([1.3, 1])
        with col_sql:
            st.markdown("**SQL executed against `claims_ops.db`:**")
            st.code(get_sql_text(metric_key), language="sql")
        with col_dq:
            st.markdown("**Data quality checks:**")
            checks = data_quality_report(df)
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
            for c in checks:
                st.markdown(f"{icon.get(c['status'], '•')} **{c['check']}:** {c['result']}")

        with st.expander(f"View query result ({len(df):,} rows)"):
            st.dataframe(df, use_container_width=True, hide_index=True)

st.success("✅ All metrics validated against the live database. Continue to **Live Dashboard** to see them visualized.")
