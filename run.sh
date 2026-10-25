#!/usr/bin/env bash
set -e
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl
