.PHONY: run test lint fmt migrate heads
SHELL := /usr/bin/bash
ENV ?= .env

run:
	set -a; source ./$(ENV); set +a; uvicorn focus.backend.app:app --reload

test:
	set -a; source ./$(ENV); set +a; pytest -q
# 	pytest -q

lint:
	ruff check .

fmt:
	ruff format .

migrate:
	set -a; source ./$(ENV); set +a; PYTHONPATH=$$PWD alembic upgrade head

heads:
	PYTHONPATH=$$PWD alembic heads
