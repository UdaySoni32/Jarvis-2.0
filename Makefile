.PHONY: help setup install install-sys-deps install-dev dev test lint format clean run run-api docker-build docker-run

help:
	@echo "JARVIS 2.0 - Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Initial project setup"
	@echo "  make install-sys-deps - Install system deps (portaudio, etc.) via apt-get"
	@echo "  make install        - Install dependencies"
	@echo "  make install-dev    - Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Run in development mode"
	@echo "  make run            - Run CLI"
	@echo "  make run-api        - Run API server"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make test-watch     - Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make type-check     - Run type checker"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make docs           - Generate documentation"

setup:
	@echo "Setting up JARVIS 2.0..."
	python3 -m venv venv
	@echo "Virtual environment created!"
	@echo "Activate it with: source venv/bin/activate"
	@echo "Then run: make install"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "Dependencies installed!"

install-sys-deps:
	@echo "Installing system dependencies for pyaudio (PortAudio)..."
	sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-dev build-essential
	@echo "System dependencies installed! Now run: make install"

install-dev:
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	@echo "Dev dependencies installed!"

dev:
	python -m src.cli --debug

run:
	python -m src.cli

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-watch:
	pytest-watch tests/ -v

lint:
	@echo "Running linters..."
	ruff check src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	@echo "Clean complete!"

docs:
	mkdocs build

docs-serve:
	mkdocs serve

docker-build:
	docker build -t jarvis-2.0:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

init-db:
	alembic upgrade head

pre-commit:
	pre-commit install
	pre-commit run --all-files
