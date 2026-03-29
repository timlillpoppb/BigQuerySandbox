.PHONY: help install deps build test docs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	./.venv/Scripts/python.exe -m pip install -r requirements.txt

deps: ## Install dbt packages
	./.venv/Scripts/python.exe -m dbt.cli.main deps

build: ## Build all models
	./.venv/Scripts/python.exe -m dbt.cli.main build

test: ## Run all tests
	./.venv/Scripts/python.exe -m dbt.cli.main test

docs: ## Generate documentation
	./.venv/Scripts/python.exe -m dbt.cli.main docs generate

clean: ## Clean target directory
	rm -rf target/