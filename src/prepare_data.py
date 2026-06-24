"""
prepare_data.py
----------------
Clean + validate the raw extract, then engineer model features.

This is the "data validation / data quality" stage from the resume, made
concrete:  de-duplicate, standardize messy categoricals, drop impossible
values, impute sensibly, and engineer a few derived signals.

Run:  python src/prepare_data.py
In :  data/raw/students.csv
Out:  data/processed/students_clean.parquet
"""
from __future__ import annotations

import pandas as pd
import yaml

with open("config.yaml") as fh:
    CFG = yaml.safe_load(fh)


# --- standardization helpers -------------------------------------------------
MAJOR_MAP = {
    "comp sci": "Computer Science", "cs": "Computer Science",
    "computer science": "Computer Science",
    "business admin": "Business", "bus": "Business", "business": "Business",
    "psych": "Psychology", "psychology": "Psychology",
}


def _standardize_major(s: pd.Series) -> pd.Series:
    cleaned = s.str.strip().str.lower()
    return cleaned.map(MAJOR_MAP).fillna(s.str.strip().str.title())


def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    report = {"start_rows": len(df)}

    # 1) drop exact duplicate records
    df = df.drop_duplicates().copy()
    report["after_dedupe"] = len(df)

    # 2) standardize categoricals
    df["major"] = _standardize_major(df["major"])
    df["term"] = df["term"].str.strip().str.title()

    # 3) range validation — GPA must be within 0–4
    invalid_gpa = (df["current_gpa"] > 4.0) | (df["current_gpa"] < 0)
    df = df.loc[~invalid_gpa].copy()
    report["dropped_invalid_gpa"] = int(invalid_gpa.sum())

    # 4) impute missing values
    #    - numeric performance/engagement -> median (robust to outliers)
    #    - submit_rate -> median; commute -> median
    for col in ["midterm_score", "prior_gpa", "assignment_submit_rate",
                "commute_distance_mi"]:
        med = df[col].median()
        n_missing = int(df[col].isna().sum())
        df[col] = df[col].fillna(med)
        report[f"imputed_{col}"] = n_missing

    report["final_rows"] = len(df)
    _print_report(report)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derived signals that tend to sharpen early-warning models."""
    df = df.copy()
    # momentum: are they trending down vs their own baseline?
    df["gpa_delta"] = (df["current_gpa"] - df["prior_gpa"]).round(2)
    # engagement intensity normalized by course load
    df["logins_per_credit"] = (
        df["lms_logins_per_week"] / df["credit_load"].clip(lower=1)
    ).round(3)
    # combined disengagement flag (cheap, interpretable)
    df["low_engagement"] = (
        (df["assignment_submit_rate"] < 0.6)
        & (df["lms_logins_per_week"] < 5)
    ).astype(int)
    return df


def _print_report(r: dict) -> None:
    print("Data-quality report")
    print("-" * 40)
    print(f"  rows in                : {r['start_rows']:,}")
    print(f"  duplicates removed     : {r['start_rows'] - r['after_dedupe']:,}")
    print(f"  invalid GPAs dropped   : {r['dropped_invalid_gpa']:,}")
    for k, v in r.items():
        if k.startswith("imputed_"):
            print(f"  imputed {k[8:]:<22}: {v:,}")
    print(f"  rows out               : {r['final_rows']:,}")
    print("-" * 40)


def main() -> None:
    raw = pd.read_csv(CFG["paths"]["raw_data"])
    clean = validate_and_clean(raw)
    feat = engineer_features(clean)
    out = CFG["paths"]["clean_data"]
    feat.to_parquet(out, index=False)
    print(f"Wrote {len(feat):,} clean rows ({feat.shape[1]} cols) -> {out}")


if __name__ == "__main__":
    main()
