.PHONY: help test test-python test-node test-deno test-browser test-sql test-all setup-python setup-node setup-local teardown-local format format-python format-js lint lint-python lint-js check clean

# Default target
help:
	@echo "Community Calendar Test Suite"
	@echo ""
	@echo "Targets:"
	@echo "  make test            - Run Python + node (vitest) + Deno tests"
	@echo "  make test-python     - Run Python tests (pytest via uv)"
	@echo "  make test-node       - Run node seam tests (vitest via pnpm)"
	@echo "  make test-deno       - Run edge-function tests (Deno: my-picks dedupe)"
	@echo "  make test-browser    - Run browser groups (Playwright over xmlui/test.html)"
	@echo "  make test-sql        - Run database tests (local Supabase via pgTAP)"
	@echo "  make format          - Auto-format Python + JS code"
	@echo "  make format-python   - Auto-format Python code (ruff format)"
	@echo "  make format-js       - Auto-format JS code (prettier --write + eslint --fix)"
	@echo "  make lint            - Lint Python + JS code"
	@echo "  make lint-python     - Lint Python code (ruff check; type checkers gate)"
	@echo "  make lint-js         - Lint JS code (prettier --check + eslint)"
	@echo "  make check           - Run lint + Python + node tests"
	@echo "  make setup-python    - Create venv and install dependencies (uv sync)"
	@echo "  make setup-node      - Install JS dependencies (pnpm install)"
	@echo "  make setup-local     - Start local Supabase and apply schema"
	@echo "  make teardown-local  - Stop local Supabase"
	@echo "  make clean           - Clean test artifacts"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - uv (install with: curl -LsSf https://astral.sh/uv/install.sh | sh)"
	@echo "  - Supabase CLI installed (for database tests)"
	@echo "  - PostgreSQL client (psql) for local database access"

# Run default tests
test: test-python test-node test-deno

# Alias for test
test-all: test

# Setup Python environment with uv
setup-python:
	@echo "Setting up Python environment with uv..."
	@uv sync
	@echo "✓ Dependencies installed"
	@echo ""
	@echo "Activate venv with: source .venv/bin/activate"

# Run Python tests
test-python:
	@echo "Running Python tests..."
	@uv run env -u PYTHONPATH pytest tests/ -v --ignore=tests/js

# Setup node dependencies with pnpm
setup-node:
	@echo "Setting up node environment with pnpm..."
	@pnpm install
	@echo "✓ Node dependencies installed"

# Run node seam tests (vitest; browser + bench stay manual/CI-only)
test-node:
	@echo "Running node tests..."
	@pnpm vitest run

# Run edge-function tests (Deno; not covered by pytest or vitest)
test-deno:
	@echo "Running Deno tests..."
	@deno test supabase/functions/my-picks/dedupe_test.ts supabase/functions/load-events/scope_test.ts

# Run browser groups (requires playwright browsers: pnpm exec playwright install chromium)
test-browser:
	@echo "Running browser tests..."
	@pnpm playwright test

# Auto-format Python + JS code
format: format-python format-js

# Auto-format Python code
format-python:
	@echo "Formatting Python code..."
	@uv run ruff format .
	@echo "✓ Formatted"

# Auto-format JS code (prettier owns style, eslint --fix owns correctness)
format-js:
	@echo "Formatting JS code..."
	@pnpm run format:js
	@echo "✓ Formatted"

# Lint Python + JS code
lint: lint-python lint-js

# Lint JS code. Prettier (format) + ESLint (recommended) gate.
lint-js:
	@echo "Linting JS code..."
	@pnpm run lint:js
	@echo "✓ JS clean"

# Lint Python code. Ruff (format + check) and all four type checkers gate.
# `uv sync` runs first so a stale venv (e.g. after removing a dependency) can't
# mask diagnostics with leftover installed packages — the checkers must resolve
# against the exact lockfile state, not whatever uv run leaves behind.
lint-python:
	@echo "Syncing environment to lockfile..."
	@uv sync --quiet
	@echo "✓ environment synced"
	@echo ""
	@echo "Running ruff format check..."
	@uv run ruff format --check .
	@echo "✓ ruff formatted"
	@echo ""
	@echo "Running ruff check..."
	@uv run ruff check .
	@echo "✓ ruff clean"
	@echo ""
	@echo "Running type checkers..."
	@status=0; \
	for checker in "pyright" "ty check" "pyrefly check --min-severity warn" "zuban mypy ."; do \
		echo "  → $$checker"; \
		uv run $$checker >/tmp/cc-lint-$$(echo $$checker | tr ' ' '_').log 2>&1 || status=$$?; \
		tail -2 /tmp/cc-lint-$$(echo $$checker | tr ' ' '_').log | sed 's/^/    /'; \
	done; \
	echo ""; \
	if [ $$status -ne 0 ]; then \
		echo "❌ Type checkers reported diagnostics (gating)."; \
	else \
		echo "✓ Type checkers clean"; \
	fi; \
	exit $$status

# Lint + tests
check: lint test-python test-node test-deno

# Run database tests (requires prepared local Supabase project DB)
test-sql:
	@echo "Running database tests..."
	@if ! supabase status > /dev/null 2>&1; then \
		echo "ERROR: Local Supabase is not running."; \
		echo "Run: make setup-local"; \
		exit 1; \
	fi
	@supabase test db supabase/tests/

# Setup local Supabase environment
setup-local:
	@echo "Starting local Supabase..."
	supabase start
	@echo "Applying migrations..."
	supabase db reset
	@echo ""
	@echo "✓ Local environment ready"
	@echo "Run: make test-sql"

# Teardown local Supabase
teardown-local:
	@echo "Stopping local Supabase..."
	supabase stop

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"
