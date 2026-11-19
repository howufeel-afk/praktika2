.PHONY: test run-cargo-mock run-cycle run-filter run-reverse run-live

test:
	python3 -m unittest discover -s tests -p "test_*.py"

run-cargo-mock:
	python3 -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output app_graph.png

run-cycle:
	python3 -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt --output cycle_graph.png

run-filter:
	python3 -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST --output diamond_filtered.png

run-reverse:
	python3 -m src.main --package D --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --reverse --output reverse_d.png

run-live:
	python3 -m src.main --package quote --version 1.0.35 --repo https://index.crates.io --output quote_graph.png
