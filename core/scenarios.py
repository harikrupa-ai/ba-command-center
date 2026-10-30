"""
Scenario library: fully-worked business requirements packages for the claims-ops
domain. Each scenario is a complete, realistic BA deliverable set — BRD, FRD,
user stories with Gherkin acceptance criteria, and a RAID log — plus a list of
metrics that drive the SQL validation and dashboard layers downstream.

These ship pre-built so the live demo always renders instantly and reliably.
"Custom ask" mode (see requirements_agent.py) generates a comparable package
live, either via a user-supplied LLM key or a rule-based fallback.
"""

SCENARIOS = {
    "denial_reduction": {
        "title": "Reduce Behavioral Health Claim Denials",
        "ask": (
            "Our Behavioral Health claims are denying at a much higher rate than "
            "every other claim type, and finance wants to know why and what we're "
            "going to do about it."
        ),
        "brd": {
            "objective": (
                "Identify the primary drivers of the elevated Behavioral Health "
                "denial rate and define a reporting + process solution that brings "
                "it in line with the book-of-business average within two quarters."
            ),
            "background": (
                "Behavioral Health claims currently deny at roughly 13.5%, nearly "
                "double the 7.1% average across all other claim types. Finance "
                "flagged this during the monthly reimbursement review; operations "
                "has no standing report that isolates denial reasons by claim type "
                "and payer, so root cause is currently anecdotal."
            ),
            "in_scope": [
                "Denial-reason breakdown for Behavioral Health claims, by payer and provider",
                "Trend view of Behavioral Health denial rate over time",
                "Comparison against all-claim-type baseline denial rate",
                "A recurring (monthly) reporting artifact for Finance and Claims Ops leadership",
            ],
            "out_of_scope": [
                "Automated appeals/resubmission workflow (tracked as a dependency, not in this phase)",
                "Payer contract renegotiation (business decision outside BA/reporting scope)",
            ],
            "success_metrics": [
                "Behavioral Health denial rate reported with <24hr data latency",
                "Top 3 denial reasons identified and quantified by dollar impact",
                "Denial rate reduced from 13.5% toward the 9% target within 2 quarters",
            ],
            "stakeholders": [
                "VP, Claims Operations (Executive Sponsor)",
                "Finance — Reimbursement Reporting",
                "Behavioral Health Provider Network Managers",
                "Claims Processing Team Leads",
            ],
        },
        "frd": {
            "functional": [
                {"id": "FR-1", "text": "System shall calculate denial rate = denied claims / total claims, filterable by claim type, payer, provider, and date range."},
                {"id": "FR-2", "text": "System shall break down denials by denial reason for any selected claim-type/payer combination."},
                {"id": "FR-3", "text": "System shall display a month-over-month trend line of Behavioral Health denial rate against the all-claim-type baseline."},
                {"id": "FR-4", "text": "System shall rank denial reasons by total billed-dollar impact, not just claim count, so Finance can prioritize by cost."},
                {"id": "FR-5", "text": "System shall support drill-down from payer-level denial rate to the underlying claim list."},
            ],
            "non_functional": [
                "Dashboard must load filtered views in under 3 seconds against the full claims table",
                "Underlying data refresh cadence: daily",
                "Access limited to Claims Ops, Finance, and Behavioral Health network management roles",
            ],
            "data_requirements": [
                "claims table: claim_type, payer_id, provider_id, status, billed_amount, submitted_date",
                "denials table: claim_id (FK), denial_reason, denial_date",
                "payers, providers reference tables for human-readable names and region/specialty rollups",
            ],
        },
        "user_stories": [
            {
                "id": "US-1",
                "story": "As a Claims Ops Team Lead, I want to see the Behavioral Health denial rate trended monthly against the overall baseline, so that I can tell leadership whether our corrective actions are working.",
                "ac": [
                    ("Given", "the Live Dashboard is open and Behavioral Health is selected as the claim type"),
                    ("When", "I view the denial rate trend chart"),
                    ("Then", "I see monthly denial rate plotted against the all-claim-type baseline for the same months"),
                ],
            },
            {
                "id": "US-2",
                "story": "As a Finance Reimbursement Analyst, I want denial reasons ranked by total billed-dollar impact, so that I can prioritize which root cause to fix first.",
                "ac": [
                    ("Given", "I have filtered to Behavioral Health claims"),
                    ("When", "I open the denial-reason breakdown"),
                    ("Then", "reasons are sorted by total billed amount denied, descending, not just by claim count"),
                ],
            },
            {
                "id": "US-3",
                "story": "As a Provider Network Manager, I want to see denial rate by provider within Behavioral Health, so that I can identify outlier providers needing documentation coaching.",
                "ac": [
                    ("Given", "I am viewing the Behavioral Health denial report"),
                    ("When", "I group by provider"),
                    ("Then", "I can see each provider's denial rate and claim volume side by side, sorted highest denial rate first"),
                ],
            },
            {
                "id": "US-4",
                "story": "As a Claims Ops Team Lead, I want to drill from a payer's denial rate down to the specific denied claims, so that I can audit a sample without requesting a separate data pull.",
                "ac": [
                    ("Given", "a payer's denial rate is shown on the dashboard"),
                    ("When", "I click to drill down"),
                    ("Then", "I see a claim-level table filtered to that payer's denied Behavioral Health claims"),
                ],
            },
        ],
        "raid": [
            {"type": "Risk", "text": "If denial-reason data is inconsistently coded at submission, root-cause analysis will understate true drivers.", "owner": "Claims Ops"},
            {"type": "Assumption", "text": "Denial reason is captured at the point of adjudication for all payers in scope.", "owner": "BA"},
            {"type": "Issue", "text": "No existing standing report isolates denial rate by claim type — this is being built from scratch, not modified.", "owner": "BA"},
            {"type": "Dependency", "text": "Appeals/resubmission workflow automation (out of scope here) depends on this reporting being in place first.", "owner": "Claims Ops / IT"},
        ],
        "metrics": [
            {"id": "M-1", "name": "Behavioral Health Denial Rate Trend", "metric_key": "denial_rate_trend", "chart_type": "line"},
            {"id": "M-2", "name": "Denial Reason Breakdown by $ Impact", "metric_key": "denial_reason_dollar_impact", "chart_type": "bar"},
            {"id": "M-3", "name": "Denial Rate by Provider", "metric_key": "denial_rate_by_provider", "chart_type": "table"},
        ],
    },

    "payment_accuracy": {
        "title": "Standardize Monthly Payment-Accuracy Reporting",
        "ask": (
            "Finance is manually pulling payment-accuracy numbers by payer every "
            "month and it's inconsistent and slow. We need a standard, repeatable report."
        ),
        "brd": {
            "objective": (
                "Deliver a standardized, self-serve payment-accuracy report "
                "(paid vs. billed) by payer and claim type, replacing the manual "
                "monthly data pull."
            ),
            "background": (
                "Finance currently rebuilds a payment-accuracy spreadsheet by hand "
                "each month, pulling from three different exports. Numbers have "
                "varied month to month due to inconsistent filtering (e.g., whether "
                "pending claims are included), undermining trust in the report."
            ),
            "in_scope": [
                "Payment accuracy % (paid/billed) by payer, claim type, and region",
                "Standardized definition that excludes pending/denied claims from the paid-ratio calculation",
                "Month-over-month trend view",
                "Exportable view for Finance's existing monthly deck",
            ],
            "out_of_scope": [
                "Automated general-ledger reconciliation",
                "Payer-side remittance file (835) ingestion — current scope uses adjudicated claim records only",
            ],
            "success_metrics": [
                "Report generation time reduced from ~2 days manual effort to real-time self-serve",
                "Single agreed-upon definition of payment accuracy adopted by Finance and Claims Ops",
                "Zero discrepancies between monthly deck numbers and the underlying claims data",
            ],
            "stakeholders": [
                "Director of Finance",
                "Claims Ops Reporting Analyst",
                "Payer Relations team",
            ],
        },
        "frd": {
            "functional": [
                {"id": "FR-1", "text": "System shall calculate payment accuracy = SUM(paid_amount)/SUM(billed_amount) for claims with status = Paid only, explicitly excluding Denied and Pending claims from the denominator."},
                {"id": "FR-2", "text": "System shall break down payment accuracy by payer, selectable by date range."},
                {"id": "FR-3", "text": "System shall break down payment accuracy by claim type within a selected payer."},
                {"id": "FR-4", "text": "System shall display month-over-month trend for any selected payer."},
                {"id": "FR-5", "text": "System shall flag any payer whose payment accuracy drops more than 5 percentage points month-over-month."},
            ],
            "non_functional": [
                "Calculation definition must be documented inline on the report so Finance and Ops always see the same formula",
                "Data as of previous business day close",
            ],
            "data_requirements": [
                "claims table: payer_id, claim_type, billed_amount, paid_amount, status, processed_date",
                "payers reference table",
            ],
        },
        "user_stories": [
            {
                "id": "US-1",
                "story": "As a Finance Director, I want payment accuracy by payer with a clearly stated calculation definition, so that the monthly deck numbers are defensible in leadership review.",
                "ac": [
                    ("Given", "I open the Live Dashboard payment-accuracy view"),
                    ("When", "I look at any payer's accuracy figure"),
                    ("Then", "I see the exact formula used (Paid claims only; SUM(paid)/SUM(billed)) displayed alongside it"),
                ],
            },
            {
                "id": "US-2",
                "story": "As a Claims Ops Reporting Analyst, I want to be alerted when a payer's payment accuracy drops more than 5 points month-over-month, so that I can investigate before the Finance review.",
                "ac": [
                    ("Given", "payment accuracy data for the current and prior month is available"),
                    ("When", "a payer's accuracy drops more than 5 percentage points"),
                    ("Then", "that payer is visually flagged on the dashboard"),
                ],
            },
            {
                "id": "US-3",
                "story": "As a Payer Relations manager, I want to compare payment accuracy across claim types for one payer, so that I know which claim category to raise in the next payer meeting.",
                "ac": [
                    ("Given", "I select a single payer"),
                    ("When", "I view the claim-type breakdown"),
                    ("Then", "I see accuracy % per claim type ranked lowest to highest"),
                ],
            },
        ],
        "raid": [
            {"type": "Assumption", "text": "Pending claims are correctly excluded from historical accuracy calculations in all source extracts.", "owner": "BA"},
            {"type": "Risk", "text": "Without a single documented formula, Finance and Ops may continue to produce conflicting numbers even after this report ships.", "owner": "Finance"},
            {"type": "Issue", "text": "Prior months' manual spreadsheets used inconsistent denominators; historical trend prior to this project's data may not be reconcilable.", "owner": "BA"},
            {"type": "Dependency", "text": "Full remittance (835) ingestion, if later approved, would supersede the adjudicated-claims-only method used here.", "owner": "IT"},
        ],
        "metrics": [
            {"id": "M-1", "name": "Payment Accuracy by Payer", "metric_key": "payment_accuracy_by_payer", "chart_type": "bar"},
            {"id": "M-2", "name": "Payment Accuracy Trend", "metric_key": "payment_accuracy_trend", "chart_type": "line"},
            {"id": "M-3", "name": "Payment Accuracy by Claim Type", "metric_key": "payment_accuracy_by_claim_type", "chart_type": "bar"},
        ],
    },

    "processing_tat": {
        "title": "Improve Emergency Claim Processing Turnaround Time",
        "ask": (
            "Emergency claims are taking too long to process compared to other claim "
            "types and we're getting provider complaints. Leadership wants visibility "
            "into where the time is going."
        ),
        "brd": {
            "objective": (
                "Provide visibility into Emergency claim processing turnaround time "
                "(TAT) by provider and region to identify where delays concentrate, "
                "supporting a target of reducing average TAT from current levels to "
                "under 14 days."
            ),
            "background": (
                "Provider complaints about slow Emergency claim reimbursement have "
                "increased. There is currently no TAT report broken out by claim type, "
                "so Claims Ops cannot tell whether the issue is isolated to certain "
                "regions, providers, or payers, or is a broad processing capacity issue."
            ),
            "in_scope": [
                "Average and distribution of processing days for Emergency claims",
                "TAT by region and by provider",
                "TAT by payer (to rule out payer-side delay vs. internal processing delay)",
                "Comparison against all-claim-type baseline TAT",
            ],
            "out_of_scope": [
                "Claims adjudication system/workflow re-engineering (separate IT initiative)",
                "Staffing model changes",
            ],
            "success_metrics": [
                "TAT visibility delivered with provider- and region-level granularity",
                "Root-cause segment (internal vs. payer-side) identified",
                "Average Emergency claim TAT reduced to under 14 days within one quarter of report go-live",
            ],
            "stakeholders": [
                "Director of Claims Operations",
                "Regional Processing Team Leads",
                "Provider Relations",
            ],
        },
        "frd": {
            "functional": [
                {"id": "FR-1", "text": "System shall calculate processing_days = processed_date - submitted_date for each claim."},
                {"id": "FR-2", "text": "System shall display average and median processing days for Emergency claims, filterable by region, provider, and payer."},
                {"id": "FR-3", "text": "System shall compare Emergency claim TAT against the all-claim-type average TAT in the same period."},
                {"id": "FR-4", "text": "System shall rank regions by average Emergency TAT, highest first."},
                {"id": "FR-5", "text": "System shall identify the top 10 providers by claim volume with the highest average TAT, to flag for operational review."},
            ],
            "non_functional": [
                "TAT figures must exclude claims still in Pending status (no processed_date yet)",
                "Report must refresh daily",
            ],
            "data_requirements": [
                "claims table: claim_type, region, provider_id, payer_id, submitted_date, processed_date, processing_days, status",
                "providers reference table",
            ],
        },
        "user_stories": [
            {
                "id": "US-1",
                "story": "As a Director of Claims Operations, I want average Emergency claim TAT compared to the all-claim-type baseline, so that I can tell leadership whether this is an Emergency-specific issue or a systemic one.",
                "ac": [
                    ("Given", "the Live Dashboard is filtered to Emergency claims"),
                    ("When", "I view the TAT summary"),
                    ("Then", "I see Emergency average TAT side-by-side with the all-claim-type average for the same period"),
                ],
            },
            {
                "id": "US-2",
                "story": "As a Regional Processing Team Lead, I want to see TAT ranked by region, so that I know whether my region is underperforming.",
                "ac": [
                    ("Given", "I open the regional TAT breakdown"),
                    ("When", "regions are displayed"),
                    ("Then", "they are sorted by average TAT, highest (worst) first, with claim volume shown alongside"),
                ],
            },
            {
                "id": "US-3",
                "story": "As Provider Relations, I want the top providers by volume with the worst TAT flagged, so that I can proactively reach out before complaints escalate.",
                "ac": [
                    ("Given", "I view the provider TAT table"),
                    ("When", "I sort by TAT"),
                    ("Then", "I see the top 10 highest-volume, highest-TAT providers surfaced at the top"),
                ],
            },
        ],
        "raid": [
            {"type": "Risk", "text": "If delays are concentrated payer-side (not internal processing), this report alone won't resolve the underlying cause — only isolate it.", "owner": "Claims Ops"},
            {"type": "Assumption", "text": "submitted_date and processed_date are captured consistently across all regions' intake systems.", "owner": "BA"},
            {"type": "Issue", "text": "Pending claims have no processed_date and must be explicitly excluded from TAT averages to avoid understating the metric.", "owner": "BA"},
            {"type": "Dependency", "text": "Any staffing or workflow changes driven by this report's findings are a separate initiative outside this project's scope.", "owner": "Claims Ops Leadership"},
        ],
        "metrics": [
            {"id": "M-1", "name": "Emergency TAT vs. Baseline", "metric_key": "tat_vs_baseline", "chart_type": "bar"},
            {"id": "M-2", "name": "TAT by Region", "metric_key": "tat_by_region", "chart_type": "bar"},
            {"id": "M-3", "name": "Top Providers by TAT", "metric_key": "tat_by_provider", "chart_type": "table"},
        ],
    },

    "provider_visibility": {
        "title": "Self-Serve Provider Performance Visibility",
        "ask": (
            "Provider Network Managers keep emailing the analytics team for one-off "
            "claim volume and denial numbers for their providers. We need to make "
            "this self-serve."
        ),
        "brd": {
            "objective": (
                "Give Provider Network Managers a self-serve view of claim volume, "
                "denial rate, and payment accuracy at the individual provider level, "
                "eliminating ad hoc data-pull requests to the analytics team."
            ),
            "background": (
                "The analytics team fields 15-20 ad hoc requests per month from "
                "Provider Network Managers for provider-level claim metrics. Each "
                "takes 30-60 minutes to pull and format, taking the team away from "
                "higher-value analysis work."
            ),
            "in_scope": [
                "Provider-level claim volume, denial rate, and payment accuracy, filterable by specialty and region",
                "Side-by-side comparison of a provider against their specialty peer average",
                "Self-serve filtering so Network Managers do not need to request custom pulls",
            ],
            "out_of_scope": [
                "Provider contract/credentialing data (separate system)",
                "Individual patient-level data (not required for network performance reporting)",
            ],
            "success_metrics": [
                "Ad hoc data-pull requests to analytics reduced by at least 80%",
                "Network Managers can self-serve any provider's metrics within seconds",
            ],
            "stakeholders": [
                "Provider Network Managers",
                "Analytics Team Lead",
                "VP, Provider Relations",
            ],
        },
        "frd": {
            "functional": [
                {"id": "FR-1", "text": "System shall display claim volume, denial rate, and payment accuracy for any selected provider."},
                {"id": "FR-2", "text": "System shall compute the specialty peer average for the same three metrics for comparison."},
                {"id": "FR-3", "text": "System shall allow filtering the provider list by specialty and region."},
                {"id": "FR-4", "text": "System shall visually indicate when a provider's denial rate is meaningfully above their specialty peer average."},
            ],
            "non_functional": [
                "Provider search/filter must return results in under 2 seconds",
                "No login-gated data beyond existing dashboard access controls",
            ],
            "data_requirements": [
                "claims table: provider_id, claim_type, status, billed_amount, paid_amount",
                "providers table: specialty, region",
            ],
        },
        "user_stories": [
            {
                "id": "US-1",
                "story": "As a Provider Network Manager, I want to look up any provider's denial rate and compare it to their specialty's average, so that I can have an informed coaching conversation without emailing analytics.",
                "ac": [
                    ("Given", "I search for a provider on the Live Dashboard"),
                    ("When", "their profile loads"),
                    ("Then", "I see their denial rate next to the average for their specialty"),
                ],
            },
            {
                "id": "US-2",
                "story": "As an Analytics Team Lead, I want Network Managers to self-serve standard provider metrics, so that my team isn't interrupted by repetitive ad hoc requests.",
                "ac": [
                    ("Given", "a Network Manager needs a provider's claim volume and payment accuracy"),
                    ("When", "they use the self-serve provider lookup"),
                    ("Then", "no request is sent to the analytics team"),
                ],
            },
        ],
        "raid": [
            {"type": "Assumption", "text": "Provider specialty classification in the reference table is current and accurate.", "owner": "BA"},
            {"type": "Risk", "text": "Small-volume providers may show misleadingly extreme denial rates; peer-average comparison should account for sample size.", "owner": "Analytics"},
            {"type": "Dependency", "text": "Any future provider scorecard tied to compensation would require sign-off from Provider Relations leadership beyond this report's scope.", "owner": "VP, Provider Relations"},
        ],
        "metrics": [
            {"id": "M-1", "name": "Provider Denial Rate vs. Specialty Peer Avg", "metric_key": "provider_vs_peer_denial", "chart_type": "bar"},
            {"id": "M-2", "name": "Provider Claim Volume", "metric_key": "provider_volume", "chart_type": "table"},
        ],
    },
}
