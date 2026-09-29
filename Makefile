.PHONY: help install dev up down logs test format lint type-check clean docker-build docker-logs

help:
	@echo "Maritime AI System - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install         - Install Python dependencies"
	@echo "  make dev-setup       - Setup development environment"
	@echo ""
	@echo "Docker:"
	@echo "  make up              - Start Docker services"
	@echo "  make down            - Stop Docker services"
	@echo "  make docker-build    - Build Docker image"
	@echo "  make docker-logs     - View Docker logs"
	@echo ""
	@echo "Development:"
	@echo "  make format          - Format code with Black"
	@echo "  make lint            - Run flake8 linter"
	@echo "  make type-check      - Run mypy type checking"
	@echo "  make test            - Run pytest tests"
	@echo "  make test-cov        - Run tests with coverage"
	@echo ""
	@echo "Database:"
	@echo "  make db-init         - Initialize database"
	@echo "  make db-shell        - Open database shell"
	@echo "  make db-backup       - Backup database"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean           - Clean temporary files"
	@echo "  make status          - Show service status"
	@echo "  make run             - Run application locally"
	@echo ""

install:
	pip install -r requirements.txt

dev-setup: install
	cp .env.example .env
	@echo "✓ Development environment setup complete!"

up:
	docker-compose up -d
	@echo "✓ Services started"
	sleep 5
	make status

down:
	docker-compose down
	@echo "✓ Services stopped"

docker-build:
	docker-compose build --no-cache
	@echo "✓ Docker image built"

docker-logs:
	docker-compose logs -f

logs:
	docker-compose logs -f api

status:
	@docker-compose ps

test:
	pytest -v

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term-missing

format:
	black app/ tests/ *.py --line-length=100
	@echo "✓ Code formatted"

lint:
	flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503
	@echo "✓ Linting complete"

type-check:
	mypy app/ --ignore-missing-imports
	@echo "✓ Type checking complete"

quality: format lint type-check
	@echo "✓ Code quality checks complete"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✓ Cleaned up temporary files"

db-init:
	docker-compose exec api python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
	@echo "✓ Database initialized"

db-shell:
	docker-compose exec postgres psql -U maritime_user -d maritime_ai

db-backup:
	docker-compose exec postgres pg_dump -U maritime_user maritime_ai > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✓ Database backed up"

run:
	python main.py

health-check:
	@curl -s http://localhost:8000/health | python -m json.tool
	@echo ""

api-docs:
	@echo "Opening API documentation..."
	@python -m webbrowser http://localhost:8000/docs || echo "Visit http://localhost:8000/docs"

all-checks: clean format lint type-check test
	@echo "✓ All checks passed!"

.DEFAULT_GOAL := help
