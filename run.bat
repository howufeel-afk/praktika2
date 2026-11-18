@echo off
echo === Running Unit Tests ===
py -m unittest discover -s tests -p "test_*.py"
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo === Demo 1: Cargo Package Analysis (Offline Mock Index) ===
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output app_graph.png

echo.
echo === Demo 2: Test Repo with Cyclic Dependencies ===
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt

echo.
echo === Demo 3: Test Repo with Substring Filter (filter=TEST) ===
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
