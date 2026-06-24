# Early-Warning Risk Engine

I built this to score every record in a population by how likely it is to end badly, early enough that someone can actually do something about it.

The demo version predicts which students are at risk of not being retained, so an advisor can step in before they drop out. The part I care about more is that none of the modeling code knows it's working with students. The entity, the features, the target, and the risk cutoffs all live in [`config.yaml`](config.yaml). Point that file at a different dataset and the same pipeline scores wells, pumps, or any other asset instead. That's how a student-retention project becomes a predictive-maintenance or production-monitoring project without rewriting anything.

Here's the mapping I had in mind:

| Student version | Asset version (e.g. oil & gas) |
|---|---|
| Student → not retained | Well → production decline |
| LMS logins, submit rate | Sensor readings, telemetry frequency |
| Current vs. prior GPA | Current vs. baseline production |
| At-risk student watchlist | At-risk asset maintenance list |

## Live demo

Repo: https://github.com/Nithinchowdary123/early-warning-risk-engine

The dashboard has the headline KPIs, cohort risk breakdowns, the model's top risk drivers, an exportable watchlist of the highest-risk records, and a what-if tool that recomputes the risk score live as you move the sliders.

Hosted version (Streamlit Cloud): _add the URL here once deployed — see [DEPLOY.md](DEPLOY.md)._

## How it fits together

```
 data/raw            src/                                  app/
┌──────────┐   ┌────────────────────────────────────┐   ┌──────────────┐
│ raw CSV  │ → │ prepare_data.py  (clean + validate │ → │ streamlit_app│
│ (messy)  │   │                   + feature eng.)   │   │  KPIs        │
└──────────┘   │ warehouse.py     (DuckDB + SQL)     │   │  watchlist   │
               │ risk_engine.py   (train + score)    │   │  live score  │
               └────────────────────────────────────┘   └──────────────┘
        config.yaml drives every stage
```

The flow is: load the raw extract, clean and validate it, engineer a few features, run the SQL analytics, train the model, score and band every record, then surface it all on the dashboard.

## What's in here

- **SQL** ([`src/sql/analytics.sql`](src/sql/analytics.sql)) — cohort comparisons, term trends, and an `NTILE` window function to bucket students into engagement deciles.
- **Cleaning and validation** ([`src/prepare_data.py`](src/prepare_data.py)) — drops duplicates, standardizes the messy category labels, throws out impossible values, and imputes what's missing. It prints a short data-quality report so you can see exactly what it changed.
- **Modeling** ([`src/risk_engine.py`](src/risk_engine.py)) — a gradient boosting classifier with ROC-AUC and feature importances. Nothing in this file is student-specific; it reads everything from the config.
- **Dashboard** ([`app/streamlit_app.py`](app/streamlit_app.py)) — Streamlit and Plotly.
- **One-command rebuild** ([`run_pipeline.py`](run_pipeline.py)) — regenerates the whole thing from scratch.

## What the data says

A few things that came out of the demo dataset:

- Engagement matters most. Non-retention drops from about 65% among the least-engaged students to roughly 17% among the most-engaged.
- First-generation students are retained at a noticeably lower rate (about 8 points lower than continuing-generation students).
- The model lands around 0.80 ROC-AUC. The strongest drivers are current GPA, assignment submission rate, and LMS logins.
- It ends up flagging a few thousand students as high-risk, which is the list an advising team would actually work from.

## Running it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python run_pipeline.py            # data -> clean -> warehouse -> model
streamlit run app/streamlit_app.py
```

## Deploying it

It's set up for Streamlit Community Cloud, which is free. Short version: push to GitHub, go to [share.streamlit.io](https://share.streamlit.io), make a new app pointing at `app/streamlit_app.py` on `main`. Full steps are in [DEPLOY.md](DEPLOY.md).

The cleaned data and the trained model are committed so the hosted app works straight away. The DuckDB file is tied to a specific version, so I left it out of git and rebuild it in memory at query time instead.

## Pointing it at a different problem

To turn this into, say, an equipment-failure monitor:

1. Swap in the new dataset.
2. In `config.yaml`, change `entity_label` and `event_label` and list the new feature columns and target.
3. Run `python run_pipeline.py` again.

The cleaning, SQL, model, and dashboard pick up the new config without code changes.

## Layout

```
config.yaml              config that drives the whole pipeline
run_pipeline.py          rebuild everything in one command
requirements.txt
data/
  raw/                   generated messy extract
  processed/             cleaned parquet + scored output
src/
  generate_data.py       synthetic data with realistic mess baked in
  prepare_data.py        clean, validate, feature-engineer
  warehouse.py           DuckDB + the named SQL runner
  risk_engine.py         config-driven train + score
  sql/analytics.sql      the analytical queries
app/
  streamlit_app.py       the dashboard
models/                  saved model
```

The student data is synthetic — I generated it, so there are no real student records in here.
