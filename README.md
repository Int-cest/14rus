# 14rus

Минимальная инструкция по запуску проекта.

## Что нужно

- Python 3.10+
- pip

## 1. Создать и активировать виртуальное окружение

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/macOS
```

## 2. Установить зависимости

```powershell
pip install -r requirements.txt
```

## 3. Указать папку для сканирования

Откройте src/config.py и при необходимости поменяйте PATH_DATA.

Текущее значение по умолчанию:

```python
PATH_DATA = PROJECT_ROOT / "datasets" / "share"
```

## 4. Запуск из терминала

Из корня проекта:

```
python src/main.py
```

Путь сканирования задается в src/config.py через PATH_DATA.

## 5. Результат

После выполнения создаются файлы:

- report.csv
- report.json
- report.md

Файлы сохраняются в текущую директорию, из которой запускается команда.

## 6. Где смотреть время выполнения

Во время запуска тайминг и прогресс пишутся:

- в терминал (INFO-логи)
- в logs/parser_info.log
- ошибки в logs/parser_error.log

Прогресс показывается каждые 50 обработанных файлов (elapsed + скорость).
