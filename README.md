# Cargo Dependency Visualizer (Вариант 25)

Инструмент визуализации графа зависимостей для пакетов Rust (Cargo), реализованный на стандартной библиотеке Python без использования сторонних менеджеров пакетов и библиотек.

## 1. Общее описание и структура проекта

- `src/config.py` — модель конфигурации `AppConfig` и функции валидации параметров.
- `src/cli.py` — парсер аргументов командной строки и вывод конфигурации в формате ключ-значение.
- `src/cargo.py` — загрузка данных Cargo Sparse Index (`index.crates.io`) и парсер тестового репозитория.
- `src/graph.py` — построение транзитивного графа зависимостей алгоритмом BFS без рекурсии с обработкой циклов и фильтрацией.
- `src/main.py` — основная точка входа CLI-приложения.
- `tests/` — модульные тесты (`unittest`) и тестовые графы (`mock_index.jsonl`, `repo_cycle.txt`, `repo_diamond.txt`).
- `run.bat`, `run.sh`, `Makefile` — скрипты запуска тестов и демонстрационных сценариев.

## 2. Настраиваемые параметры (CLI-опции)

- `--package` — имя анализируемого пакета (обязательный).
- `--version` — версия пакета в формате SemVer (обязательный).
- `--repo` — URL-адрес репозитория или путь к файлу тестового репозитория (по умолчанию `https://index.crates.io`).
- `--test-mode` — флаг включения режима работы с тестовым репозиторием.
- `--output` — имя сгенерированного файла с изображением графа (по умолчанию `graph.png`).
- `--filter` — подстрока для фильтрации пакетов (по умолчанию пустая).

## 3. Команды для сборки и запуска тестов

Автоматический запуск всех 16 модульных тестов и демонстрационных сценариев (Windows):
```cmd
run.bat
```

Запуск всех тестов вручную:
```cmd
py -m unittest discover -s tests -p "test_*.py"
```

Запуск тестов по отдельным этапам:
```cmd
py -m unittest tests/test_cli.py
py -m unittest tests/test_cargo.py
py -m unittest tests/test_graph.py
```

## 4. Примеры использования (по этапам и пунктам задания)

### Этап 1. Минимальный прототип с конфигурацией

**Пункт 3. Вывод всех настраиваемых параметров в формате ключ-значение:**
```cmd
py -c "from src.cli import parse_arguments, print_config_key_value; print_config_key_value(parse_arguments(['--package', 'serde', '--version', '1.0.104']))"
```

**Пункт 4. Демонстрация обработки ошибок для всех параметров:**
```cmd
py -m src.main --package "123!bad" --version 1.0.0
py -m src.main --package serde --version latest
py -m src.main --package serde --version 1.0.0 --repo ftp://wrong.url
py -m src.main --package serde --version 1.0.0 --test-mode --repo no_file.txt
py -m src.main --package serde --version 1.0.0 --output graph.exe
```

### Этап 2. Сбор данных

**Пункты 2–4. Извлечение и вывод прямых зависимостей заданной версии (офлайн мок-файл и онлайн `crates.io`):**
```cmd
py -c "from src.cargo import get_crate_dependencies; print('\n'.join(f'- {d.name} ({d.requirement})' for d in get_crate_dependencies('tests/mock_index.jsonl', 'app', '1.0.0', True)))"
py -c "from src.cargo import get_crate_dependencies; print('\n'.join(f'- {d.name} ({d.requirement})' for d in get_crate_dependencies('https://index.crates.io', 'serde', '1.0.104', False)))"
```

### Этап 3. Основные операции (BFS без рекурсии)

**Пункт 2. Фильтрация пакетов по подстроке (`--filter`):**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
py -m src.main --package BTEST --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
```

**Пункт 3. Обработка циклических зависимостей:**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt
```

**Пункт 4. Режим тестирования (заглавные латинские буквы) и анализ реального пакета:**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt
py -m src.main --package serde --version 1.0.104 --repo https://index.crates.io
```

### Проверка истории коммитов (Пункт 5 каждого этапа)

```cmd
git log --oneline
```
