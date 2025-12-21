.PHONY: run test lint fmt migrate heads

ENV ?= .env

run:
	uvicorn focus.backend.app:app --reload

test:
	pytest -q

lint:
	ruff check .

fmt:
	ruff format .

migrate:
	PYTHONPATH=$$PWD alembic upgrade head

heads:
	PYTHONPATH=$$PWD alembic heads
