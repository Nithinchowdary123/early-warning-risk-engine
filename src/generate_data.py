"""
generate_data.py
-----------------
Creates a realistic, intentionally-messy student-success dataset.

Why synthetic? It is reproducible (anyone can clone the repo and regenerate),
it carries NO real student PII, and it lets us bake in *genuine* predictive
signal so the model has something real to learn — while still injecting the
kind of mess (missing values, duplicates, inconsistent labels, outliers) that
a real analyst has to clean before any modeling can happen.

Run:  python src/generate_data.py
Out:  data/raw/students.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 15_000


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def build_clean_frame() -> pd.DataFrame:
    """Generate the underlying *clean* signal before we dirty it up."""
    # --- context / demographics ---------------------------------------------
    first_gen = RNG.binomial(1, 0.34, N)
    financial_aid = RNG.binomial(1, 0.55, N)
    commute = np.clip(RNG.exponential(8, N), 0, 60).round(1)
    credit_load = RNG.choice([6, 9, 12, 15, 18], N, p=[0.05, 0.12, 0.33, 0.38, 0.12])

    # --- academic baseline ---------------------------------------------------
    prior_gpa = np.clip(RNG.normal(3.0, 0.5, N), 0.0, 4.0).round(2)

    # --- engagement (correlated with prior_gpa + noise) ---------------------
    base = (prior_gpa - 3.0)
    lms_logins = np.clip(RNG.normal(8 + base * 3, 3, N), 0, 30).round(1)
    submit_rate = np.clip(_sigmoid(base * 1.5 + RNG.normal(0.8, 0.6, N)), 0, 1).round(3)
    days_late = np.clip(RNG.exponential(2.5, N) - base * 1.5, 0, 30).round(1)

    # --- current-term performance -------------------------------------------
    midterm = np.clip(
        55 + base * 12 + (submit_rate - 0.5) * 30 + RNG.normal(0, 8, N), 0, 100
    ).round(1)
    current_gpa = np.clip(
        prior_gpa * 0.6 + (midterm / 100) * 4 * 0.4 + RNG.normal(0, 0.25, N), 0, 4
    ).round(2)

    df = pd.DataFrame(
        {
            "student_id": np.arange(100000, 100000 + N),
            "lms_logins_per_week": lms_logins,
            "assignment_submit_rate": submit_rate,
            "avg_days_late": days_late,
            "current_gpa": current_gpa,
            "midterm_score": midterm,
            "prior_gpa": prior_gpa,
            "credit_load": credit_load,
            "financial_aid_flag": financial_aid,
            "first_gen_flag": first_gen,
            "commute_distance_mi": commute,
        }
    )

    # --- latent risk -> outcome ---------------------------------------------
    # Higher risk when: low engagement, poor performance, first-gen, long commute.
    logit = (
        -1.0
        + (8 - df.lms_logins_per_week) * 0.10
        + (0.7 - df.assignment_submit_rate) * 2.5
        + df.avg_days_late * 0.06
        + (2.6 - df.current_gpa) * 1.1
        + (65 - df.midterm_score) * 0.015
        + df.first_gen_flag * 0.45
        + df.commute_distance_mi * 0.015
        - df.financial_aid_flag * 0.20
    )
    prob = _sigmoid(logit)
    df["not_retained"] = RNG.binomial(1, np.clip(prob, 0.01, 0.97))

    # categorical context (kept clean here; we dirty it below)
    majors = ["Computer Science", "Biology", "Business", "Psychology",
              "Engineering", "Nursing", "History"]
    df["major"] = RNG.choice(majors, N)
    df["term"] = RNG.choice(["Fall 2024", "Spring 2025", "Fall 2025"], N)
    return df


def add_realistic_mess(df: pd.DataFrame) -> pd.DataFrame:
    """Inject the kind of data-quality problems a real analyst has to handle."""
    df = df.copy()

    # 1) Inconsistent categorical labels (the classic dirty-data headache)
    major_aliases = {
        "Computer Science": ["Computer Science", "Comp Sci", "CS", "computer science"],
        "Business": ["Business", "Business Admin", "BUS"],
        "Psychology": ["Psychology", "Psych"],
    }
    for canonical, variants in major_aliases.items():
        mask = df["major"] == canonical
        df.loc[mask, "major"] = RNG.choice(variants, mask.sum())

    # 2) Missing values scattered through engagement/performance columns
    for col, frac in [
        ("midterm_score", 0.06),
        ("commute_distance_mi", 0.04),
        ("prior_gpa", 0.03),
        ("assignment_submit_rate", 0.05),
    ]:
        idx = RNG.choice(df.index, int(len(df) * frac), replace=False)
        df.loc[idx, col] = np.nan

    # 3) Duplicate rows (double-entered records)
    dupes = df.sample(120, random_state=1)
    df = pd.concat([df, dupes], ignore_index=True)

    # 4) A few impossible/outlier values to be validated out
    bad = RNG.choice(df.index, 25, replace=False)
    df.loc[bad, "current_gpa"] = 5.5  # GPA can't exceed 4.0

    # 5) Whitespace + case noise in term labels
    df.loc[RNG.choice(df.index, 200, replace=False), "term"] = " fall 2025 "

    # shuffle so dupes/bad rows aren't all at the bottom
    return df.sample(frac=1, random_state=7).reset_index(drop=True)


def main() -> None:
    clean = build_clean_frame()
    messy = add_realistic_mess(clean)
    out = "data/raw/students.csv"
    messy.to_csv(out, index=False)
    rate = clean["not_retained"].mean()
    print(f"Wrote {len(messy):,} rows -> {out}")
    print(f"True not-retained rate (clean): {rate:.1%}")
    print(f"Injected: {messy.isna().any(axis=1).sum():,} rows with missing values, "
          f"120 duplicates, 25 invalid GPAs")


if __name__ == "__main__":
    main()
