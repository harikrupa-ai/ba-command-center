import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from sql_validator import run_metric
from dashboard_builder import build_chart

st.set_page_config(page_title="Live Dashboard", page_icon="📊", layout="wide")

st.title("📊 Live Dashboard")
st.caption("Auto-built from the requirement's validated metrics. Not a mockup — these charts are driven by the SQL results from the Data Validation step.")

scenario = st.session_state.get("active_scenario")
if not scenario:
    st.warning("No requirement loaded yet. Go to **Requirements Workspace** first.")
    st.stop()

st.header(scenario["title"])

metrics = scenario.get("metrics", [])
if not metrics:
    st.warning("This requirement has no metrics defined.")
    st.stop()

validated = st.session_state.get("validated_data", {})

cols = st.columns(2) if len(metrics) > 1 else [st.container()]
for i, m in enumerate(metrics):
    metric_key = m.get("metric_key")
    df = validated.get(metric_key)
    if df is None:
        df = run_metric(metric_key)
    fig = build_chart(metric_key, df, m["name"], m.get("chart_type", "bar"))
    target_col = cols[i % len(cols)] if len(metrics) > 1 else cols[0]
    with target_col:
        st.plotly_chart(fig, use_container_width=True)

st.success("✅ Dashboard generated. Continue to **Traceability Matrix** to see the full ask-to-chart chain.")
