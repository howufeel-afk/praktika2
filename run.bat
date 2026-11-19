@echo off
echo === Running Unit Tests ===
py -m unittest discover -s tests -p "test_*.py"
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo === Demo 1 (Stages 1-3, 5): Cargo Package Analysis & PlantUML Visualization ===
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output app_graph.png

echo.
echo === Demo 2 (Stage 3, 5): Test Repo with Cyclic Dependencies ===
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt --output cycle_graph.png

echo.
echo === Demo 3 (Stage 3): Test Repo with Substring Filter (filter=TEST) ===
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST --output diamond_filtered.png

echo.
echo === Demo 4 (Stage 4): Reverse Dependencies Mode ===
py -m src.main --package D --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --reverse --output reverse_d.png
