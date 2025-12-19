.PHONY: help install dev run docker-build docker-up docker-down test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

dev: ## Install development dependencies
	. venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

run: ## Run the service locally
	. venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the service in production mode
	. venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

test: ## Run tests
	. venv/bin/activate && pytest tests/ -v

test-cov: ## Run tests with coverage
	. venv/bin/activate && pytest tests/ -v --cov=app --cov-report=html

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

setup: ## Run setup script
	./setup.sh

format: ## Format code with black
	. venv/bin/activate && black app/ tests/

lint: ## Lint code with flake8
	. venv/bin/activate && flake8 app/ tests/

check: lint test ## Run linting and tests
