# Depositary Oversight Dashboard — Power BI Build Guide

A portfolio project built to mirror the actual responsibilities in a Junior Depositary Analyst role: daily cashflow monitoring, asset safekeeping/ownership verification, and depositary query handling. Data file: `data/depositary_oversight_dataset.xlsx` (5 sheets, fictional).

## 1. Import & Data Model

In Power BI Desktop: **Get Data → Excel workbook** → select all 5 sheets (Funds, Calendar, CashFlows, AssetHoldings, Queries) → Load.

Go to **Model view** and build a star schema:
- `Funds[FundID]` → one-to-many → `CashFlows[FundID]`
- `Funds[FundID]` → one-to-many → `AssetHoldings[FundID]`
- `Funds[FundID]` → one-to-many → `Queries[FundID]`
- `Calendar[Date]` → one-to-many → `CashFlows[Date]` (mark Calendar as a **Date table**: Table tools → Mark as date table)
- Also relate `Calendar[Date]` to `Queries[DateRaised]` as an **inactive** relationship (activate it in specific measures with `USERELATIONSHIP`)

Funds, Calendar = dimension tables (1 side). CashFlows, AssetHoldings, Queries = fact tables (many side).

## 2. DAX Measures

Create a new table (Modeling → New table, or a blank query) called `_Measures` to keep them organized, then add:

```dax
Total Cash Monitored = SUM(CashFlows[Amount_EUR])

Confirmed On Time % =
DIVIDE(
    CALCULATE(COUNTROWS(CashFlows), CashFlows[Status] = "Confirmed", CashFlows[ConfirmLagDays] <= 1),
    CALCULATE(COUNTROWS(CashFlows), CashFlows[Status] = "Confirmed")
)

Flagged Transactions = CALCULATE(COUNTROWS(CashFlows), CashFlows[Status] = "Flagged")

Pending Transactions = CALCULATE(COUNTROWS(CashFlows), CashFlows[Status] = "Pending")

Assets Verified % =
DIVIDE(
    CALCULATE(COUNTROWS(AssetHoldings), AssetHoldings[VerificationStatus] = "Verified"),
    COUNTROWS(AssetHoldings)
)

Assets With Discrepancy = CALCULATE(COUNTROWS(AssetHoldings), AssetHoldings[VerificationStatus] = "Discrepancy")

Total AUM Monitored = SUM(Funds[AUM_EUR])

Open Queries = CALCULATE(COUNTROWS(Queries), Queries[Status] <> "Closed")

Avg Query Age (Open, Days) =
AVERAGEX(
    FILTER(Queries, Queries[Status] <> "Closed"),
    DATEDIFF(Queries[DateRaised], TODAY(), DAY)
)

Queries Closed Within SLA % =
VAR ClosedQueries = FILTER(Queries, Queries[Status] = "Closed")
VAR WithinSLA =
    FILTER(
        ClosedQueries,
        DATEDIFF(Queries[DateRaised], Queries[DateClosed], DAY) <= Queries[SLA_Days]
    )
RETURN DIVIDE(COUNTROWS(WithinSLA), COUNTROWS(ClosedQueries))

New Queries (by Date Raised) =
CALCULATE(COUNTROWS(Queries), USERELATIONSHIP(Calendar[Date], Queries[DateRaised]))
```

Format each `%` measure as a percentage (0 decimal places) and each EUR measure with the `€` currency format via the Modeling ribbon.

## 3. Report Pages

Build four pages, each with a **page-level slicer panel** on the left (Fund, Client, Date range) so every visual responds together.

### Page 1 — Executive Overview
- Four KPI cards across the top: **Total AUM Monitored**, **Confirmed On Time %**, **Assets Verified %**, **Open Queries**
- Line chart: `Total Cash Monitored` by `Calendar[Month]`, split by `CashFlows[Type]`
- Donut chart: AUM by `Strategy`
- Clustered bar: AUM by `Jurisdiction`

### Page 2 — Cash Monitoring
- KPI cards: Confirmed On Time %, Flagged Transactions, Pending Transactions
- Stacked bar chart: transaction count by `CashFlows[Type]`, colored by `Status`
- Table: flagged/pending transactions only (visual-level filter: `Status` ≠ Confirmed) — columns TransactionID, FundID, Date, Type, Amount_EUR, Status — sorted by Date descending
- Line chart: daily (or weekly) transaction volume over the 6-month window

### Page 3 — Asset Safekeeping
- KPI cards: Assets Verified %, Assets With Discrepancy, Total Market Value
- Donut chart: `VerificationStatus` split
- Bar chart: Market Value by `AssetType`
- Table: holdings with `VerificationStatus` = Discrepancy or Pending, sorted oldest `LastVerifiedDate` first — this is the "needs follow-up" worklist, the most job-relevant visual on the report

### Page 4 — Query & SLA Tracker
- KPI cards: Open Queries, Avg Query Age, Queries Closed Within SLA %
- Column chart: query count by `Category`, colored by `Status`
- Line chart: `New Queries (by Date Raised)` by week — volume trend
- Table: all open/in-progress queries, sorted by `DateRaised` ascending (oldest first = highest priority)

## 4. Design Guidance (keep it clean, not cluttered)

- **Palette**: one dark navy (`#1B2A4A`), one teal accent (`#2E8B8B`), one amber for warnings/flags (`#D9A441`), neutral greys for everything else. Use amber *only* for Flagged/Discrepancy/Open states — it should draw the eye straight to what needs attention.
- **Font**: Segoe UI (Power BI default) throughout, one size for KPI numbers (28–32pt), one for labels (10–11pt).
- **KPI cards**: white background, thin 1px border or subtle shadow, no gradients, no 3D.
- **Charts**: no legends when a single series; data labels on bars instead of relying on axis gridlines; turn off gridlines on the Y axis for a cleaner look.
- **Layout**: consistent margins, align all cards and charts to a grid (View → Gridlines + Snap to grid), same visual height across a row.
- **White space**: don't fill every pixel — a little breathing room between cards reads as more professional than a dense page.

## 5. Talking About It (for a CV or interview)

Listed as: *"Depositary Oversight Dashboard (Power BI) — self-directed project modeling daily cashflow monitoring, asset safekeeping verification, and query/SLA tracking for a portfolio of funds, built on a relational data model with DAX time-intelligence measures."*

Be ready to explain, in your own words: why a star schema instead of one flat table; how `Queries Closed Within SLA %` is calculated and why that matters operationally; and what the Asset Safekeeping worklist page is *for* (prioritizing follow-up — directly mirrors the "verifying ownership of assets" responsibility in a depositary role).
