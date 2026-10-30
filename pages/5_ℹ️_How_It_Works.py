import streamlit as st

st.set_page_config(page_title="How It Works", page_icon="ℹ️", layout="wide")

st.title("ℹ️ How This Was Built")

st.markdown("""
### Architecture

```
  Business Ask (plain English)
         │
         ▼
  ┌─────────────────────┐        Scenario Library: 4 fully pre-built
  │ Requirements Agent   │  ───   BA packages, always available instantly
  │ (core/requirements_  │
  │  agent.py)           │        Custom Ask: live LLM call if you supply
  └─────────┬────────────┘        your own API key, else a transparent
            │                      rule-based extractor — never just errors
            ▼
  BRD · FRD · User Stories (Gherkin AC) · RAID Log
            │
            ▼
  ┌─────────────────────┐
  │ SQL Validator         │  ───   Real parameterized SQL, run against a
  │ (core/sql_validator.  │        normalized 120,000-row SQLite database
  │  py)                  │        (claims, providers, payers, denials)
  └─────────┬────────────┘        + null-rate / outlier data-quality checks
            │
            ▼
  ┌─────────────────────┐
  │ Dashboard Builder     │  ───   Plotly charts generated from the
  │ (core/dashboard_      │        requirement's declared metric list —
  │  builder.py)          │        not hand-wired per scenario
  └─────────┬────────────┘
            │
            ▼
  ┌─────────────────────┐
  │ Traceability Matrix   │  ───   Requirement → Story → SQL Metric →
  │ (core/traceability.   │        Dashboard Widget → Status
  │  py)                  │
  └─────────────────────┘
```

### Why it's designed this way

A lot of "AI business analyst" portfolio projects are a chat window wrapped around
an LLM. This one is built the way the actual BA deliverable chain works:

- **The database is real and relational** — 120,000 claims, 180 providers, 8 payers,
  and a separate denials table with foreign keys, not a flat CSV. Every chart on the
  Live Dashboard page is the output of an actual `JOIN`/`GROUP BY` query, visible in
  full on the Data Validation page.
- **The requirements are structured artifacts**, not a paragraph of AI prose: a BRD
  with explicit in/out of scope, an FRD with numbered functional requirements, user
  stories with Gherkin-style Given/When/Then acceptance criteria, and a RAID log.
  These are the documents a BA is actually evaluated on.
- **The Scenario Library ships four fully-worked requirements packages** so the demo
  is always instant and reliable — no waiting on an API, no risk of a bad LLM response
  breaking the experience for a recruiter clicking through it.
- **Custom asks support a real LLM call** if you bring your own OpenAI-compatible key
  (OpenAI, or any compatible endpoint), so the "AI agent" architecture is genuinely
  live, not just decorative. Without a key, a transparent rule-based extractor still
  produces a structurally complete package — the tool never just shows an error.

### Stack

Python · Streamlit · SQLite · Pandas · Plotly · OpenAI SDK (optional, bring-your-own-key)

### About

Built by **Hari Krupa Cheguri** — Business Analyst with 5+ years across health insurance,
banking, and enterprise analytics.
[LinkedIn](https://www.linkedin.com/in/krupa-ch-57308220b/) ·
[GitHub](https://github.com/harikrupa-ai)
""")
