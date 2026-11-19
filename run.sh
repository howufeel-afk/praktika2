#!/usr/bin/env bash
set -e
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output app_graph.png
python3 -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt --output cycle_graph.png
python3 -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST --output diamond_filtered.png
python3 -m src.main --package D --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --reverse --output reverse_d.png
