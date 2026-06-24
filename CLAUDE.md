# Project guide

Early-Warning Risk Engine: a config-driven pipeline that cleans data, runs SQL
analytics, trains a risk model, and serves a Streamlit dashboard. Demoed on
student retention; switches domains by editing `config.yaml` only.

## Commands

Always activate the venv first: `source .venv/bin/activate`

| Task | Command |
|---|---|
| Install deps | `pip install -r requirements.txt` |
| Rebuild everything | `python run_pipeline.py` |
| Run dashboard | `streamlit run app/streamlit_app.py` |
| Regenerate raw data only | `python src/generate_data.py` |
| Clean + features only | `python src/prepare_data.py` |
| Build warehouse + run SQL | `python src/warehouse.py` |
| Train + score only | `python src/risk_engine.py` |
| Smoke-test the app | `python -c "from streamlit.testing.v1 import AppTest; print(len(AppTest.from_file('app/streamlit_app.py').run().exception))"` (expect 0) |

## How it's wired

- `config.yaml` is the single source of truth. Code reads features, target,
  paths, and risk thresholds from it. To change domains, edit this, not the code.
- Pipeline order: `generate_data.py` -> `prepare_data.py` -> `warehouse.py` ->
  `risk_engine.py` -> dashboard reads the outputs.
- Data flow: `data/raw/students.csv` (messy) -> `data/processed/students_clean.parquet`
  -> `data/processed/students_scored.parquet` + `models/risk_model.joblib`.
- SQL lives in `src/sql/analytics.sql` as `-- :name <query>` blocks; `warehouse.run_query("<name>")`
  runs them against the clean parquet via an in-memory DuckDB.

## Conventions / gotchas

- `.venv/` and `data/processed/warehouse.duckdb` are git-ignored. The parquet
  files and `models/*.joblib` ARE committed so the deployed app works.
- Don't parameterize DuckDB `CREATE VIEW` (it errors); the path is inlined in
  `warehouse.run_query`.
- Data is synthetic, generated with a fixed seed (42) for reproducibility.
- Keep sklearn pinned to the version in `requirements.txt` so the committed
  model loads on Streamlit Cloud.

## Deploy

Streamlit Community Cloud, main file `app/streamlit_app.py`, branch `main`.
Full steps in `DEPLOY.md`.
