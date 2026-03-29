.PHONY: help install deps build test docs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

deps: ## Install dbt packages
	dbt deps

build: ## Build all models
	dbt build

test: ## Run all tests
	dbt test

docs: ## Generate documentation
	dbt docs generate

clean: ## Clean target directory
	rm -rf target/