import argparse, io, sys, time, math
import pandas as pd, numpy as np, requests as rq
from datetime import datetime

OWID_URL = "https://covid.ourworldindata.org/data/owid-covid-data.csv"  # doc: docs.owid.io
WB_BASE = "https://api.worldbank.org/v2"

WB_SERIES = {
    "SI.POV.GINI": "gini",
    "PA.NUS.PPP": "ppp_conv_gdp_lcu_per_intl$",
    "NY.GDP.PCAP.PP.KD": "gdp_pc_ppp_const2021",
    "NY.GDP.PCAP.PP.CD": "gdp_pc_ppp_current",
    "FP.CPI.TOTL.ZG": "inflation_cpi_annual_pct",
    "SL.UEM.TOTL.ZS": "unemployment_total_pct",
}

NON_COUNTRY_ISO3 = {"WLD","EUN","EUU","OED","HIC","LMY","LIC","MIC","LMC","UMC","SSA","EAP","ECA","MNA","NAC","SAS","LCN","MEA"}  # aggregates

def fetch_wb_indicator(ind, start_year=2019, end_year=None):
    end_year = end_year or datetime.utcnow().year
    per_page = 20000
    page = 1
    rows = []
    while True:
        url = f"{WB_BASE}/country/all/indicator/{ind}?date={start_year}:{end_year}&format=json&per_page={per_page}&page={page}"
        r = rq.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or len(data) < 2 or data[1] is None:
            break
        meta, items = data[0], data[1]
        for it in items:
            iso3 = it.get("countryiso3code")
            if not iso3 or iso3 in NON_COUNTRY_ISO3: 
                continue
            if it.get("value") is None: 
                continue
            rows.append({
                "iso3": iso3,
                "year": int(it["date"]),
                "indicator": ind,
                "value": it["value"],
            })
        if meta.get("page") * meta.get("pages", 1) >= meta.get("pages", 1):
            if page >= meta.get("pages", 1):
                break
        page += 1
    df = pd.DataFrame(rows)
    return df

def fetch_worldbank(start_year=2019):
    frames = []
    for ind in WB_SERIES:
        df = fetch_wb_indicator(ind, start_year=start_year)
        if not df.empty:
            df["var"] = WB_SERIES[ind]
            frames.append(df[["iso3","year","var","value"]])
    if not frames:
        return pd.DataFrame(columns=["iso3","year","var","value"])
    out = pd.concat(frames, ignore_index=True)
    return out

def fetch_owid_covid():
    # daily CSV (wide dataset) — we subset useful columns
    df = pd.read_csv(OWID_URL, parse_dates=["date"])
    keep = [
        "iso_code","location","date",
        "new_cases","new_deaths",
        "total_cases","total_deaths",
        "new_vaccinations","people_vaccinated","people_fully_vaccinated",
        "population"
    ]
    present = [c for c in keep if c in df.columns]
    df = df[present]
    # filter to country ISO-3 (skip OWID_* aggregates)
    df = df[df["iso_code"].str.len()==3].copy()
    return df

def monthly_from_daily(df):
    # sum flows (new_*) and take last for stocks (total_*, people_*)
    df["year_month"] = df["date"].values.astype("datetime64[M]")
    flows = [c for c in df.columns if c.startswith("new_")]
    stocks = [c for c in df.columns if c.startswith("total_") or c.startswith("people_")]
    grp = df.groupby(["iso_code","location","year_month"])
    agg = {}
    for c in flows: agg[c] = "sum"
    for c in stocks: agg[c] = "last"
    out = grp.agg(agg).reset_index()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-year", type=int, default=2019)
    args = ap.parse_args()

    print("Fetching OWID COVID…")
    covid_daily = fetch_owid_covid()
    covid_daily = covid_daily[covid_daily["date"] >= pd.Timestamp(f"{args.start_year}-01-01")]
    covid_daily.to_csv("data/owid_covid_daily.csv", index=False)

    print("Aggregating monthly COVID…")
    covid_monthly = monthly_from_daily(covid_daily)
    covid_monthly.to_csv("data/owid_covid_monthly.csv", index=False)

    print("Fetching World Bank indicators…")
    wb = fetch_worldbank(start_year=args.start_year)
    wb.sort_values(["iso3","year","var"], inplace=True)
    wb.to_csv("data/wb_annual_economy.csv", index=False)

    # data source notes
    with open("README_DATA_SOURCES.md","w", encoding="utf-8") as f:
        f.write(
"""# Data Sources

- Our World in Data COVID-19: docs + CSV (cases/deaths/tests/vaccinations). See: https://docs.owid.io/projects/covid/en/latest/dataset.html
- World Bank Indicators API. Example structure & paging: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures
- Codes used:
  - Gini: SI.POV.GINI
  - PPP conversion factor (GDP, LCU per intl $): PA.NUS.PPP
  - GDP per capita, PPP (constant 2021 intl $): NY.GDP.PCAP.PP.KD
  - GDP per capita, PPP (current intl $): NY.GDP.PCAP.PP.CD
  - Inflation, CPI (annual %): FP.CPI.TOTL.ZG
  - Unemployment, total (%): SL.UEM.TOTL.ZS
"""
        )
    print("Done. Files in /data.")

if __name__ == "__main__":
    main()
