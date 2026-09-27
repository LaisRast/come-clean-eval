.DEFAULT_GOAL := help

MODEL ?= openrouter/openai/gpt-5.6-sol
EPOCHS ?= 1

.PHONY: help install eval eval-all page deploy check-models view clean

# Scratch checkout for the gh-pages branch. Removed again on the way out, even
# if a step fails, so a botched deploy does not leave a worktree behind.
GH_PAGES_WORKTREE ?= /tmp/come-clean-gh-pages

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
	@set -e; \
	git rev-parse --verify gh-pages >/dev/null 2>&1 || { \
		echo "No gh-pages branch. Create one once with:"; \
		echo "  git switch --orphan gh-pages && git commit --allow-empty -m init"; \
		echo "  git push -u origin gh-pages && git switch main"; \
		exit 1; \
	}; \
	git worktree remove --force $(GH_PAGES_WORKTREE) >/dev/null 2>&1 || true; \
	git worktree prune; \
	trap 'git worktree remove --force $(GH_PAGES_WORKTREE) >/dev/null 2>&1 || true' EXIT; \
	git worktree add $(GH_PAGES_WORKTREE) gh-pages; \
	cp public/index.html $(GH_PAGES_WORKTREE)/index.html; \
	git -C $(GH_PAGES_WORKTREE) add index.html; \
	if git -C $(GH_PAGES_WORKTREE) diff --cached --quiet; then \
		echo "Page unchanged since last deploy."; \
	else \
		git -C $(GH_PAGES_WORKTREE) commit -m "deploy: $$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
		git -C $(GH_PAGES_WORKTREE) push; \
	fi

check-models:
	uv run python scripts/check_models.py

view:
	uv run inspect view start

clean:
	rm -rf logs/*
