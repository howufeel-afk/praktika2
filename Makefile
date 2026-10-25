.PHONY: test run-mock run-live

test:
	python3 -m unittest discover -s tests -p "test_*.py"

run-mock:
	python3 -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl

run-live:
	python3 -m src.main --package serde --version 1.0.104 --repo https://index.crates.io
