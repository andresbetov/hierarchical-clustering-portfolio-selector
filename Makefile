.PHONY: install test run run-debug clean help

help:
	@echo "Hierarchical Clustering Portfolio Selector — Common Tasks"
	@echo ""
	@echo "  make install    Install dependencies via uv"
	@echo "  make test       Run the offline test suite (pytest)"
	@echo "  make run        Run full portfolio analysis (downloads data)"
	@echo "  make run-debug  Run with DEBUG logging"
	@echo "  make clean      Remove cache, charts, build artifacts"
	@echo ""

install:
	uv sync

test:
	uv run python -m pytest

run:
	uv run scripts/assets-investment.py

run-debug:
	LOG_LEVEL=DEBUG uv run scripts/assets-investment.py

clean:
	rm -rf __pycache__ .ruff_cache .pytest_cache charts/*.png *.pyc
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.nbc" -o -name "*.nbi" | xargs rm -f 2>/dev/null || true

