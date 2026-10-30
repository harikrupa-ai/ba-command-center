"""
Builds a Plotly figure for a given metric_key + result DataFrame. The chart
type/shape is driven by the metric's declared chart_type from the requirement
package, so the dashboard is genuinely generated from the requirement, not
hand-wired per scenario.
"""
import plotly.express as px
import plotly.graph_objects as go

TEAL = "#2E6F6E"
ACCENT = "#E8955D"
PALETTE = ["#2E6F6E", "#E8955D", "#5B7FBF", "#C4556B", "#7FA653", "#9B7EDE", "#D4A24C", "#5C9EA8"]


def _base_layout(fig, title, has_legend=False):
    fig.update_layout(
        title=dict(text=title, y=0.98),
        template="plotly_white",
        font=dict(family="Inter, -apple-system, sans-serif", size=13),
        margin=dict(l=40, r=20, t=110 if has_legend else 50, b=40),
        colorway=PALETTE,
        legend=dict(orientation="h", yanchor="top", y=1.16, xanchor="left", x=0, title_text=""),
    )
    return fig


def build_chart(metric_key: str, df, title: str, chart_type: str):
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data returned for this query", showarrow=False)
        return _base_layout(fig, title)

    cols = df.columns.tolist()

    if metric_key == "denial_rate_trend":
        fig = px.line(df, x="month", y="denial_rate_pct", color="claim_type", markers=True)
        return _base_layout(fig, title, has_legend=True)

    if metric_key == "payment_accuracy_trend":
        fig = px.line(df, x="month", y="payment_accuracy_pct", markers=True)
        return _base_layout(fig, title)

    if metric_key == "tat_vs_baseline":
        fig = px.bar(df, x="claim_type", y="avg_tat_days", text="avg_tat_days")
        fig.update_traces(texttemplate="%{text} days", textposition="outside")
        return _base_layout(fig, title)

    if chart_type == "bar":
        y_col = next((c for c in cols if "pct" in c or "amount" in c or "billed" in c or "days" in c), cols[-1])
        x_col = cols[0]
        fig = px.bar(df.sort_values(y_col, ascending=False), x=x_col, y=y_col, text=y_col)
        fig.update_traces(texttemplate="%{text}", textposition="outside")
        fig.update_xaxes(tickangle=-30)
        return _base_layout(fig, title)

    if chart_type == "line":
        y_col = next((c for c in cols if c != cols[0]), cols[-1])
        fig = px.line(df, x=cols[0], y=y_col, markers=True)
        return _base_layout(fig, title)

    # table fallback
    fig = go.Figure(data=[go.Table(
        header=dict(values=[c.replace("_", " ").title() for c in cols],
                    fill_color=TEAL, font=dict(color="white", size=12), align="left"),
        cells=dict(values=[df[c] for c in cols], align="left", height=28),
    )])
    return _base_layout(fig, title)
