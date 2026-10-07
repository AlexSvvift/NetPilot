.PHONY: install run test format docker-up

install:
	python -m pip install -r requirements.txt

run:
	python -m uvicorn app.main:app --reload

test:
	python -m pytest

format:
	python -m ruff check . --fix

docker-up:
	docker compose up --build
