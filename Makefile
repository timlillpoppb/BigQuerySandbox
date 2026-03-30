.PHONY: help install deps build test docs clean
.PHONY: run run-full run-bronze run-silver run-gold
.PHONY: test-bronze test-silver test-gold test-data test-schema
.PHONY: build-full build-bronze build-silver build-gold
.PHONY: compile snapshot seed source-freshness
.PHONY: debug parse list docs-serve
.PHONY: state-modified state-modified-plus

# Cross-platform dbt executable selection.
# On Windows PowerShell, make may not be installed, and path separators are backslashes.
DBT_EXE := ./.venv/Scripts/dbt.exe
PYTHON_EXE := ./.venv/Scripts/python.exe
ifeq ($(OS),Windows_NT)
  # Absolute path expressed in Windows separators (e.g. C:\Users\...\dbt.exe)
  DBT_EXE := $(subst /,\\,$(CURDIR))\\.venv\\Scripts\\dbt.exe
  PYTHON_EXE := $(subst /,\\,$(CURDIR))\\.venv\\Scripts\\python.exe
endif

help: ## Show this help
	@echo "Available make commands:"
	@echo "  build           - Build all models (run + test)"
	@echo "  test            - Run all tests"
	@echo "  run             - Run all models"
	@echo "  docs            - Generate documentation"
	@echo "  deps            - Install dbt packages"
	@echo "  clean           - Clean target directory"
	@echo "  version         - Show dbt version"
	@echo ""
	@echo "Layer-specific commands:"
	@echo "  run-bronze, run-silver, run-gold"
	@echo "  build-bronze, build-silver, build-gold"
	@echo "  test-bronze, test-silver, test-gold"
	@echo ""
	@echo "Environment commands:"
	@echo "  run-target-dev, run-target-staging, run-target-prod"
	@echo "  test-target-dev, test-target-staging, test-target-prod"
	@echo "  build-target-dev, build-target-staging, build-target-prod"
	@echo ""
	@echo "State-based commands:"
	@echo "  state-modified, state-modified-plus, state-build-modified"
	@echo ""
	@echo "Custom selection:"
	@echo "  run-select SELECT=model, test-select SELECT=model, build-select SELECT=model"
	@echo ""
	@echo "Streamlit BI Dashboard:"
	@echo "  streamlit-restart - Kill, clear cache, and restart Streamlit fresh"
	@echo ""
	@echo "GitHub PR & Deployment:"
	@echo "  pr-and-merge    - Create PR, validate CI/CD, auto-merge to master and deploy"
	@echo "                   (Requires: GITHUB_TOKEN environment variable)"
	@echo "  pr-status       - Monitor deployment progress"
	@echo ""
	@echo "Other commands: compile, snapshot, seed, source-freshness, debug, parse, list, docs-serve"

install: ## Install Python dependencies
	$(PYTHON_EXE) -m pip install -r requirements.txt

deps: ## Install dbt packages
	$(DBT_EXE) deps

# ===== RUN COMMANDS =====
run: ## Run all models
	$(DBT_EXE) run

run-full: ## Run all models with full refresh
	$(DBT_EXE) run --full-refresh

run-bronze: ## Run bronze layer models
	$(DBT_EXE) run --select bronze

run-silver: ## Run silver layer models
	$(DBT_EXE) run --select silver

run-gold: ## Run gold layer models
	$(DBT_EXE) run --select gold

run-staging: ## Run staging models
	$(DBT_EXE) run --select stg_*

run-facts: ## Run fact tables
	$(DBT_EXE) run --select fact_*

run-dims: ## Run dimension tables
	$(DBT_EXE) run --select dim_*

run-incremental: ## Run incremental models only
	$(DBT_EXE) run --select config.materialized:incremental

# ===== BUILD COMMANDS =====
build: ## Build all models (run + test)
	$(DBT_EXE) build

build-full: ## Build all models with full refresh
	$(DBT_EXE) build --full-refresh

build-bronze: ## Build bronze layer
	$(DBT_EXE) build --select bronze

build-silver: ## Build silver layer
	$(DBT_EXE) build --select silver

build-gold: ## Build gold layer
	$(DBT_EXE) build --select gold

