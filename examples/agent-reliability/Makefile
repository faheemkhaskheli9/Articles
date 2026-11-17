.PHONY: install test lint demo build check
install:
	python -m pip install -r requirements-dev.txt

test:
	python -m pytest -q

lint:
	ruff check .

demo:
	python -m agent_reliability --json

build:
	python scripts/build_site.py

check: lint test
	python scripts/build_site.py --check
