.PHONY: install dev test lint format docker-build docker-run seed clean

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

seed:
	python sample_data.py

docker-build:
	docker build -t ai-sql-assistant:latest .

docker-run:
	docker run --rm -p 8000:8000 \
	  -e ANTHROPIC_API_KEY=$$ANTHROPIC_API_KEY \
	  ai-sql-assistant:latest

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -name "*.pyc" -delete