# ===== TEST COMMANDS =====
test: ## Run all tests
	$(DBT_EXE) test

test-data: ## Run data tests only
	$(DBT_EXE) test --data

test-schema: ## Run schema tests only
	$(DBT_EXE) test --schema

test-bronze: ## Test bronze layer
	$(DBT_EXE) test --select bronze

test-silver: ## Test silver layer
	$(DBT_EXE) test --select silver

test-gold: ## Test gold layer
	$(DBT_EXE) test --select gold

# ===== STATE-BASED COMMANDS (CI/CD) =====
state-modified: ## Run modified models since last state
	$(DBT_EXE) run --select state:modified

state-modified-plus: ## Run modified models + downstream
	$(DBT_EXE) run --select state:modified+

state-test-modified: ## Test modified models
	$(DBT_EXE) test --select state:modified

state-build-modified: ## Build modified models + downstream
	$(DBT_EXE) build --select state:modified+

# ===== OTHER DBT COMMANDS =====
compile: ## Compile all models (dry run)
	$(DBT_EXE) compile

snapshot: ## Update all snapshots
	$(DBT_EXE) snapshot

seed: ## Load seed data
	$(DBT_EXE) seed

source-freshness: ## Check source data freshness
	$(DBT_EXE) source freshness

debug: ## Debug dbt configuration
	$(DBT_EXE) debug

parse: ## Parse project and validate
	$(DBT_EXE) parse

list: ## List all models
	$(DBT_EXE) list

docs: ## Generate documentation
	$(DBT_EXE) docs generate

docs-serve: ## Serve docs locally
	$(DBT_EXE) docs serve

# ===== UTILITY COMMANDS =====
clean: ## Clean target directory
	rm -rf target/

version: ## Show dbt version
	$(DBT_EXE) --version

# ===== CUSTOM SELECT COMMANDS =====
# Usage: make run-select SELECT="my_model"
run-select: ## Run specific model(s) - usage: make run-select SELECT="my_model"
	$(DBT_EXE) run --select $(SELECT)

test-select: ## Test specific model(s) - usage: make test-select SELECT="my_model"
	$(DBT_EXE) test --select $(SELECT)

build-select: ## Build specific model(s) - usage: make build-select SELECT="my_model"
	$(DBT_EXE) build --select $(SELECT)

# ===== ENVIRONMENT TARGETS =====
# Usage: make run-target-dev, make run-target-staging, make run-target-prod
run-target-dev: ## Run in dev environment
	$(DBT_EXE) run --target dev

run-target-staging: ## Run in staging environment
	$(DBT_EXE) run --target staging

run-target-prod: ## Run in prod environment
	$(DBT_EXE) run --target prod

test-target-dev: ## Test in dev environment
	$(DBT_EXE) test --target dev

test-target-staging: ## Test in staging environment
	$(DBT_EXE) test --target staging

test-target-prod: ## Test in prod environment
	$(DBT_EXE) test --target prod

build-target-dev: ## Build in dev environment
	$(DBT_EXE) build --target dev

build-target-staging: ## Build in staging environment
	$(DBT_EXE) build --target staging

build-target-prod: ## Build in prod environment
	$(DBT_EXE) build --target prod

# ===== STREAMLIT BI DASHBOARD =====
streamlit-restart: ## Kill Streamlit, clear cache, and restart fresh
	powershell -Command "Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force; Remove-Item -Path $$env:USERPROFILE\.streamlit\cache -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path $$env:USERPROFILE\.streamlit\secrets -Recurse -Force -ErrorAction SilentlyContinue; cd \"$(CURDIR)\"; .\.venv\Scripts\streamlit.exe run bi/0_TheLook_Analytics_Platform.py"

# ===== GITHUB PR & DEPLOYMENT =====
pr-and-merge: ## Create PR, validate CI/CD checks, auto-merge to master and deploy
	@if not defined GITHUB_TOKEN (echo ERROR: GITHUB_TOKEN not set & echo Run: set GITHUB_TOKEN=your_token_here & exit /b 1)
	$(PYTHON_EXE) scripts/pr_and_merge.py

pr-status: ## Check status of current PR (requires gh CLI)
	@echo Use: make pr-and-merge to automate, or visit PR manually
