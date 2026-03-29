.PHONY: help install deps build test docs clean
.PHONY: run run-full run-bronze run-silver run-gold
.PHONY: test-bronze test-silver test-gold test-data test-schema
.PHONY: build-full build-bronze build-silver build-gold
.PHONY: compile snapshot seed source-freshness
.PHONY: debug parse list docs-serve
.PHONY: state-modified state-modified-plus

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
	@echo "Other commands: compile, snapshot, seed, source-freshness, debug, parse, list, docs-serve"

install: ## Install Python dependencies
	./.venv311/Scripts/python.exe -m pip install -r requirements.txt

deps: ## Install dbt packages
	./.venv311/Scripts/dbt.exe deps

# ===== RUN COMMANDS =====
run: ## Run all models
	./.venv311/Scripts/dbt.exe run

run-full: ## Run all models with full refresh
	./.venv311/Scripts/dbt.exe run --full-refresh

run-bronze: ## Run bronze layer models
	./.venv311/Scripts/dbt.exe run --select bronze

run-silver: ## Run silver layer models
	./.venv311/Scripts/dbt.exe run --select silver

run-gold: ## Run gold layer models
	./.venv311/Scripts/dbt.exe run --select gold

run-staging: ## Run staging models
	./.venv311/Scripts/dbt.exe run --select stg_*

run-facts: ## Run fact tables
	./.venv311/Scripts/dbt.exe run --select fact_*

run-dims: ## Run dimension tables
	./.venv311/Scripts/dbt.exe run --select dim_*

run-incremental: ## Run incremental models only
	./.venv311/Scripts/dbt.exe run --select config.materialized:incremental

# ===== BUILD COMMANDS =====
build: ## Build all models (run + test)
	./.venv311/Scripts/dbt.exe build

build-full: ## Build all models with full refresh
	./.venv311/Scripts/dbt.exe build --full-refresh

build-bronze: ## Build bronze layer
	./.venv311/Scripts/dbt.exe build --select bronze

build-silver: ## Build silver layer
	./.venv311/Scripts/dbt.exe build --select silver

build-gold: ## Build gold layer
	./.venv311/Scripts/dbt.exe build --select gold

# ===== TEST COMMANDS =====
test: ## Run all tests
	./.venv311/Scripts/dbt.exe test

test-data: ## Run data tests only
	./.venv311/Scripts/dbt.exe test --data

test-schema: ## Run schema tests only
	./.venv311/Scripts/dbt.exe test --schema

test-bronze: ## Test bronze layer
	./.venv311/Scripts/dbt.exe test --select bronze

test-silver: ## Test silver layer
	./.venv311/Scripts/dbt.exe test --select silver

test-gold: ## Test gold layer
	./.venv311/Scripts/dbt.exe test --select gold

# ===== STATE-BASED COMMANDS (CI/CD) =====
state-modified: ## Run modified models since last state
	./.venv311/Scripts/dbt.exe run --select state:modified

state-modified-plus: ## Run modified models + downstream
	./.venv311/Scripts/dbt.exe run --select state:modified+

state-test-modified: ## Test modified models
	./.venv311/Scripts/dbt.exe test --select state:modified

state-build-modified: ## Build modified models + downstream
	./.venv311/Scripts/dbt.exe build --select state:modified+

# ===== OTHER DBT COMMANDS =====
compile: ## Compile all models (dry run)
	./.venv311/Scripts/dbt.exe compile

snapshot: ## Update all snapshots
	./.venv311/Scripts/dbt.exe snapshot

seed: ## Load seed data
	./.venv311/Scripts/dbt.exe seed

source-freshness: ## Check source data freshness
	./.venv311/Scripts/dbt.exe source freshness

debug: ## Debug dbt configuration
	./.venv311/Scripts/dbt.exe debug

parse: ## Parse project and validate
	./.venv311/Scripts/dbt.exe parse

list: ## List all models
	./.venv311/Scripts/dbt.exe list

docs: ## Generate documentation
	./.venv311/Scripts/dbt.exe docs generate

docs-serve: ## Serve docs locally
	./.venv311/Scripts/dbt.exe docs serve

# ===== UTILITY COMMANDS =====
clean: ## Clean target directory
	rm -rf target/

version: ## Show dbt version
	./.venv311/Scripts/dbt.exe --version

# ===== CUSTOM SELECT COMMANDS =====
# Usage: make run-select SELECT="my_model"
run-select: ## Run specific model(s) - usage: make run-select SELECT="my_model"
	./.venv311/Scripts/dbt.exe run --select $(SELECT)

test-select: ## Test specific model(s) - usage: make test-select SELECT="my_model"
	./.venv311/Scripts/dbt.exe test --select $(SELECT)

build-select: ## Build specific model(s) - usage: make build-select SELECT="my_model"
	./.venv311/Scripts/dbt.exe build --select $(SELECT)

# ===== ENVIRONMENT TARGETS =====
# Usage: make run-target-dev, make run-target-staging, make run-target-prod
run-target-dev: ## Run in dev environment
	./.venv311/Scripts/dbt.exe run --target dev

run-target-staging: ## Run in staging environment
	./.venv311/Scripts/dbt.exe run --target staging

run-target-prod: ## Run in prod environment
	./.venv311/Scripts/dbt.exe run --target prod

test-target-dev: ## Test in dev environment
	./.venv311/Scripts/dbt.exe test --target dev

test-target-staging: ## Test in staging environment
	./.venv311/Scripts/dbt.exe test --target staging

test-target-prod: ## Test in prod environment
	./.venv311/Scripts/dbt.exe test --target prod

build-target-dev: ## Build in dev environment
	./.venv311/Scripts/dbt.exe build --target dev

build-target-staging: ## Build in staging environment
	./.venv311/Scripts/dbt.exe build --target staging

build-target-prod: ## Build in prod environment
	./.venv311/Scripts/dbt.exe build --target prod