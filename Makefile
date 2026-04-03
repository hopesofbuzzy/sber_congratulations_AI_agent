.PHONY: setup run test lint format

setup:
	cd backend && python3 -m venv .venv && \
	. .venv/bin/activate && \
	pip install -r requirements.txt -r requirements-dev.txt && \
	cp env.example .env

run:
	cd backend && PYTHONPATH=. .venv/bin/python -m app.worker.run_dev_server

test:
	cd backend && .venv/bin/pytest -q

lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/black --check .

format:
	cd backend && .venv/bin/black .
