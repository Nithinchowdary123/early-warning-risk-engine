# Deployment guide

Get a public, résumé-ready URL in a few minutes.

## 1. Put the repo on GitHub

```bash
# from the project root
git init
git add .
git commit -m "Early-Warning Risk Engine: end-to-end analytics product"

# create an empty repo on github.com first (e.g. early-warning-risk-engine), then:
git branch -M main
git remote add origin https://github.com/Nithinchowdary123/early-warning-risk-engine.git
git push -u origin main
```

> The committed `data/processed/*.parquet` and `models/*.joblib` let the app run
> on the cloud without regenerating anything. The DuckDB binary is git-ignored and
> rebuilt in-memory at query time.

## 2. Deploy on Streamlit Community Cloud (free)

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **New app**.
3. Select your repo, branch `main`, and set **Main file path** to:
   ```
   app/streamlit_app.py
   ```
4. Click **Deploy**. First build installs `requirements.txt` (~2 min).
5. Copy the resulting `https://<app>.streamlit.app` URL into:
   - your résumé (under the project),
   - the **Live demo** section of `README.md`.

## 3. (Optional) Add a Power BI companion

To also show the BI tool on your résumé:
- Import `data/processed/students_scored.parquet` into Power BI Desktop.
- Recreate the watchlist + risk-by-program visuals.
- Publish to Power BI Service and link it in the README.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` on cloud | confirm the package is in `requirements.txt` |
| App can't find data | ensure `data/processed/*.parquet` and `models/*.joblib` were committed (not git-ignored) |
| Model load error | the cloud sklearn version must match `requirements.txt` (pinned to `1.3.2`) |
