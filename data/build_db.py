"""
Builds a realistic, normalized SQLite database for a healthcare claims-operations
business: payers, providers, claims, and denials as separate related tables
(not a flat CSV) so the Data Validation layer can run real JOIN queries.

Run: python data/build_db.py
Output: data/claims_ops.db
"""
import sqlite3
import numpy as np
import os
from datetime import datetime, timedelta

rng = np.random.default_rng(42)
DB_PATH = os.path.join(os.path.dirname(__file__), "claims_ops.db")

N_CLAIMS = 120_000
N_PROVIDERS = 180

PAYERS = [
    ("PYR001", "Cigna Healthcare", "Commercial"),
    ("PYR002", "Aetna", "Commercial"),
    ("PYR003", "UnitedHealthcare", "Commercial"),
    ("PYR004", "BCBS of Texas", "Commercial"),
    ("PYR005", "Humana", "Medicare Advantage"),
    ("PYR006", "Kaiser Permanente", "Commercial"),
    ("PYR007", "Anthem", "Commercial"),
    ("PYR008", "Molina Healthcare", "Medicaid"),
]
PAYER_WEIGHTS = np.array([0.22, 0.17, 0.16, 0.14, 0.11, 0.08, 0.07, 0.05])

REGIONS = ["DFW", "Houston", "Austin", "San Antonio", "El Paso"]
REGION_WEIGHTS = np.array([0.34, 0.26, 0.17, 0.14, 0.09])

SPECIALTIES = [
    "Primary Care", "Cardiology", "Orthopedics", "Behavioral Health",
    "Pharmacy Services", "Emergency Medicine", "Oncology", "Pediatrics",
    "OB/GYN", "Physical Therapy",
]

CLAIM_TYPES = {
    "Outpatient":        {"base": 650,  "sigma": 0.55, "denial_base": 0.085},
    "Inpatient":         {"base": 9200, "sigma": 0.65, "denial_base": 0.065},
    "Pharmacy":          {"base": 180,  "sigma": 0.70, "denial_base": 0.045},
    "Emergency":         {"base": 2400, "sigma": 0.60, "denial_base": 0.115},
    "Preventive":        {"base": 240,  "sigma": 0.40, "denial_base": 0.020},
    "Behavioral Health": {"base": 410,  "sigma": 0.50, "denial_base": 0.135},
}
CLAIM_TYPE_NAMES = list(CLAIM_TYPES.keys())
CLAIM_TYPE_WEIGHTS = np.array([0.34, 0.09, 0.22, 0.12, 0.14, 0.09])

