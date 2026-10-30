import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from scenarios import SCENARIOS
from requirements_agent import generate

st.set_page_config(page_title="Requirements Workspace", page_icon="📝", layout="wide")

st.title("📝 Requirements Workspace")
st.caption("Pick a real claims-ops scenario, or describe your own business ask.")

tab1, tab2 = st.tabs(["📚 Scenario Library", "✍️ Custom Ask"])

with tab1:
    st.markdown("Four real business problems, each already run through the full BA pipeline.")
    scenario_cols = st.columns(2)
    keys = list(SCENARIOS.keys())
    for i, key in enumerate(keys):
        sc = SCENARIOS[key]
        with scenario_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{sc['title']}**")
                st.caption(sc["ask"])
                if st.button("Open this requirement", key=f"open_{key}", use_container_width=True):
                    st.session_state["active_scenario"] = {**sc, "generation_mode": "scenario_library"}
                    st.session_state["active_scenario_key"] = key
                    st.toast(f"Loaded: {sc['title']}", icon="✅")

with tab2:
    st.markdown("Type a business problem the way a stakeholder would actually say it.")
    custom_ask = st.text_area(
        "Business ask",
        placeholder="e.g. 'Our pharmacy claims are taking forever to process and providers are complaining — what's going on?'",
        height=90,
    )

    with st.expander("⚙️ Optional: use a live LLM (bring your own API key)"):
        st.caption(
            "Without a key, requirements are generated with a transparent rule-based "
            "extractor (shown in the output). With an OpenAI-compatible key, a real "
            "model generates the full package live."
        )
        api_key = st.text_input("API key", type="password", placeholder="sk-...")
        base_url = st.text_input("Base URL (optional)", placeholder="https://api.openai.com/v1")
        model = st.text_input("Model (optional)", placeholder="gpt-4o-mini")

    if st.button("Generate requirements", type="primary", disabled=not custom_ask.strip()):
        with st.spinner("Generating BRD, FRD, user stories, and RAID log..."):
            result = generate(custom_ask, api_key=api_key, base_url=base_url, model=model)
        st.session_state["active_scenario"] = result
        st.session_state["active_scenario_key"] = "custom"
        if result.get("generation_mode") == "live":
            st.success("Generated live via your API key.")
        else:
            if result.get("live_error"):
                st.warning(f"Live generation failed ({result['live_error']}); used the rule-based fallback instead.")
            else:
                st.info("Generated with the rule-based fallback (no API key supplied).")

st.divider()

scenario = st.session_state.get("active_scenario")
if not scenario:
    st.info("Select a scenario above, or generate a custom ask, to see the full requirements package here.")
    st.stop()

st.header(f"📋 {scenario['title']}")
mode = scenario.get("generation_mode", "scenario_library")
mode_label = {"scenario_library": "Pre-built scenario", "live": "Generated live via LLM", "fallback": "Generated via rule-based fallback"}
st.caption(f"**Business ask:** {scenario['ask']}  ·  _{mode_label.get(mode, mode)}_")

brd, frd, stories, raid = st.tabs(["BRD", "FRD", "User Stories", "RAID Log"])

with brd:
    b = scenario["brd"]
    st.subheader("Objective")
    st.write(b["objective"])
    st.subheader("Background")
    st.write(b["background"])
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("In Scope")
        for item in b["in_scope"]:
            st.markdown(f"- {item}")
    with c2:
        st.subheader("Out of Scope")
        for item in b["out_of_scope"]:
            st.markdown(f"- {item}")
    st.subheader("Success Metrics")
    for item in b["success_metrics"]:
        st.markdown(f"- {item}")
    st.subheader("Stakeholders")
    st.write(", ".join(b["stakeholders"]))

with frd:
    f = scenario["frd"]
    st.subheader("Functional Requirements")
    for req in f["functional"]:
        st.markdown(f"**{req['id']}** — {req['text']}")
    st.subheader("Non-Functional Requirements")
    for item in f["non_functional"]:
        st.markdown(f"- {item}")
    st.subheader("Data Requirements")
    for item in f["data_requirements"]:
        st.markdown(f"- `{item}`")

with stories:
    for s in scenario["user_stories"]:
        with st.container(border=True):
            st.markdown(f"**{s['id']}**: {s['story']}")
            st.caption("Acceptance Criteria (Gherkin)")
            for kw, text in s["ac"]:
                st.markdown(f"&nbsp;&nbsp;**{kw}** {text}", unsafe_allow_html=True)

with raid:
    import pandas as pd
    raid_df = pd.DataFrame(scenario["raid"])
    raid_df.columns = [c.title() for c in raid_df.columns]
    st.dataframe(raid_df, use_container_width=True, hide_index=True)

st.success("✅ Requirements ready. Continue to **Data Validation** in the sidebar to run these against the real database.")
