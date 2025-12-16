.PHONY: help setup install test lint format clean docker-up docker-down migrate seed

help:
	@echo "Autonomous Compliance Platform - Available Commands:"
	@echo ""
	@echo "  setup          - Complete project setup"
	@echo "  install        - Install all dependencies"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linters"
	@echo "  format         - Format code"
	@echo "  clean          - Clean build artifacts"
	@echo "  docker-up      - Start Docker containers"
	@echo "  docker-down    - Stop Docker containers"
	@echo "  migrate        - Run database migrations"
	@echo "  seed           - Seed database with initial data"
	@echo "  dev            - Start development servers"
	@echo ""

setup: install migrate
	@echo "✓ Setup complete!"

install:
	@echo "Installing backend dependencies..."
	cd backend && python3 -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ Dependencies installed"

test:
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest
	@echo "✓ Tests complete"

lint:
	@echo "Running linters..."
	cd backend && . venv/bin/activate && \
		flake8 app --max-line-length=120 || true
	@echo "✓ Linting complete"

format:
	@echo "Formatting code..."
	cd backend && . venv/bin/activate && \
		black app --line-length=120 || true
	@echo "✓ Formatting complete"

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.pytest_cache
	rm -rf frontend/build frontend/node_modules/.cache
	@echo "✓ Cleanup complete"

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "✓ Containers started"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "✓ Containers stopped"

migrate:
	@echo "Running database migrations..."
	cd backend && . venv/bin/activate && alembic upgrade head
	@echo "✓ Migrations complete"

seed:
	@echo "Seeding database..."
	cd backend && . venv/bin/activate && python scripts/seed_db.py
	@echo "✓ Database seeded"

dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Run 'make docker-up' for containerized setup"
