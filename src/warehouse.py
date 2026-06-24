"""
warehouse.py
-------------
Loads the cleaned extract into a DuckDB warehouse and exposes the named
queries in src/sql/analytics.sql so both the CLI and the dashboard can reuse
the exact same SQL.

Run:  python src/warehouse.py            # (re)build warehouse + print KPIs
Use:  from src.warehouse import run_query
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pandas as pd
import yaml

with open("config.yaml") as fh:
    CFG = yaml.safe_load(fh)

SQL_FILE = Path("src/sql/analytics.sql")


def build_warehouse() -> None:
    """Load the clean parquet into a persistent DuckDB table called `students`."""
    db = CFG["paths"]["duckdb"]
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db)
    con.execute("DROP TABLE IF EXISTS students")
    con.execute(
        "CREATE TABLE students AS SELECT * FROM read_parquet(?)",
        [CFG["paths"]["clean_data"]],
    )
    n = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    con.close()
    print(f"Warehouse built: {n:,} rows in `students` -> {db}")


def _parse_named_queries() -> dict[str, str]:
    """Split analytics.sql into {name: sql} using the `-- :name foo` markers."""
    text = SQL_FILE.read_text()
    blocks = re.split(r"-- :name\s+(\w+)", text)
    # blocks = [preamble, name1, sql1, name2, sql2, ...]
    queries: dict[str, str] = {}
    for i in range(1, len(blocks), 2):
        queries[blocks[i].strip()] = blocks[i + 1].strip()
    return queries


QUERIES = _parse_named_queries()


def run_query(name: str) -> pd.DataFrame:
    """Run a named query from analytics.sql against the cleaned data.

    Uses an in-memory DuckDB with a view over the clean parquet rather than the
    persisted .duckdb file. This keeps the dashboard portable (no version-locked
    binary to commit) while running the *exact* SQL from analytics.sql.
    """
    if name not in QUERIES:
        raise KeyError(f"Unknown query '{name}'. Available: {list(QUERIES)}")
    parquet = Path(CFG["paths"]["clean_data"]).resolve().as_posix()
    con = duckdb.connect(":memory:")
    try:
        con.execute(
            f"CREATE VIEW students AS SELECT * FROM read_parquet('{parquet}')"
        )
        return con.execute(QUERIES[name]).df()
    finally:
        con.close()


def main() -> None:
    build_warehouse()
    print(f"\nNamed queries available: {list(QUERIES)}\n")
    print("=== overall_kpis ===")
    print(run_query("overall_kpis").to_string(index=False))
    print("\n=== risk_by_major ===")
    print(run_query("risk_by_major").to_string(index=False))
    print("\n=== engagement_decile_retention ===")
    print(run_query("engagement_decile_retention").to_string(index=False))


if __name__ == "__main__":
    main()
