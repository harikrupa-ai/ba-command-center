"""
Data Validation layer: maps each metric_key from a requirement to a real SQL
query executed against claims_ops.db, plus basic data-quality checks
(null rates, row counts, outlier flags) so the "validation" step is genuine,
not decorative.
"""
import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "claims_ops.db")

if not os.path.exists(DB_PATH):
    # First run on a fresh deploy: build the database on the fly.
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
    import build_db
    build_db.build()

QUERIES = {
    "denial_rate_trend": """
        SELECT
            strftime('%Y-%m', c.submitted_date) AS month,
            c.claim_type,
            COUNT(*) AS total_claims,
            SUM(CASE WHEN c.status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
            ROUND(100.0 * SUM(CASE WHEN c.status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 2) AS denial_rate_pct
        FROM claims c
        WHERE c.status IN ('Paid','Denied')
        GROUP BY month, c.claim_type
        ORDER BY month
    """,
    "denial_reason_dollar_impact": """
        SELECT
            d.denial_reason,
            COUNT(*) AS denied_claims,
            ROUND(SUM(c.billed_amount), 2) AS total_billed_denied
        FROM denials d
        JOIN claims c ON c.claim_id = d.claim_id
        WHERE c.claim_type = 'Behavioral Health'
        GROUP BY d.denial_reason
        ORDER BY total_billed_denied DESC
    """,
    "denial_rate_by_provider": """
        SELECT
            p.provider_name,
            p.region,
            COUNT(*) AS total_claims,
            SUM(CASE WHEN c.status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
            ROUND(100.0 * SUM(CASE WHEN c.status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 2) AS denial_rate_pct
        FROM claims c
        JOIN providers p ON p.provider_id = c.provider_id
        WHERE c.claim_type = 'Behavioral Health' AND c.status IN ('Paid','Denied')
        GROUP BY p.provider_id
        HAVING total_claims >= 20
        ORDER BY denial_rate_pct DESC
        LIMIT 15
    """,
    "payment_accuracy_by_payer": """
        SELECT
            py.payer_name,
            COUNT(*) AS paid_claims,
            ROUND(SUM(c.billed_amount), 2) AS total_billed,
            ROUND(SUM(c.paid_amount), 2) AS total_paid,
            ROUND(100.0 * SUM(c.paid_amount) / SUM(c.billed_amount), 2) AS payment_accuracy_pct
        FROM claims c
        JOIN payers py ON py.payer_id = c.payer_id
        WHERE c.status = 'Paid'
        GROUP BY py.payer_id
        ORDER BY payment_accuracy_pct ASC
    """,
    "payment_accuracy_trend": """
        SELECT
            strftime('%Y-%m', c.processed_date) AS month,
            ROUND(100.0 * SUM(c.paid_amount) / SUM(c.billed_amount), 2) AS payment_accuracy_pct
        FROM claims c
        WHERE c.status = 'Paid'
        GROUP BY month
        ORDER BY month
    """,
    "payment_accuracy_by_claim_type": """
        SELECT
            c.claim_type,
            ROUND(100.0 * SUM(c.paid_amount) / SUM(c.billed_amount), 2) AS payment_accuracy_pct
        FROM claims c
        WHERE c.status = 'Paid'
        GROUP BY c.claim_type
        ORDER BY payment_accuracy_pct ASC
    """,
    "tat_vs_baseline": """
        SELECT
            c.claim_type,
            ROUND(AVG(c.processing_days), 1) AS avg_tat_days,
            COUNT(*) AS claims
        FROM claims c
        WHERE c.processing_days IS NOT NULL
        GROUP BY c.claim_type
        ORDER BY avg_tat_days DESC
    """,
    "tat_by_region": """
        SELECT
            c.region,
            ROUND(AVG(c.processing_days), 1) AS avg_tat_days,
            COUNT(*) AS claims
        FROM claims c
        WHERE c.claim_type = 'Emergency' AND c.processing_days IS NOT NULL
        GROUP BY c.region
        ORDER BY avg_tat_days DESC
    """,
    "tat_by_provider": """
        SELECT
            p.provider_name,
            p.region,
            COUNT(*) AS claims,
            ROUND(AVG(c.processing_days), 1) AS avg_tat_days
        FROM claims c
        JOIN providers p ON p.provider_id = c.provider_id
        WHERE c.claim_type = 'Emergency' AND c.processing_days IS NOT NULL
        GROUP BY p.provider_id
        HAVING claims >= 15
        ORDER BY claims DESC, avg_tat_days DESC
        LIMIT 10
    """,
    "provider_vs_peer_denial": """
        WITH provider_stats AS (
            SELECT
                p.provider_id, p.provider_name, p.specialty, p.region,
                COUNT(*) AS total_claims,
                SUM(CASE WHEN c.status='Denied' THEN 1 ELSE 0 END) AS denied,
                100.0 * SUM(CASE WHEN c.status='Denied' THEN 1 ELSE 0 END) / COUNT(*) AS denial_rate_pct
            FROM claims c
            JOIN providers p ON p.provider_id = c.provider_id
            WHERE c.status IN ('Paid','Denied')
            GROUP BY p.provider_id
            HAVING total_claims >= 20
        ),
        specialty_avg AS (
            SELECT specialty, AVG(denial_rate_pct) AS specialty_avg_denial_pct
            FROM provider_stats GROUP BY specialty
        )
        SELECT
            ps.provider_name, ps.specialty, ps.region, ps.total_claims,
            ROUND(ps.denial_rate_pct, 2) AS provider_denial_rate_pct,
            ROUND(sa.specialty_avg_denial_pct, 2) AS specialty_avg_denial_pct
        FROM provider_stats ps
        JOIN specialty_avg sa ON sa.specialty = ps.specialty
        ORDER BY (ps.denial_rate_pct - sa.specialty_avg_denial_pct) DESC
        LIMIT 15
    """,
    "provider_volume": """
        SELECT
            p.provider_name, p.specialty, p.region,
            COUNT(*) AS total_claims,
            ROUND(SUM(c.billed_amount), 2) AS total_billed
        FROM claims c
        JOIN providers p ON p.provider_id = c.provider_id
        GROUP BY p.provider_id
        ORDER BY total_claims DESC
        LIMIT 20
    """,
}


def run_metric(metric_key: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        sql = QUERIES.get(metric_key, QUERIES["denial_rate_trend"])
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df


def get_sql_text(metric_key: str) -> str:
    return QUERIES.get(metric_key, QUERIES["denial_rate_trend"]).strip()


def data_quality_report(df: pd.DataFrame) -> list[dict]:
    """Lightweight, real data-quality checks on the query result."""
    checks = []
    checks.append({
        "check": "Row count returned",
        "result": f"{len(df):,} rows",
        "status": "pass" if len(df) > 0 else "fail",
    })
    null_counts = df.isnull().sum()
    total_nulls = int(null_counts.sum())
    checks.append({
        "check": "Null values in result set",
        "result": f"{total_nulls} null cell(s)" if total_nulls else "none found",
        "status": "pass" if total_nulls == 0 else "warn",
    })
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    outlier_note = "n/a — no numeric columns"
    status = "pass"
    for col in numeric_cols:
        if df[col].dropna().empty:
            continue
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
        if len(outliers) > 0:
            outlier_note = f"{len(outliers)} potential outlier(s) in '{col}'"
            status = "warn"
            break
        else:
            outlier_note = f"no outliers detected in '{col}' (IQR method)"
    checks.append({"check": "Outlier scan (IQR method)", "result": outlier_note, "status": status})
    return checks
