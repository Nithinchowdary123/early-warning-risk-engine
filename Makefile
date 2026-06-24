# Short commands. Run `make <target>`. Activate the venv first: source .venv/bin/activate

.PHONY: help setup build run data clean-data warehouse model test

help:            ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

setup:           ## install dependencies
	pip install -r requirements.txt

build:           ## rebuild the whole pipeline (data -> clean -> warehouse -> model)
	python run_pipeline.py

run:             ## launch the dashboard
	streamlit run app/streamlit_app.py

data:            ## regenerate raw data only
	python src/generate_data.py

clean-data:      ## clean + feature-engineer only
	python src/prepare_data.py

warehouse:       ## build warehouse + print SQL results
	python src/warehouse.py

model:           ## train + score only
	python src/risk_engine.py

test:            ## smoke-test that the dashboard renders (expect 0)
	python -c "from streamlit.testing.v1 import AppTest; print('exceptions:', len(AppTest.from_file('app/streamlit_app.py').run().exception))"
