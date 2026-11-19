# Cargo Dependency Visualizer (Вариант 25)

CLI-инструмент анализа и визуализации графа зависимостей пакетов Rust (Cargo), разработанный на стандартной библиотеке Python без сторонних библиотек и менеджеров пакетов.

## 1. Общее описание и структура проекта

- `src/config.py` — модель конфигурации `AppConfig` и валидация всех пользовательских параметров.
- `src/cli.py` — парсер опций командной строки (`argparse`) и вывод конфигурации в формате `ключ: значение`.
- `src/cargo.py` — работа с форматом Cargo Sparse Index (`index.crates.io`), API обратных зависимостей и парсер тестового репозитория.
- `src/graph.py` — построение прямого и обратного графов зависимостей алгоритмом BFS без рекурсии с фильтрацией и защитой от циклов.
- `src/visualizer.py` — генерация диаграмм на языке **PlantUML** (`.puml`) и экспорт изображений графа в `.png` / `.svg`.
- `src/main.py` — точка входа CLI-приложения (`py -m src.main`).
- `tests/` — модульные тесты (`unittest`) и тестовые репозитории (`mock_index.jsonl`, `repo_cycle.txt`, `repo_diamond.txt`).
- `run.bat`, `run.sh`, `Makefile` — скрипты автоматического запуска тестов и демонстраций.

## 2. Описание всех функций и настроек (CLI-параметры)

- `--package` — имя анализируемого пакета (обязательный).
- `--version` — версия пакета в формате SemVer `X.Y.Z` (обязательный).
- `--repo` — URL-адрес репозитория Cargo или путь к файлу тестового репозитория (по умолчанию `https://index.crates.io`).
- `--test-mode` — флаг включения режима работы с локальным тестовым репозиторием.
- `--output` — имя сгенерированного файла с изображением графа (`.png`, `.svg`, `.puml`, `.txt`; по умолчанию `graph.png`).
- `--filter` — подстрока для исключения пакетов из графа (по умолчанию пустая).
- `--reverse` — режим поиска и вывода обратных зависимостей для заданного пакета (Этап 4).

Справка по параметрам:
```cmd
py -m src.main --help
```

## 3. Команды для сборки и запуска тестов

Автоматический запуск всех 22 модульных тестов и демонстраций (Windows):
```cmd
run.bat
```

Запуск модульных тестов вручную:
```cmd
py -m unittest discover -s tests -p "test_*.py"
```

## 4. Примеры использования (команды CLI по всем 5 этапам задания)

### Этап 1. Минимальный прототип с конфигурацией

**Пункты 1–3. Передача параметров через CLI и вывод в формате ключ-значение:**
```cmd
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output my_graph.png --filter dev
```

**Пункт 4. Демонстрация обработки ошибок для параметров:**
```cmd
py -m src.main --package "123!bad" --version 1.0.0
py -m src.main --package serde --version latest
py -m src.main --package serde --version 1.0.0 --repo ftp://wrong.url
py -m src.main --package serde --version 1.0.0 --test-mode --repo missing_repo.txt
py -m src.main --package serde --version 1.0.0 --output graph.exe
py -m src.main --package serde --version 1.0.0 --filter "bad filter!"
```

### Этап 2. Сбор данных (формат пакетов Rust / Cargo)

**Пункты 1–4. Извлечение прямых зависимостей заданной версии пакета:**
```cmd
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl
py -m src.main --package app --version 1.1.0 --test-mode --repo tests/mock_index.jsonl
py -m src.main --package serde_json --version 1.0.100 --repo https://index.crates.io
```

### Этап 3. Основные операции (транзитивный граф, BFS без рекурсии)

**Пункт 1 и 4. Построение графа зависимостей алгоритмом BFS без рекурсии:**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt
py -m src.main --package quote --version 1.0.35 --repo https://index.crates.io
```

**Пункт 2. Фильтрация пакетов по подстроке (`--filter`):**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --filter TEST
py -m src.main --package serde_json --version 1.0.100 --repo https://index.crates.io --filter ryu
```

**Пункт 3. Корректная обработка циклических зависимостей:**
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt
```

### Этап 4. Дополнительные операции (обратные зависимости)

**Пункты 1–2. Вывод обратных зависимостей (`--reverse`) с использованием BFS на различных случаях:**

1. Обратные зависимости узла `D` в ромбовидном графе (`D <- B, C`, далее `B <- A`, `C <- A`):
```cmd
py -m src.main --package D --version 1.0.0 --test-mode --repo tests/repo_diamond.txt --reverse
```
2. Обратные зависимости узла `C` в графе с циклами (`C <- A, E` с обработкой циклов):
```cmd
py -m src.main --package C --version 1.0.0 --test-mode --repo tests/repo_cycle.txt --reverse
```
3. Обратные зависимости пакета `libc` в локальном индексе Cargo (`libc <- mio <- tokio <- app`):
```cmd
py -m src.main --package libc --version 0.2.0 --test-mode --repo tests/mock_index.jsonl --reverse
```
4. Обратные зависимости реального крейта из `crates.io`:
```cmd
py -m src.main --package quote --version 1.0.35 --repo https://index.crates.io --reverse
```

### Этап 5. Визуализация (PlantUML и сравнение со штатными инструментами)

**Пункты 1–3. Генерация PlantUML (`.puml`) и изображений (`.png` / `.svg`) для 3 различных пакетов:**

1. Пакет `app` (граф зависимостей Cargo):
```cmd
py -m src.main --package app --version 1.0.0 --test-mode --repo tests/mock_index.jsonl --output app_graph.png
```
2. Пакет `A` из графа с циклами (циклические дуги выделяются красным пунктиром `#red : cycle`):
```cmd
py -m src.main --package A --version 1.0.0 --test-mode --repo tests/repo_cycle.txt --output cycle_graph.png
```
3. Реальный пакет `quote` с `crates.io` (сохранение в векторный `.svg` и `.png`):
```cmd
py -m src.main --package quote --version 1.0.35 --repo https://index.crates.io --output quote_graph.svg
```

**Пункт 4. Сравнение со штатным инструментом Cargo (`cargo tree`):**

Штатная команда менеджера пакетов Rust для просмотра дерева зависимостей:
```cmd
cargo tree --edges normal
```

Сравнение результатов:
- **Совпадения:** оба инструмента строят транзитивный граф рабочих (`normal`) зависимостей, исключая `dev-dependencies`.
- **Причины расхождений:**
  1. **Отсутствие `Cargo.lock` и разрешение SemVer:** штатный `cargo tree` опирается на lock-файл конкретного проекта и целевую ОС, а наша утилита разрешает диапазоны версий (`^1.0.0`) напрямую по индексу репозитория.
  2. **Опциональные зависимости (`features`):** `cargo tree` включает зависимости, активируемые стандартными фичами (`default`), тогда как наша утилита строго отфильтровывает все пакеты с флагом `"optional": true`.
  3. **Пользовательский фильтр и циклы:** наша утилита исключает подграфы по подстроке `--filter` и визуализирует обратные циклические рёбра, тогда как Cargo запрещает циклические рабочие зависимости на уровне манифеста `Cargo.toml`.
