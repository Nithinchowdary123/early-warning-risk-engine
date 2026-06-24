"""
run_pipeline.py — one command to rebuild everything from scratch.

    python run_pipeline.py

Runs: generate data -> clean + engineer -> build warehouse -> train + score.
After this, launch the dashboard with:  streamlit run app/streamlit_app.py
"""
import subprocess
import sys

STEPS = [
    ("Generate raw data", "src/generate_data.py"),
    ("Clean + engineer features", "src/prepare_data.py"),
    ("Build DuckDB warehouse", "src/warehouse.py"),
    ("Train model + score population", "src/risk_engine.py"),
]


def main() -> None:
    for i, (label, script) in enumerate(STEPS, 1):
        print(f"\n{'='*60}\n[{i}/{len(STEPS)}] {label}\n{'='*60}")
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"\n❌ Step failed: {script}")
            sys.exit(result.returncode)
    print("\n✅ Pipeline complete. Launch the dashboard with:")
    print("   streamlit run app/streamlit_app.py")


if __name__ == "__main__":
    main()
