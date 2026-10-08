# Depositary Oversight Dashboard

A Power BI practice project modeled on the day-to-day responsibilities of a fund depositary role: daily cashflow monitoring, asset safekeeping / ownership verification, and depositary query & SLA tracking across a portfolio of funds.

**All data in this repo is synthetic and fictional** — invented fund names, clients, and figures for demonstration purposes. It is not real client or company data.

## Status

- [x] Data model designed (star schema: Funds, Calendar, CashFlows, AssetHoldings, Queries)
- [x] Synthetic dataset generated (`data/depositary_oversight_dataset.xlsx`)
- [x] DAX measures and report spec written (`docs/build-guide.md`)
- [x] Design preview built (`preview/index.html`)
- [ ] Power BI report built in Power BI Desktop (`.pbix`) — in progress
- [ ] Screenshots of the finished report added below

## What's in here

| Path | What it is |
|---|---|
| `data/depositary_oversight_dataset.xlsx` | 5-sheet dataset: Funds, Calendar, CashFlows, AssetHoldings, Queries — ~510 transactions, 62 holdings, 93 queries across 6 funds, Apr–Sep 2026 |
| `docs/build-guide.md` | Full build guide: data model/relationships, every DAX measure, the 4-page report spec, and the design system |
| `preview/index.html` | A static HTML/Chart.js mock of the finished report's layout and visuals — a design reference, not the live Power BI file |
| `*.pbix` | The actual Power BI report — added once built in Power BI Desktop |

## Why these four pages

The report is built around the real responsibilities in a depositary analyst role, not a generic BI demo:

- **Executive Overview** — portfolio-level health at a glance (AUM, confirmation rate, verification rate, open queries)
- **Cash Monitoring** — the daily cashflow-confirmation workflow, with a worklist of anything not yet confirmed
- **Asset Safekeeping** — ownership verification status by asset, with a follow-up worklist sorted oldest-first (this is the closest analogue to "verifying ownership of the assets of a fund")
- **Query & SLA Tracker** — open depositary queries against their SLA, mirroring "routine depositary information requests and queries"

## Reproducing the dataset

```bash
pip install pandas numpy openpyxl
python scripts/generate_data.py   # writes data/depositary_oversight_dataset.xlsx
python scripts/aggregate.py       # writes preview/dashboard_data.json (used by preview/index.html)
```
