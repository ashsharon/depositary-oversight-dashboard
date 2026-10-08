"""
Generates a synthetic, clearly-fictional dataset modeling depositary / fund-oversight
operations, for use as a Power BI portfolio project.

NOT real client or company data. Fund names, client names and figures are invented
for demonstration purposes only.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# 1. Funds (dimension)
# ---------------------------------------------------------------------------
funds = pd.DataFrame([
    {"FundID": "F01", "FundName": "Meridian Private Equity Fund I",      "Client": "Juniper Capital Partners",   "Strategy": "Private Equity",   "Jurisdiction": "Luxembourg", "Custodian": "Northgate Custody Bank",   "AUM_EUR": 412_000_000},
    {"FundID": "F02", "FundName": "Northbridge Real Assets II",          "Client": "Northbridge Advisors",       "Strategy": "Real Assets",      "Jurisdiction": "Guernsey",    "Custodian": "Harborview Trust & Custody","AUM_EUR": 287_500_000},
    {"FundID": "F03", "FundName": "Solstice Infrastructure Fund",        "Client": "Solstice Capital Group",     "Strategy": "Infrastructure",   "Jurisdiction": "Ireland",     "Custodian": "Northgate Custody Bank",   "AUM_EUR": 540_000_000},
    {"FundID": "F04", "FundName": "Alderwood Venture Fund III",          "Client": "Alderwood Partners",         "Strategy": "Venture Capital",  "Jurisdiction": "Luxembourg",  "Custodian": "Cedar Point Custody",      "AUM_EUR": 165_000_000},
    {"FundID": "F05", "FundName": "Kestrel Private Debt Fund",           "Client": "Kestrel Asset Management",   "Strategy": "Private Debt",     "Jurisdiction": "Jersey",      "Custodian": "Harborview Trust & Custody","AUM_EUR": 231_000_000},
    {"FundID": "F06", "FundName": "Thornfield Secondaries Fund II",      "Client": "Thornfield Capital",         "Strategy": "Private Equity",   "Jurisdiction": "Guernsey",    "Custodian": "Cedar Point Custody",      "AUM_EUR": 198_000_000},
])

# ---------------------------------------------------------------------------
# 2. Calendar (dimension) — 1 Apr 2026 to 30 Sep 2026, a 6-month monitoring window
# ---------------------------------------------------------------------------
start, end = date(2026, 4, 1), date(2026, 9, 30)
cal_dates = pd.date_range(start, end, freq="D")
calendar = pd.DataFrame({
    "Date": cal_dates,
    "Year": cal_dates.year,
    "Month": cal_dates.strftime("%b %Y"),
    "MonthNum": cal_dates.month,
    "Weekday": cal_dates.strftime("%A"),
    "IsWeekend": cal_dates.weekday >= 5,
})

business_days = calendar.loc[~calendar["IsWeekend"], "Date"].tolist()

# ---------------------------------------------------------------------------
# 3. CashFlows (fact) — daily cashflow monitoring
# ---------------------------------------------------------------------------
cf_types = ["Subscription", "Redemption", "Capital Call", "Distribution", "Management Fee", "Expense Payment"]
cf_type_w = [0.18, 0.08, 0.27, 0.22, 0.15, 0.10]
statuses = ["Confirmed", "Confirmed", "Confirmed", "Confirmed", "Pending", "Flagged"]  # weighted via choice below

rows = []
tid = 1000
for d in business_days:
    n_today = rng.integers(2, 7)
    for _ in range(n_today):
        fund = funds.sample(1, random_state=rng.integers(1, 1_000_000)).iloc[0]
        cf_type = rng.choice(cf_types, p=cf_type_w)
        if cf_type in ("Capital Call", "Subscription"):
            amount = rng.uniform(500_000, 15_000_000)
        elif cf_type in ("Distribution", "Redemption"):
            amount = rng.uniform(300_000, 12_000_000)
        else:
            amount = rng.uniform(5_000, 350_000)
        status_roll = rng.random()
        if status_roll < 0.86:
            status = "Confirmed"
            lag_roll = rng.random()
            if lag_roll < 0.80:
                confirm_lag = 0   # same-day, the SLA target
            elif lag_roll < 0.94:
                confirm_lag = 1
            else:
                confirm_lag = int(rng.integers(2, 4))  # occasional late confirmation
        elif status_roll < 0.96:
            status = "Pending"
            confirm_lag = None
        else:
            status = "Flagged"
            confirm_lag = None
        rows.append({
            "TransactionID": f"TXN{tid}",
            "FundID": fund["FundID"],
            "Date": d,
            "Type": cf_type,
            "Amount_EUR": round(amount, 2),
            "Status": status,
            "ConfirmLagDays": confirm_lag,
        })
        tid += 1

cashflows = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# 4. AssetHoldings (fact) — asset safekeeping / ownership verification
# ---------------------------------------------------------------------------
asset_types = ["Equity Stake", "Fund Interest", "Real Estate Asset", "Infrastructure Asset", "Debt Instrument", "Cash & Equivalents"]
holding_rows = []
hid = 1
for _, fund in funds.iterrows():
    n_assets = rng.integers(8, 14)
    for _ in range(n_assets):
        asset_type = rng.choice(asset_types)
        value = rng.uniform(2_000_000, 60_000_000)
        verify_roll = rng.random()
        if verify_roll < 0.78:
            v_status = "Verified"
            v_date = pd.Timestamp(end) - timedelta(days=int(rng.integers(0, 85)))
        elif verify_roll < 0.93:
            v_status = "Pending"
            v_date = pd.NaT
        else:
            v_status = "Discrepancy"
            v_date = pd.Timestamp(end) - timedelta(days=int(rng.integers(0, 20)))
        holding_rows.append({
            "HoldingID": f"AST{hid:04d}",
            "FundID": fund["FundID"],
            "AssetName": f"{asset_type.split(' ')[0]} Position {hid}",
            "AssetType": asset_type,
            "Custodian": fund["Custodian"],
            "MarketValue_EUR": round(value, 2),
            "VerificationStatus": v_status,
            "LastVerifiedDate": v_date,
        })
        hid += 1

holdings = pd.DataFrame(holding_rows)

# ---------------------------------------------------------------------------
# 5. Queries (fact) — depositary information requests / correspondence tracking
# ---------------------------------------------------------------------------
categories = ["Cash Monitoring", "Safekeeping", "Documentation", "Valuation", "Other"]
raised_by = ["Client", "Fund Administrator", "Internal Review", "Auditor"]
query_rows = []
qid = 1
for d in business_days:
    if rng.random() < 0.55:  # not every day has a new query
        continue
    n_new = rng.integers(1, 3)
    for _ in range(n_new):
        fund = funds.sample(1, random_state=rng.integers(1, 1_000_000)).iloc[0]
        category = rng.choice(categories, p=[0.32, 0.26, 0.18, 0.14, 0.10])
        sla_days = {"Cash Monitoring": 1, "Safekeeping": 3, "Documentation": 5, "Valuation": 5, "Other": 3}[category]
        days_since_raised = (pd.Timestamp(end) - pd.Timestamp(d)).days
        # Older queries have had time to close; only a recent handful are still open/in progress.
        # Anything past 20 days is force-closed — a well-run queue doesn't let items go stale.
        recency = min(1.0, days_since_raised / 15)
        close_prob = 1.0 if days_since_raised > 20 else 0.30 + 0.68 * recency
        resolve_roll = rng.random()
        if resolve_roll < close_prob:
            status = "Closed"
            resolve_days = max(0, int(rng.normal(sla_days * 0.8, sla_days * 0.5)))
            resolve_days = min(resolve_days, max(1, days_since_raised))
            date_closed = pd.Timestamp(d) + timedelta(days=resolve_days)
            if date_closed.date() > end:
                date_closed = pd.Timestamp(end)
        elif resolve_roll < close_prob + 0.65 * (1 - close_prob):
            status = "In Progress"
            date_closed = pd.NaT
        else:
            status = "Open"
            date_closed = pd.NaT
        query_rows.append({
            "QueryID": f"QRY{qid:04d}",
            "FundID": fund["FundID"],
            "DateRaised": d,
            "RaisedBy": rng.choice(raised_by),
            "Category": category,
            "SLA_Days": sla_days,
            "Status": status,
            "DateClosed": date_closed,
        })
        qid += 1

queries = pd.DataFrame(query_rows)

# ---------------------------------------------------------------------------
# Write workbook
# ---------------------------------------------------------------------------
out_path = "../data/depositary_oversight_dataset.xlsx"
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    funds.to_excel(writer, sheet_name="Funds", index=False)
    calendar.to_excel(writer, sheet_name="Calendar", index=False)
    cashflows.to_excel(writer, sheet_name="CashFlows", index=False)
    holdings.to_excel(writer, sheet_name="AssetHoldings", index=False)
    queries.to_excel(writer, sheet_name="Queries", index=False)

print("Funds:", len(funds))
print("Calendar days:", len(calendar))
print("CashFlows:", len(cashflows))
print("AssetHoldings:", len(holdings))
print("Queries:", len(queries))
print("Saved to", out_path)
