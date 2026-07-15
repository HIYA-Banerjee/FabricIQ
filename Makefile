.PHONY: setup lint format seed train evaluate backend frontend dev test docker-build docker-up docker-down clean

setup:
	@echo "Installing python packages..."
	pip install -r backend/requirements.txt
	@echo "Installing node packages..."
	cd frontend && npm install

lint:
	@echo "Linting python files..."
	flake8 backend || true
	@echo "Linting frontend files..."
	cd frontend && npm run lint || true

format:
	@echo "Formatting backend..."
	black backend || true

seed:
	@echo "Seeding database..."
	python -c "from app.db.session import SessionLocal; from app.simulator.factory_simulator import seed_database; db = SessionLocal(); seed_database(db, 'factory_alpha'); seed_database(db, 'factory_beta'); db.close()"

train:
	@echo "Training models..."
	python -m app.ml.training

evaluate:
	@echo "Evaluating metrics..."
	python -c "import json; print(json.dumps(json.load(open('model_metrics.json')), indent=2))"

backend:
	@echo "Launching FastAPI server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Launching Next.js client..."
	cd frontend && npm run dev

dev:
	@echo "Starting development environment..."
	make -j 2 backend frontend

test:
	@echo "Running backend test suite..."
	pytest backend/tests

docker-build:
	@echo "Building docker containers..."
	docker compose build

docker-up:
	@echo "Launching docker compose stack..."
	docker compose up -d

docker-down:
	@echo "Stopping docker compose stack..."
	docker compose down

clean:
	@echo "Cleaning cache files..."
	rm -rf backend/__pycache__ backend/app/__pycache__ backend/app/*/__pycache__
	rm -rf .pytest_cache model_metrics.json loomsense.db test.db
