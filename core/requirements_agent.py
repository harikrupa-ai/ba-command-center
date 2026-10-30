"""
Requirements Agent: turns a plain-English business ask into a structured BA
deliverable package (BRD, FRD, user stories, RAID log, metric list).

Two modes:
  - Scenario Library: pre-built, fully-worked packages (see scenarios.py) —
    always available, no API key needed, used for the four shipped demo asks.
  - Custom ask: the visitor types their own business ask.
      * If they supply their own OpenAI-compatible API key, this calls a real
        LLM to generate the package live.
      * If no key is supplied, a transparent rule-based generator produces a
        structurally complete (if less nuanced) package from keyword/entity
        extraction, so the tool never just errors out.
"""
import json
import re

CLAIM_TYPE_WORDS = ["outpatient", "inpatient", "pharmacy", "emergency", "preventive", "behavioral health"]
PAYER_WORDS = ["cigna", "aetna", "unitedhealthcare", "united healthcare", "bcbs", "humana", "kaiser", "anthem", "molina"]
METRIC_WORDS = {
    "denial": "denial_rate_trend",
    "deny": "denial_rate_trend",
    "payment accuracy": "payment_accuracy_by_payer",
    "paid": "payment_accuracy_by_payer",
    "turnaround": "tat_vs_baseline",
    "processing time": "tat_vs_baseline",
    "tat": "tat_vs_baseline",
    "provider": "provider_vs_peer_denial",
}


def _extract_focus(ask: str):
    ask_l = ask.lower()
    claim_type = next((w for w in CLAIM_TYPE_WORDS if w in ask_l), None)
    payer = next((w for w in PAYER_WORDS if w in ask_l), None)
    metric_key = "denial_rate_trend"
    for kw, key in METRIC_WORDS.items():
        if kw in ask_l:
            metric_key = key
            break
    return claim_type, payer, metric_key


def generate_fallback(ask: str) -> dict:
    """Rule-based package builder — no API key required. Transparent heuristic,
    not a disguised canned answer: the output genuinely reflects the input ask."""
    claim_type, payer, metric_key = _extract_focus(ask)
    focus_phrase = claim_type.title() if claim_type else "the affected claim segment"
    payer_phrase = f" for {payer.title()}" if payer else ""

    focus_label = " ".join(x for x in [claim_type.title() if claim_type else None, payer.title() if payer else None] if x)
    if focus_label:
        title = f"{focus_label} — Requirement from Business Ask"
    else:
        words = ask.strip().rstrip(".").split()
        snippet = " ".join(words[:8])
        title = f"Requirement: {snippet}{'…' if len(words) > 8 else ''}"

    brd = {
        "objective": (
            f"Investigate and report on the issue described — \"{ask.strip()}\" — "
            f"with reporting broken out for {focus_phrase}{payer_phrase}, and define "
            f"measurable success criteria for resolution."
        ),
        "background": (
            f"Stakeholders raised the following business problem: \"{ask.strip()}\". "
            f"No structured requirement currently exists for this ask; this package "
            f"was generated from the raw request using keyword-based analysis "
            f"(no live LLM key was supplied for this session)."
        ),
        "in_scope": [
            f"Reporting and root-cause breakdown for {focus_phrase}{payer_phrase}",
            "Trend view over the available date range",
            "Comparison against the relevant book-of-business baseline",
        ],
        "out_of_scope": [
            "Process or workflow changes resulting from findings (tracked separately)",
            "Any system outside the claims_ops database used by this tool",
        ],
        "success_metrics": [
            "Report available with provider/payer-level granularity",
            "Primary driver(s) of the issue identified and quantified",
        ],
        "stakeholders": ["Claims Operations", "Finance", "Requesting stakeholder"],
    }

    frd = {
        "functional": [
            {"id": "FR-1", "text": f"System shall report the relevant metric filtered to {focus_phrase}{payer_phrase}."},
            {"id": "FR-2", "text": "System shall display a trend of the metric over the available date range."},
            {"id": "FR-3", "text": "System shall compare the filtered metric against the overall baseline for context."},
        ],
        "non_functional": [
            "Report must reflect data as of the most recent daily refresh",
        ],
        "data_requirements": [
            "claims table (claim_type, payer_id, provider_id, status, billed_amount, paid_amount, dates)",
            "denials table" if metric_key == "denial_rate_trend" else "providers/payers reference tables",
        ],
    }

    user_stories = [
        {
            "id": "US-1",
            "story": f"As a stakeholder who raised this request, I want to see {focus_phrase} broken out clearly, so that I can understand the scope of the issue.",
            "ac": [
                ("Given", "the Live Dashboard is open"),
                ("When", f"I filter to {focus_phrase}"),
                ("Then", "the relevant metric and trend are displayed"),
            ],
        },
        {
            "id": "US-2",
            "story": "As a BA, I want this requirement traced from ask to dashboard, so that I can show stakeholders exactly how their question was answered.",
            "ac": [
                ("Given", "this requirement has been processed"),
                ("When", "I open the Traceability Matrix"),
                ("Then", "I see this requirement linked to its user story, SQL metric, and dashboard widget"),
            ],
        },
    ]

    raid = [
        {"type": "Assumption", "text": "The claims_ops database schema contains the fields needed to answer this ask directly.", "owner": "BA"},
        {"type": "Risk", "text": "This package was generated via keyword extraction rather than a live LLM call — nuance in the original ask may be lost; review before treating as final.", "owner": "BA"},
    ]

    metrics = [
        {"id": "M-1", "name": f"{focus_phrase} — Requested Metric", "metric_key": metric_key, "chart_type": "bar"},
    ]

    return {
        "title": title,
        "ask": ask,
        "brd": brd,
        "frd": frd,
        "user_stories": user_stories,
        "raid": raid,
        "metrics": metrics,
        "generation_mode": "fallback",
    }


