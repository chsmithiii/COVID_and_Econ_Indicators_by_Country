# COVID & Economic Indicators by Country (2019 → present)

This repo builds a tidy panel combining **COVID-19** daily metrics with **annual macro indicators** (GINI, PPP, GDP per capita PPP, inflation, unemployment) for all countries, 2019–present.

## Data sources
- COVID-19: Our World in Data — complete CSV (cases, deaths, tests, vax).  
- Economics: World Bank Indicators API (annual).  
See `/src/fetch_and_build.py` for exact endpoints and series codes.

## Output (written to `/data`)
- `owid_covid_daily.csv` — daily by country (subset of columns)
- `owid_covid_monthly.csv` — monthly aggregates (sums for flow, last-of-month for stocks)
- `wb_annual_economy.csv` — annual indicators by country/indicator
- `README_DATA_SOURCES.md` — links and notes

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/fetch_and_build.py --start-year 2019
```

## Indicators pulled (World Bank codes)
- Gini index: `SI.POV.GINI`
- PPP conversion factor, GDP (LCU per intl $): `PA.NUS.PPP`
- GDP per capita, PPP (constant 2021 intl $): `NY.GDP.PCAP.PP.KD`
- GDP per capita, PPP (current intl $): `NY.GDP.PCAP.PP.CD`
- Inflation, consumer prices (annual %): `FP.CPI.TOTL.ZG`
- Unemployment, total (% of total labor force): `SL.UEM.TOTL.ZS`

> Notes: GINI/PPP are annual and country coverage varies by year. COVID is daily; we also publish monthly aggregates.

## Automations
A GitHub Action runs weekly to refresh data and commit changes (see `.github/workflows/update-data.yml`).
