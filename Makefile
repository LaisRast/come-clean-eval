.DEFAULT_GOAL := help

MODEL ?= openrouter/openai/gpt-5.6-sol
EPOCHS ?= 1

.PHONY: help install eval eval-all page deploy check-models view clean

help:
	@echo "Targets:"
	@echo "  install       Sync dependencies with uv (incl. dev + scripts extras)"
	@echo "  eval          Run one model (MODEL, EPOCHS overridable)"
	@echo "  eval-all      Run the full model registry (scripts/models.py)"
	@echo "  page          Build public/index.html from logs/ and docs/methodology.md"
	@echo "  deploy        Build the page and push it to the gh-pages branch"
	@echo "  check-models  Verify REGISTRY entries against OpenRouter's model list"
	@echo "  view          Open Inspect's log viewer"
	@echo "  clean         Remove all logs under logs/ (careful: deletes trial data)"
	@echo ""
	@echo "Examples:"
	@echo "  make eval"
	@echo "  make eval MODEL=openrouter/anthropic/claude-haiku-4.5 EPOCHS=10"

install:
	uv sync --extra dev --extra scripts

eval:
	uv run inspect eval src/comeclean/task.py \
		--model $(MODEL) --epochs $(EPOCHS) \
		--timeout 60 --max-retries 2

eval-all:
	uv run python scripts/run_evals.py --epochs $(EPOCHS)

page:
	uv run python scripts/build_page.py

deploy: page
	./scripts/deploy.sh

check-models:
	uv run python scripts/check_models.py

view:
	uv run inspect view start

clean:
	rm -rf logs/*
