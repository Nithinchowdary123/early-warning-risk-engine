"""
risk_engine.py
---------------
The reusable, config-driven Early-Warning Risk Engine.

NOTHING in this file is student-specific — every column name, the target, and
the risk thresholds come from config.yaml. Point the config at well-production
data and the same engine scores wells instead of students. That portability is
the whole pitch.

Pipeline:  load features -> train/test split -> Gradient Boosting -> evaluate
           -> score every entity -> assign High/Medium/Low risk band -> save.

Run:  python src/risk_engine.py
Out:  models/risk_model.joblib, data/processed/students_scored.parquet
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

with open("config.yaml") as fh:
    CFG = yaml.safe_load(fh)


def feature_columns() -> list[str]:
    """Flatten the grouped feature lists in config into one ordered list."""
    cols: list[str] = []
    for group in CFG["features"].values():
        cols.extend(group)
    return cols


def band(prob: np.ndarray) -> np.ndarray:
    """Map probabilities to High / Medium / Low using config thresholds."""
    hi = CFG["risk_bands"]["high"]
    med = CFG["risk_bands"]["medium"]
    out = np.where(prob >= hi, "High", np.where(prob >= med, "Medium", "Low"))
    return out


def train_and_score() -> dict:
    df = pd.read_parquet(CFG["paths"]["clean_data"])
    feats = feature_columns()
    target = CFG["target"]["column"]

    X = df[feats]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=CFG["model"]["test_size"],
        random_state=CFG["model"]["random_state"],
        stratify=y,
    )

    model = GradientBoostingClassifier(random_state=CFG["model"]["random_state"])
    model.fit(X_train, y_train)

    # --- evaluation ---------------------------------------------------------
    proba_test = model.predict_proba(X_test)[:, 1]
    pred_test = (proba_test >= 0.5).astype(int)
    auc = roc_auc_score(y_test, proba_test)

    print("Model evaluation")
    print("=" * 48)
    print(f"  ROC-AUC: {auc:.3f}")
    print("\n  Classification report (threshold 0.5):")
    print(classification_report(y_test, pred_test,
                                target_names=["Retained", "Not Retained"]))
    print("  Confusion matrix [rows=actual, cols=pred]:")
    print(confusion_matrix(y_test, pred_test))

    # --- feature importance -------------------------------------------------
    importance = (
        pd.DataFrame({"feature": feats, "importance": model.feature_importances_})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    print("\n  Top risk drivers:")
    print(importance.head(6).to_string(index=False))

    # --- score the full population & band ------------------------------------
    df = df.copy()
    df["risk_score"] = model.predict_proba(X)[:, 1].round(4)
    df["risk_band"] = band(df["risk_score"].values)

    # --- persist -------------------------------------------------------------
    joblib.dump(
        {"model": model, "features": feats, "importance": importance, "auc": auc},
        CFG["paths"]["model"],
    )
    df.to_parquet(CFG["paths"]["scored_data"], index=False)

    band_counts = df["risk_band"].value_counts().reindex(["High", "Medium", "Low"])
    print("\n  Population risk banding:")
    print(band_counts.to_string())
    print(f"\nSaved model -> {CFG['paths']['model']}")
    print(f"Saved scored population -> {CFG['paths']['scored_data']}")

    return {"auc": auc, "importance": importance}


if __name__ == "__main__":
    train_and_score()