SYSTEM_PROMPT = """You are a senior Business Analyst. Given a plain-English business ask about a \
healthcare claims operations business, produce a JSON object with this exact shape:
{
  "title": "short title",
  "brd": {"objective": "...", "background": "...", "in_scope": ["..."], "out_of_scope": ["..."], \
"success_metrics": ["..."], "stakeholders": ["..."]},
  "frd": {"functional": [{"id":"FR-1","text":"..."}], "non_functional": ["..."], "data_requirements": ["..."]},
  "user_stories": [{"id":"US-1","story":"As a ... I want ... so that ...", \
"ac":[["Given","..."],["When","..."],["Then","..."]]}],
  "raid": [{"type":"Risk|Assumption|Issue|Dependency","text":"...","owner":"..."}],
  "metrics": [{"id":"M-1","name":"...","metric_key":"denial_rate_trend|payment_accuracy_by_payer|tat_vs_baseline|provider_vs_peer_denial","chart_type":"bar|line|table"}]
}
The claims_ops database has tables: claims(claim_id, provider_id, payer_id, claim_type, region, \
billed_amount, paid_amount, status[Paid/Denied/Pending], submitted_date, processed_date, processing_days), \
denials(denial_id, claim_id, denial_reason, denial_date), providers(provider_id, provider_name, specialty, \
region), payers(payer_id, payer_name, payer_type). Pick metric_key only from the allowed list above. \
Return ONLY the JSON object, no prose, no markdown fences."""


def generate_live(ask: str, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini") -> dict:
    """Calls a real OpenAI-compatible endpoint with the visitor's own key.
    Raises on any failure — caller should catch and fall back."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ask},
        ],
        temperature=0.3,
    )
    content = resp.choices[0].message.content.strip()
    content = re.sub(r"^```(json)?|```$", "", content, flags=re.MULTILINE).strip()
    data = json.loads(content)
    data["ask"] = ask
    data["generation_mode"] = "live"
    return data


def generate(ask: str, api_key: str = "", base_url: str = "", model: str = "") -> dict:
    """Entry point used by the app: tries live mode if a key was supplied,
    otherwise uses the transparent fallback. Never raises to the caller."""
    if api_key:
        try:
            return generate_live(ask, api_key, base_url or "https://api.openai.com/v1", model or "gpt-4o-mini")
        except Exception as e:
            fb = generate_fallback(ask)
            fb["live_error"] = str(e)
            return fb
    return generate_fallback(ask)
