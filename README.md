# Cargo Dependency Visualizer (Вариант 25)

Инструмент визуализации графа зависимостей для пакетов Rust (Cargo).
Реализованы Этапы 1, 2 и 3.

## Структура проекта
- `src/config.py` — модель конфигурации и валидация параметров.
- `src/cli.py` — парсер аргументов командной строки.
- `src/cargo.py` — загрузка и парсинг метаданных Cargo Sparse Index и тестовых репозиториев.
- `src/graph.py` — построение транзитивного графа зависимостей алгоритмом BFS без рекурсии.
- `src/main.py` — точка входа CLI-приложения.
- `tests/` — модульные тесты и тестовые графы репозиториев (`repo_cycle.txt`, `repo_diamond.txt`).
- `run.bat`, `run.sh`, `Makefile` — скрипты запуска тестов и демонстрационных сценариев.

## Запуск тестов и демонстраций (Windows)
```cmd
run.bat
```

Или по отдельности:
```cmd
py -m unittest discover -s tests -p "test_*.py"
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
```
