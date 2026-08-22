# ask-boston — RAG the City, Aug 22 2026, Track A
# Quickstart:  make setup && make data && make split && make prove

.DEFAULT_GOAL := help
VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

CORPUS  := lab0_boston/corpus/docs
Q_LAB   := lab0_boston/questions.json      # 24 Fort Point questions (fiction, calibrated)
Q_REAL  := eval/questions_boston.json      # 10 real-data questions (verified in pandas)
LIMIT   := 2000                            # rows per CSV — MUST match on both sides

.PHONY: help setup data split tables prove ask baseline-ask ask-real baseline-ask-real \
        freeze-baseline ingest score-before score-after \
        score-before-real score-after-real compare demo clean-index

help: ## Show every target
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-19s %s\n", $$1, $$2}'

# -- setup ------------------------------------------------------------------

setup: ## venv + dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

data: ## Download 311 + Food Inspections from Analyze Boston (CKAN-resolved)
	$(PY) boston/download.py

split: ## Regenerate the 11 Fort Point documents from the full corpus
	$(PY) -m baseline.split_corpus --input lab0_boston/corpus/fortpoint_full.md --outdir $(CORPUS)

# -- the two indexes, kept apart on purpose ---------------------------------

freeze-baseline: ## Build the FROZEN control-group index. ONCE. Never again
	$(PY) -m baseline.freeze --limit $(LIMIT)

ingest: ## Build OUR index over the real CSVs — rebuild this freely
	$(PY) boston/ingest.py --limit $(LIMIT)

clean-index: ## Drop OUR indexes only — never touches .chroma/baseline
	rm -rf .chroma/civic .chroma/boston
	@echo "our indexes cleared; the frozen baseline is untouched"

# -- fast signal ------------------------------------------------------------

tables: ## Show every CSV registered in DuckDB (no model needed)
	$(PY) -m civic.tables

prove: ## No-LLM proof that computed answers are exact — run this first
	$(PY) -m eval.prove

ask: ## Ask our pipeline: make ask Q="..."
	$(PY) -m civic.pipeline "$(Q)"

baseline-ask: ## The same question, naively (Fort Point): make baseline-ask Q="..."
	$(PY) -m baseline.naive_rag --corpus-dir $(CORPUS) --collection fortpoint_naive "$(Q)"

ask-real: ## THE DEMO. Ask ours over live Boston data: make ask-real Q="..."
	$(PY) -m civic.pipeline --collection boston_open_data "$(Q)"

baseline-ask-real: ## THE DEMO. Same question, naive baseline over live Boston data
	$(PY) -m baseline.naive_boston "$(Q)"

# -- the measurement --------------------------------------------------------
# Suite 1: Fort Point, 24 questions. Fiction, but calibrated — verified ground
# truth in DESIGN_NOTES.md and pre-written distractors. This is the regression
# suite and the headline before/after number.

score-before: ## Baseline over the 24 Fort Point questions -> eval/results/before.txt
	$(PY) -m eval.judge --pipeline baseline.naive_rag --questions $(Q_LAB) \
	  --collection fortpoint_naive --save eval/results/before.txt

score-after: ## Ours over the same 24, same judge -> eval/results/after.txt
	$(PY) -m eval.judge --pipeline civic.pipeline --questions $(Q_LAB) \
	  --save eval/results/after.txt

# Suite 2: the real 311 export, 10 questions, each ground truth verified in
# pandas. Proves it works on the data we actually submit.

score-before-real: ## Frozen baseline over the 10 real-data questions
	$(PY) -m eval.judge --pipeline baseline.naive_boston --questions $(Q_REAL) \
	  --collection baseline_frozen --save eval/results/before_real.txt

score-after-real: ## Ours over the 10 real-data questions
	$(PY) -m eval.judge --pipeline civic.pipeline --questions $(Q_REAL) \
	  --collection boston_open_data --save eval/results/after_real.txt

compare: ## before vs after, per question. This is the final slide
	@$(PY) -m eval.compare
	@echo
	@$(PY) -m eval.compare --before eval/results/before_real.txt --after eval/results/after_real.txt 2>/dev/null || true

demo: ## The Streamlit demo surface
	$(VENV)/bin/streamlit run app/app_streamlit.py
