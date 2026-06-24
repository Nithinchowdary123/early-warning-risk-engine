"""
streamlit_app.py — Early-Warning Risk Engine dashboard.

Run locally:  streamlit run app/streamlit_app.py
Deploy:       push to GitHub -> share.streamlit.io -> point at this file.

The app is config-driven: titles, the entity label ("Student" / "Well"), and
the risk thresholds all come from config.yaml, so the same dashboard re-skins
for a different domain without code changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
import yaml

# make src importable when Streamlit runs from the repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.warehouse import run_query  # noqa: E402

CFG = yaml.safe_load((ROOT / "config.yaml").read_text())
ENTITY = CFG["domain"]["entity_label"]
EVENT = CFG["domain"]["event_label"]

st.set_page_config(page_title=CFG["domain"]["display_title"], layout="wide")

BAND_COLORS = {"High": "#d62728", "Medium": "#ff7f0e", "Low": "#2ca02c"}


@st.cache_data
def load_scored() -> pd.DataFrame:
    return pd.read_parquet(ROOT / CFG["paths"]["scored_data"])


@st.cache_resource
def load_model() -> dict:
    return joblib.load(ROOT / CFG["paths"]["model"])


df = load_scored()
bundle = load_model()
model, features, importance = bundle["model"], bundle["features"], bundle["importance"]

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title(f"🎯 {CFG['domain']['display_title']}")
st.caption(
    f"A config-driven early-warning engine that scores every **{ENTITY.lower()}** "
    f"by risk of **{EVENT.lower()}** so teams can intervene early. "
    "The same pipeline re-points at any entity (e.g. predictive maintenance, "
    "production-decline monitoring) by editing `config.yaml`."
)

# -----------------------------------------------------------------------------
# KPI row (from SQL)
# -----------------------------------------------------------------------------
kpis = run_query("overall_kpis").iloc[0]
high_n = int((df["risk_band"] == "High").sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Total {ENTITY}s", f"{int(kpis.total_students):,}")
c2.metric(f"{EVENT} rate", f"{kpis.not_retained_pct:.1f}%")
c3.metric("Avg GPA", f"{kpis.avg_gpa:.2f}")
c4.metric("⚠️ High-risk flagged", f"{high_n:,}")

st.divider()

# -----------------------------------------------------------------------------
# Two-column analytics
# -----------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Risk concentrates in the least-engaged")
    dec = run_query("engagement_decile_retention")
    fig = px.bar(
        dec, x="engagement_decile", y="not_retained_pct",
        labels={"engagement_decile": "Engagement decile (1=lowest)",
                "not_retained_pct": f"{EVENT} %"},
        color="not_retained_pct", color_continuous_scale="Reds",
    )
    fig.update_layout(coloraxis_showscale=False, height=340)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Top risk drivers (model feature importance)")
    imp = importance.head(8).sort_values("importance")
    fig = px.bar(imp, x="importance", y="feature", orientation="h")
    fig.update_layout(height=340, xaxis_title="Relative importance", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

left2, right2 = st.columns(2)
with left2:
    st.subheader("Risk band distribution")
    band_counts = (
        df["risk_band"].value_counts().reindex(["High", "Medium", "Low"]).reset_index()
    )
    band_counts.columns = ["risk_band", "count"]
    fig = px.pie(band_counts, names="risk_band", values="count", hole=0.5,
                 color="risk_band", color_discrete_map=BAND_COLORS)
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)

with right2:
    st.subheader(f"{EVENT} rate by program")
    major = run_query("risk_by_major")
    fig = px.bar(major.sort_values("not_retained_pct"), x="not_retained_pct", y="major",
                 orientation="h", color="not_retained_pct",
                 color_continuous_scale="Reds")
    fig.update_layout(coloraxis_showscale=False, height=320,
                      xaxis_title=f"{EVENT} %", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# Watchlist — the actionable output
# -----------------------------------------------------------------------------
st.subheader(f"🚨 Intervention watchlist — highest-risk {ENTITY.lower()}s")
st.caption("This is the 'so what': a ranked, exportable list to act on.")
band_filter = st.multiselect("Show bands", ["High", "Medium", "Low"], default=["High"])
watch = (
    df[df["risk_band"].isin(band_filter)]
    .sort_values("risk_score", ascending=False)
    [["student_id", "risk_score", "risk_band", "current_gpa",
      "assignment_submit_rate", "lms_logins_per_week", "major"]]
    .head(200)
)
st.dataframe(watch, use_container_width=True, height=300)
st.download_button(
    "⬇️ Download watchlist (CSV)",
    watch.to_csv(index=False).encode(),
    file_name="watchlist.csv", mime="text/csv",
)

st.divider()

# -----------------------------------------------------------------------------
# Live what-if scoring — the interactive ML piece
# -----------------------------------------------------------------------------
st.subheader("🔮 Live risk score — what-if tool")
st.caption(
    f"Adjust the inputs to see how the model's predicted {EVENT.lower()} risk "
    "changes in real time. (This is what a BI dashboard alone can't do.)"
)

sc1, sc2, sc3 = st.columns(3)
inputs = {}
with sc1:
    inputs["current_gpa"] = st.slider("Current GPA", 0.0, 4.0, 2.5, 0.1)
    inputs["prior_gpa"] = st.slider("Prior GPA", 0.0, 4.0, 3.0, 0.1)
    inputs["midterm_score"] = st.slider("Midterm score", 0.0, 100.0, 70.0, 1.0)
with sc2:
    inputs["assignment_submit_rate"] = st.slider("Submit rate", 0.0, 1.0, 0.7, 0.05)
    inputs["lms_logins_per_week"] = st.slider("LMS logins / week", 0.0, 30.0, 8.0, 0.5)
    inputs["avg_days_late"] = st.slider("Avg days late", 0.0, 30.0, 3.0, 0.5)
with sc3:
    inputs["credit_load"] = st.selectbox("Credit load", [6, 9, 12, 15, 18], index=2)
    inputs["commute_distance_mi"] = st.slider("Commute (mi)", 0.0, 60.0, 8.0, 1.0)
    inputs["financial_aid_flag"] = int(st.checkbox("Receives financial aid", True))
    inputs["first_gen_flag"] = int(st.checkbox("First-generation student", False))

row = pd.DataFrame([inputs])[features]
prob = float(model.predict_proba(row)[:, 1][0])
hi, med = CFG["risk_bands"]["high"], CFG["risk_bands"]["medium"]
label = "High" if prob >= hi else ("Medium" if prob >= med else "Low")

m1, m2 = st.columns([1, 2])
m1.metric(f"Predicted {EVENT.lower()} risk", f"{prob:.0%}", label)
gauge = px.bar(x=[prob], y=[""], orientation="h", range_x=[0, 1])
gauge.update_traces(marker_color=BAND_COLORS[label])
gauge.update_layout(height=120, showlegend=False, xaxis_title="risk probability",
                    yaxis_title="", margin=dict(l=0, r=0, t=10, b=0))
m2.plotly_chart(gauge, use_container_width=True)

st.divider()
st.markdown(
    f"""
    **Why this matters for the role:** swap `config.yaml` from *student / not-retained*
    to *well / production-decline* (or *pump / failure*) and this exact engine becomes
    a predictive-maintenance and production-monitoring tool — same ingest → validate →
    feature-engineer → score → rank → monitor architecture. Model ROC-AUC:
    **{bundle['auc']:.3f}**.
    """
)