DENIAL_REASONS = [
    ("Missing Prior Authorization", 0.24),
    ("Incorrect Procedure Coding", 0.19),
    ("Timely Filing Limit Exceeded", 0.15),
    ("Patient Not Eligible on DOS", 0.13),
    ("Duplicate Claim Submission", 0.10),
    ("Non-Covered Service", 0.09),
    ("Incomplete Documentation", 0.06),
    ("Coordination of Benefits Issue", 0.04),
]


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE payers (
            payer_id TEXT PRIMARY KEY,
            payer_name TEXT NOT NULL,
            payer_type TEXT NOT NULL
        )
    """)
    cur.executemany("INSERT INTO payers VALUES (?,?,?)", PAYERS)

    cur.execute("""
        CREATE TABLE providers (
            provider_id TEXT PRIMARY KEY,
            provider_name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            region TEXT NOT NULL
        )
    """)
    providers = []
    for i in range(N_PROVIDERS):
        pid = f"PRV{i+1:04d}"
        specialty = rng.choice(SPECIALTIES)
        region = rng.choice(REGIONS, p=REGION_WEIGHTS)
        name = f"{specialty.split('/')[0].split(' ')[0]} Group of {region} #{i % 37 + 1}"
        providers.append((pid, name, specialty, region))
    cur.executemany("INSERT INTO providers VALUES (?,?,?,?)", providers)

    cur.execute("""
        CREATE TABLE claims (
            claim_id TEXT PRIMARY KEY,
            provider_id TEXT NOT NULL,
            payer_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            region TEXT NOT NULL,
            billed_amount REAL NOT NULL,
            paid_amount REAL NOT NULL,
            status TEXT NOT NULL,
            submitted_date TEXT NOT NULL,
            processed_date TEXT,
            processing_days INTEGER,
            FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
            FOREIGN KEY (payer_id) REFERENCES payers(payer_id)
        )
    """)
    cur.execute("""
        CREATE TABLE denials (
            denial_id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            denial_reason TEXT NOT NULL,
            denial_date TEXT NOT NULL,
            FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
        )
    """)

    start_date = datetime(2025, 1, 1)
    date_span_days = 660  # through mid-Oct 2026

    claim_types = rng.choice(CLAIM_TYPE_NAMES, size=N_CLAIMS, p=CLAIM_TYPE_WEIGHTS)
    payer_idx = rng.choice(len(PAYERS), size=N_CLAIMS, p=PAYER_WEIGHTS)
    provider_idx = rng.integers(0, N_PROVIDERS, size=N_CLAIMS)
    offsets = rng.integers(0, date_span_days, size=N_CLAIMS)

    claims_rows = []
    denial_rows = []
    denial_counter = 1

    for i in range(N_CLAIMS):
        ctype = claim_types[i]
        cfg = CLAIM_TYPES[ctype]
        billed = float(np.round(rng.lognormal(mean=np.log(cfg["base"]), sigma=cfg["sigma"]), 2))
        billed = max(billed, 25.0)

        provider = providers[provider_idx[i]]
        payer = PAYERS[payer_idx[i]]
        region = provider[3]

        submitted = start_date + timedelta(days=int(offsets[i]))
        proc_days = int(max(1, rng.normal(18, 9)))
        processed = submitted + timedelta(days=proc_days)

        denial_prob = cfg["denial_base"]
        # a couple of payers run noticeably higher/lower denial rates, realistically
        if payer[0] in ("PYR008",):  # Medicaid payer, higher denial rate
            denial_prob *= 1.6
        elif payer[0] in ("PYR006",):  # Kaiser, lower
            denial_prob *= 0.7

        roll = rng.random()
        if processed > datetime(2026, 10, 20):
            status = "Pending"
            paid = 0.0
            processed_str = None
            proc_days_val = None
        elif roll < denial_prob:
            status = "Denied"
            paid = 0.0
            processed_str = processed.strftime("%Y-%m-%d")
            proc_days_val = proc_days
            reason = rng.choice(
                [r[0] for r in DENIAL_REASONS],
                p=np.array([r[1] for r in DENIAL_REASONS]),
            )
            denial_rows.append((
                f"DNL{denial_counter:06d}", f"CLM{i+1:07d}", reason, processed_str
            ))
            denial_counter += 1
        else:
            status = "Paid"
            accuracy = rng.normal(0.93, 0.06)
            paid = float(np.round(billed * max(0.35, min(1.0, accuracy)), 2))
            processed_str = processed.strftime("%Y-%m-%d")
            proc_days_val = proc_days

        claims_rows.append((
            f"CLM{i+1:07d}", provider[0], payer[0], ctype, region,
            billed, paid, status,
            submitted.strftime("%Y-%m-%d"), processed_str, proc_days_val,
        ))

    cur.executemany(
        "INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?,?)", claims_rows
    )
    cur.executemany(
        "INSERT INTO denials VALUES (?,?,?,?)", denial_rows
    )

    cur.execute("CREATE INDEX idx_claims_payer ON claims(payer_id)")
    cur.execute("CREATE INDEX idx_claims_provider ON claims(provider_id)")
    cur.execute("CREATE INDEX idx_claims_status ON claims(status)")
    cur.execute("CREATE INDEX idx_denials_claim ON denials(claim_id)")

    conn.commit()

    n_claims = cur.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    n_denials = cur.execute("SELECT COUNT(*) FROM denials").fetchone()[0]
    n_providers = cur.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
    print(f"Built {DB_PATH}")
    print(f"  claims:    {n_claims:,}")
    print(f"  denials:   {n_denials:,}")
    print(f"  providers: {n_providers:,}")
    print(f"  payers:    {len(PAYERS)}")

    conn.close()


if __name__ == "__main__":
    build()
