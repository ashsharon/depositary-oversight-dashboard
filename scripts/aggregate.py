import json
import pandas as pd
import numpy as np

xl = pd.ExcelFile("../data/depositary_oversight_dataset.xlsx")
funds = xl.parse("Funds")
cashflows = xl.parse("CashFlows", parse_dates=["Date"])
holdings = xl.parse("AssetHoldings", parse_dates=["LastVerifiedDate"])
queries = xl.parse("Queries", parse_dates=["DateRaised", "DateClosed"])

today = pd.Timestamp("2026-09-30")

# ---------- KPIs (Executive) ----------
total_aum = int(funds["AUM_EUR"].sum())
confirmed = cashflows[cashflows["Status"] == "Confirmed"]
confirmed_on_time_pct = round(100 * (confirmed["ConfirmLagDays"] <= 1).sum() / len(confirmed), 1)
assets_verified_pct = round(100 * (holdings["VerificationStatus"] == "Verified").sum() / len(holdings), 1)
open_queries_n = int((queries["Status"] != "Closed").sum())

# ---------- Page 1: monthly cash by type (stacked) ----------
cashflows["Month"] = cashflows["Date"].dt.strftime("%b %Y")
month_order = sorted(cashflows["Month"].unique(), key=lambda m: pd.to_datetime(m, format="%b %Y"))
types = ["Capital Call", "Subscription", "Distribution", "Redemption", "Management Fee", "Expense Payment"]
monthly_by_type = (
    cashflows.groupby(["Month", "Type"])["Amount_EUR"].sum().unstack(fill_value=0)
    .reindex(index=month_order, columns=types, fill_value=0)
)
monthly_by_type_eurm = (monthly_by_type / 1_000_000).round(2)

aum_by_strategy = funds.groupby("Strategy")["AUM_EUR"].sum().sort_values(ascending=False)
aum_by_jurisdiction = funds.groupby("Jurisdiction")["AUM_EUR"].sum().sort_values(ascending=False)

# ---------- Page 2: Cash Monitoring ----------
flagged_n = int((cashflows["Status"] == "Flagged").sum())
pending_n = int((cashflows["Status"] == "Pending").sum())
count_by_type_status = (
    cashflows.groupby(["Type", "Status"]).size().unstack(fill_value=0)
    .reindex(index=types, columns=["Confirmed", "Pending", "Flagged"], fill_value=0)
)
needs_attention = (
    cashflows[cashflows["Status"] != "Confirmed"]
    .merge(funds[["FundID", "FundName"]], on="FundID")
    .sort_values("Date", ascending=False)
    .head(15)
)
cashflows["Week"] = cashflows["Date"].dt.to_period("W").apply(lambda p: p.start_time.strftime("%d %b"))
weekly_volume = cashflows.groupby("Week").size()
weekly_volume = weekly_volume.reindex(cashflows.sort_values("Date")["Week"].unique())

# ---------- Page 3: Asset Safekeeping ----------
verif_counts = holdings["VerificationStatus"].value_counts().reindex(["Verified", "Pending", "Discrepancy"], fill_value=0)
value_by_assettype = holdings.groupby("AssetType")["MarketValue_EUR"].sum().sort_values(ascending=False)
discrepancy_n = int((holdings["VerificationStatus"] == "Discrepancy").sum())
total_market_value = int(holdings["MarketValue_EUR"].sum())
followup = (
    holdings[holdings["VerificationStatus"].isin(["Discrepancy", "Pending"])]
    .merge(funds[["FundID", "FundName"]], on="FundID")
    .sort_values("VerificationStatus")
)

# ---------- Page 4: Query & SLA Tracker ----------
closed = queries[queries["Status"] == "Closed"].copy()
closed["ResolveDays"] = (closed["DateClosed"] - closed["DateRaised"]).dt.days
closed["WithinSLA"] = closed["ResolveDays"] <= closed["SLA_Days"]
sla_pct = round(100 * closed["WithinSLA"].sum() / len(closed), 1)

open_q = queries[queries["Status"] != "Closed"].copy()
open_q["AgeDays"] = (today - open_q["DateRaised"]).dt.days
avg_age = round(open_q["AgeDays"].mean(), 1)

cat_status = (
    queries.groupby(["Category", "Status"]).size().unstack(fill_value=0)
    .reindex(columns=["Closed", "In Progress", "Open"], fill_value=0)
)
queries["Week"] = queries["DateRaised"].dt.to_period("W").apply(lambda p: p.start_time.strftime("%d %b"))
weekly_new_queries = queries.groupby("Week").size()
weekly_new_queries = weekly_new_queries.reindex(queries.sort_values("DateRaised")["Week"].unique())

open_table = (
    open_q.merge(funds[["FundID", "FundName"]], on="FundID")
    .sort_values("DateRaised")
    [["QueryID", "FundName", "Category", "DateRaised", "Status", "AgeDays"]]
)

data = {
    "kpis": {
        "totalAUM": total_aum,
        "confirmedOnTimePct": confirmed_on_time_pct,
        "assetsVerifiedPct": assets_verified_pct,
        "openQueries": open_queries_n,
        "flaggedTxns": flagged_n,
        "pendingTxns": pending_n,
        "discrepancyAssets": discrepancy_n,
        "totalMarketValue": total_market_value,
        "avgQueryAge": avg_age,
        "slaPct": sla_pct,
    },
    "page1": {
        "months": month_order,
        "cashByType": {t: monthly_by_type_eurm[t].tolist() for t in types},
        "aumByStrategy": {"labels": aum_by_strategy.index.tolist(), "values": (aum_by_strategy / 1_000_000).round(1).tolist()},
        "aumByJurisdiction": {"labels": aum_by_jurisdiction.index.tolist(), "values": (aum_by_jurisdiction / 1_000_000).round(1).tolist()},
    },
    "page2": {
        "types": types,
        "countByTypeStatus": {s: count_by_type_status[s].tolist() for s in ["Confirmed", "Pending", "Flagged"]},
        "weeklyVolume": {"labels": weekly_volume.index.tolist(), "values": weekly_volume.values.tolist()},
        "needsAttention": needs_attention[["TransactionID", "FundName", "Date", "Type", "Amount_EUR", "Status"]]
            .assign(Date=lambda d: d["Date"].dt.strftime("%Y-%m-%d"))
            .to_dict("records"),
    },
    "page3": {
        "verifStatus": {"labels": verif_counts.index.tolist(), "values": verif_counts.values.tolist()},
        "valueByAssetType": {"labels": value_by_assettype.index.tolist(), "values": (value_by_assettype / 1_000_000).round(1).tolist()},
        "followup": followup[["HoldingID", "FundName", "AssetType", "MarketValue_EUR", "VerificationStatus"]].to_dict("records"),
    },
    "page4": {
        "categories": cat_status.index.tolist(),
        "catStatus": {s: cat_status[s].tolist() for s in ["Closed", "In Progress", "Open"]},
        "weeklyNew": {"labels": weekly_new_queries.index.tolist(), "values": weekly_new_queries.values.tolist()},
        "openTable": open_table.assign(DateRaised=lambda d: d["DateRaised"].dt.strftime("%Y-%m-%d")).to_dict("records"),
    },
}

with open("../preview/dashboard_data.json", "w") as f:
    json.dump(data, f, indent=2, default=str)

print("KPIs:", data["kpis"])
print("Saved ../preview/dashboard_data.json")
