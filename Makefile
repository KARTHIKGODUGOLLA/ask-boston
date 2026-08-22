# ask-boston — RAG the City, Aug 22 2026
# Quickstart:  make setup && make data && make split && make prove

.DEFAULT_GOAL := help
VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

CORPUS := lab0_boston/corpus/docs
QUESTIONS := lab0_boston/questions.json

.PHONY: help setup data split ask baseline-ask prove score-before score-after compare demo clean-index

help: ## Show every target
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

setup: ## venv + dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

data: ## Download 311 + Food Inspections from Analyze Boston (CKAN-resolved)
	$(PY) boston/download.py

split: ## Regenerate the 11 Fort Point documents from the full corpus
	$(PY) -m baseline.split_corpus --input lab0_boston/corpus/fortpoint_full.md --outdir $(CORPUS)

tables: ## Show every CSV registered in DuckDB (no model needed)
	$(PY) -m civic.tables

prove: ## No-LLM proof that computed answers are exact — run this first
	$(PY) -m eval.prove

ask: ## Ask our pipeline: make ask Q="..."
	$(PY) -m civic.pipeline "$(Q)"

baseline-ask: ## Ask the naive baseline the same question: make baseline-ask Q="..."
	$(PY) -m baseline.naive_rag --corpus-dir $(CORPUS) --collection fortpoint_naive "$(Q)"

score-before: ## Grade the naive baseline over all 24 questions -> eval/results/before.txt
	$(PY) -m eval.judge --pipeline baseline.naive_rag --save eval/results/before.txt

score-after: ## Grade OUR pipeline, same judge and questions -> eval/results/after.txt
	$(PY) -m eval.judge --pipeline civic.pipeline --save eval/results/after.txt

compare: ## Print before vs after side by side
	@$(PY) -m eval.compare

demo: ## The Streamlit demo surface
	$(VENV)/bin/streamlit run app/app_streamlit.py

clean-index: ## Drop both chroma stores (do this after changing chunking)
	rm -rf .chroma
	@echo "chroma cleared — next query rebuilds both indexes"
