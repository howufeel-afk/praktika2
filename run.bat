@echo off
echo === Running Unit Tests ===
py -m unittest discover -s tests -p "test_*.py"
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo === Case 1: Cyclic Graph (A -> B -> C -> A) ===
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt

echo.
echo === Case 2: Diamond Graph with Substring Filter (filter=TEST) ===
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
