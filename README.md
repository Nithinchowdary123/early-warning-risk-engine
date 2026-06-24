# 🎯 Early-Warning Risk Engine

**An end-to-end analytics product that scores every entity in a population by its risk of a bad outcome — early enough to act on it.**

The demo predicts which **students** are at risk of not being retained, so advisors can intervene before they drop out. But the engine is deliberately **domain-agnostic**: every column, the target, and the risk thresholds live in [`config.yaml`](config.yaml). Repoint that config and the *same pipeline* scores **wells, pumps, or any asset** — turning it into a predictive-maintenance / production-decline monitor.

> **The pitch in one line:** *Same architecture, swap the entity.* At a university it flags at-risk students; at an E&P operator it flags underperforming wells or equipment heading for failure.

| Build it once for…        | …and it transfers to                                   |
|---------------------------|--------------------------------------------------------|
| **Student** → not retained | **Well** → production decline                          |
| LMS logins / submit rate   | Sensor pings / telemetry frequency                     |
| Current vs. prior GPA      | Current vs. baseline production rate                   |
| "At-risk student" watchlist| "At-risk asset" maintenance watchlist                  |

---

## 🚀 Live demo

**Repo:** https://github.com/Nithinchowdary123/early-warning-risk-engine

> One step left (interactive, ~3 min — see [Deployment](#-deployment)): connect the repo on
> [share.streamlit.io](https://share.streamlit.io) to get your live URL, then paste it here:
> **`https://<your-app>.streamlit.app`**

The dashboard includes KPIs, cohort risk analysis, model-driven risk drivers, an exportable **intervention watchlist**, and a **live what-if scorer** that recomputes risk as you move the sliders.

---

## 🏗️ Architecture

```
 data/raw            src/                                  app/
┌──────────┐   ┌────────────────────────────────────┐   ┌──────────────┐
│ raw CSV  │ → │ prepare_data.py  (clean + validate │ → │ streamlit_app│
│ (messy)  │   │                   + feature eng.)   │   │  • KPIs      │
└──────────┘   │ warehouse.py     (DuckDB + SQL)     │   │  • watchlist │
               │ risk_engine.py   (train + score)    │   │  • live score│
               └────────────────────────────────────┘   └──────────────┘
        config.yaml  ◄── single source of truth for the whole pipeline
```

**Flow:** ingest → validate & clean → engineer features → SQL analytics → train model → score & band every entity → monitor on the dashboard.

---

## 🧰 What this demonstrates

| Skill (from the JD / résumé) | Where it shows up |
|------------------------------|-------------------|
| **SQL** (CTEs, window functions, cohort analysis) | [`src/sql/analytics.sql`](src/sql/analytics.sql) — `NTILE` engagement deciles, cohort risk, trends |
| **Python** (pandas, NumPy, scikit-learn) | the entire `src/` pipeline |
| **Data cleaning & validation** | [`prepare_data.py`](src/prepare_data.py) — dedupe, standardize, range-check, impute (with a printed data-quality report) |
| **Statistical / predictive modeling** | [`risk_engine.py`](src/risk_engine.py) — Gradient Boosting, ROC-AUC, feature importance |
| **BI / dashboards** | [`app/streamlit_app.py`](app/streamlit_app.py) — Plotly + Streamlit, interactive |
| **Translating data → decisions** | the exportable watchlist + "so what" recommendations |
| **ETL / reproducibility** | [`run_pipeline.py`](run_pipeline.py) rebuilds everything with one command |

---

## 📊 Selected findings (from the demo data)

- **Engagement is the strongest lever:** non-retention falls from **64.6%** in the least-engaged decile to **16.5%** in the most-engaged — a clean, monotonic gradient.
- **Equity gap:** first-generation students show a **+7.9 pp** higher non-retention rate (43.5% vs. 35.6%).
- **Model:** Gradient Boosting reaches **ROC-AUC ≈ 0.80**; top drivers are current GPA, assignment submission rate, and LMS logins.
- **Actionable output:** the engine flags **~3,400 high-risk students** for early intervention.

---

## ▶️ Run it locally

```bash
# 1. set up an isolated environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. build everything (data → clean → warehouse → model)
python run_pipeline.py

# 3. launch the dashboard
streamlit run app/streamlit_app.py
```

---

## ☁️ Deployment

The app is built for **free** hosting on Streamlit Community Cloud:

1. Push this repo to GitHub (see [`DEPLOY.md`](DEPLOY.md) for exact commands).
2. Go to **[share.streamlit.io](https://share.streamlit.io)** → *New app*.
3. Point it at `app/streamlit_app.py` on your `main` branch.
4. Deploy. You get a public URL to put on your résumé.

> The processed data (`*.parquet`) and trained model (`*.joblib`) are committed so the deployed app runs immediately. The version-specific DuckDB binary is rebuilt on the fly (in-memory), so it's git-ignored.

---

## 🔁 Repointing to a new domain (the EOG move)

To make this a **production / predictive-maintenance** monitor, you change *config, not code*:

1. Drop in the new dataset (e.g., well telemetry).
2. In `config.yaml`, set `domain.entity_label: "Well"`, `event_label: "Production Decline"`, and list the new feature columns + target.
3. Re-run `python run_pipeline.py`.

The cleaning, SQL, modeling, and dashboard all adapt automatically — that's the design.

---

## 🗂️ Repo structure

```
.
├── config.yaml              # single source of truth (domain, features, thresholds)
├── run_pipeline.py          # one-command rebuild
├── requirements.txt
├── data/
│   ├── raw/                 # generated messy extract
│   └── processed/           # cleaned parquet + scored output
├── src/
│   ├── generate_data.py     # realistic synthetic data w/ injected mess
│   ├── prepare_data.py      # clean, validate, feature-engineer
│   ├── warehouse.py         # DuckDB + named SQL runner
│   ├── risk_engine.py       # config-driven train + score
│   └── sql/analytics.sql    # the analytical SQL
├── app/
│   └── streamlit_app.py     # the dashboard
└── models/                  # trained model bundle
```

---

*Demo data is fully synthetic and contains no real student records.*
