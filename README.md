# Cargo Dependency Visualizer (Вариант 25)

Инструмент визуализации графа зависимостей для пакетов Rust (Cargo).
Реализация Этапов 1 и 2 в рамках практической работы по конфигурационному управлению.

## Структура проекта
- `src/` — исходный код приложения (валидация, CLI, парсер Cargo Sparse Index).
- `tests/` — модульные тесты и мок-данные для автономной проверки.
- `Makefile`, `run.sh` — сценарии запуска тестов и демонстрации.

## Требования
- Python 3.8+ (только стандартная библиотека, никаких сторонних pip-пакетов).

## Запуск тестов
```bash
make test
# или
python3 -m unittest discover -s tests -p "test_*.py"
```

## Примеры запуска

### 1. Этап 1: вывод конфигурации и проверка ошибок
```bash
python3 -m src.main --package serde --version 1.0.104
```

### 2. Этап 2: получение прямых зависимостей в тестовом режиме (офлайн)
```bash
python3 -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl
```

### 3. Этап 2: получение прямых зависимостей из официального индекса crates.io
```bash
python3 -m src.main --package serde --version 1.0.104 --repo https://index.crates.io
```
