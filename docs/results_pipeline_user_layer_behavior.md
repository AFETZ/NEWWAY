# User layer behavior

Документ описывает пользовательский слой results pipeline.

## Назначение

Пользовательский слой расположен в:

```text
scripts/results_pipeline/
```

Его задача — скрыть внутреннюю реализацию pipeline и дать пользователю простой запуск без длинных CLI-команд.

## Основной entrypoint

```powershell
.\scripts\results_pipeline\run.ps1
```

Скрипт предлагает выбрать источник:

```text
1 — VaN3Twin / ns-3 CAM logs
2 — Simu5G / OMNeT++ scavetool CSV
q — выход
```

## Поведение при ошибках

Если пользователь вводит неверный путь к папке VaN3Twin, скрипт не падает сразу.
Он показывает ошибку и предлагает ввести путь заново.

Если пользователь вводит неверный путь к Simu5G CSV, скрипт также просит повторить ввод.

Если пользователь вводит `q`, запуск прекращается без ошибки.

## Default mode

Если пользователь нажимает Enter на всех вопросах, используются sample inputs и sample outputs из scripts/results_pipeline.

VaN3Twin default input:

```text
scripts/results_pipeline/sample_inputs/van3twin_cam/
```

Simu5G default input:

```text
scripts/results_pipeline/sample_inputs/simu5g_scavetool/output_all_sample.csv
```

## Output

После успешного запуска пользователь получает:

```text
normalized_events.csv
normalized_metrics.csv
aggregates_*.csv
diagnostics.csv
run_metadata.json
run_metadata.yaml
```

Главный файл:

```text
normalized_metrics.csv
```

Контроль качества для пользователя:

```text
diagnostics.csv
```

Если diagnostics.csv содержит только header, критических проблем при обработке не найдено.
