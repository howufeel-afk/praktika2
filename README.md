# Cargo Dependency Visualizer (Вариант 25)

CLI-инструмент анализа и визуализации графа зависимостей пакетов Rust (Cargo), разработанный с использованием только стандартной библиотеки Python без сторонних библиотек и менеджеров пакетов.

## 1. Общее описание и структура проекта

- `src/config.py` — модель конфигурации `AppConfig` и валидация всех 6 пользовательских параметров.
- `src/cli.py` — парсер опций командной строки (`argparse`) и вывод параметров в формате `ключ: значение`.
- `src/cargo.py` — извлечение прямых зависимостей в формате Cargo Sparse Index (`index.crates.io`) и парсер тестового репозитория.
- `src/graph.py` — построение транзитивного графа зависимостей алгоритмом BFS без рекурсии с фильтрацией и защитой от циклов.
- `src/main.py` — точка входа CLI-приложения (`py -m src.main`).
- `tests/` — модульные тесты (`unittest`) и файлы тестовых репозиториев (`mock_index.jsonl`, `repo_cycle.txt`, `repo_diamond.txt`).
- `run.bat`, `run.sh`, `Makefile` — скрипты запуска тестов и демонстрационных сценариев.

## 2. Описание всех функций и настроек (опции командной строки)

Приложение запускается через `py -m src.main` и принимает следующие параметры:

- `--package` — имя анализируемого пакета (обязательный параметр).
- `--version` — версия анализируемого пакета в формате SemVer `X.Y.Z` (обязательный параметр).
- `--repo` — URL-адрес репозитория Cargo или путь к файлу тестового репозитория (по умолчанию `https://index.crates.io`).
- `--test-mode` — флаг включения режима работы с локальным тестовым репозиторием.
- `--output` — имя сгенерированного файла с изображением графа (`.png`, `.svg`, `.puml`, `.txt`; по умолчанию `graph.png`).
- `--filter` — подстрока для исключения пакетов из анализа (по умолчанию пустая строка).

Справка по параметрам в консоли:
```cmd
py -m src.main --help
```

## 3. Команды для сборки проекта и запуска тестов

Запуск всех тестов и демонстрационных примеров одним скриптом (Windows):
```cmd
run.bat
```

Запуск всех 17 модульных тестов вручную:
```cmd
py -m unittest discover -s tests -p "test_*.py"
```

## 4. Примеры использования (команды CLI по этапам и пунктам задания)

### Этап 1. Минимальный прототип с конфигурацией

**Пункты 1–3. Передача всех настраиваемых параметров через CLI и вывод в формате ключ-значение:**
```cmd
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output my_graph.png --filter dev
```

**Пункт 4. Демонстрация обработки ошибок для каждого из 6 параметров:**

1. Ошибка в имени пакета (`--package`):
```cmd
py -m src.main --package "123!bad" --version 1.0.0
```
2. Ошибка в версии пакета (`--version`):
```cmd
py -m src.main --package serde --version latest
```
3. Ошибка в URL-адресе репозитория (`--repo`):
```cmd
py -m src.main --package serde --version 1.0.0 --repo ftp://wrong.url
```
4. Ошибка в режиме тестового репозитория (`--test-mode` с несуществующим файлом):
```cmd
py -m src.main --package serde --version 1.0.0 --test-mode --repo missing_repo.txt
```
5. Ошибка в имени выходного файла графа (`--output` с недопустимым расширением):
```cmd
py -m src.main --package serde --version 1.0.0 --output graph.exe
```
6. Ошибка в подстроке фильтрации (`--filter` с недопустимыми символами):
```cmd
py -m src.main --package serde --version 1.0.0 --filter "bad filter!"
```

### Этап 2. Сбор данных (формат пакетов Rust / Cargo)

**Пункты 1–4. Извлечение и вывод на экран прямых зависимостей заданной версии пакета:**

Работа с пакетами формата Cargo на локальном слепке индекса (версия `1.0.0` и версия `1.1.0`):
```cmd
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl
py -m src.main --package app --version 1.1.0 --test-mode --repo tests/mock_index.jsonl
```

Работа с реальным онлайн-репозиторием Rust (`https://index.crates.io`):
```cmd
py -m src.main --package serde_json --version 1.0.100 --repo https://index.crates.io
py -m src.main --package quote --version 1.0.35 --repo https://index.crates.io
```

### Этап 3. Основные операции (транзитивный граф, BFS без рекурсии)

**Пункт 1 и 4. Построение графа зависимостей алгоритмом BFS без рекурсии на тестовом репозитории (заглавные латинские буквы):**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt
```

**Пункт 2. Фильтрация пакетов, имя которых содержит заданную пользователем подстроку (`--filter`):**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
py -m src.main --package BTEST --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
```

**Пункт 3. Корректная обработка циклических зависимостей (`A -> B -> D -> A` и `C -> E -> C`):**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt
```

**Дополнительно — фильтрация на графе пакетов Cargo (`--filter mio` отсекает ветку `mio -> libc`):**
```cmd
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --filter mio
```
