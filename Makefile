.PHONY: test run-cargo-mock run-cycle run-filter run-live

test:
	python3 -m unittest discover -s tests -p "test_*.py"

run-cargo-mock:
	python3 -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output app_graph.png

run-cycle:
	python3 -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt

run-filter:
	python3 -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST

run-live:
	python3 -m src.main --package serde_json --version 1.0.100 --repo https://index.crates.io
