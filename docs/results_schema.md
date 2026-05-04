# Results Pipeline Overview

## Назначение
Документ кратко описывает текущий `results pipeline` в проекте NEWWAY и поддерживаемые источники данных.

На текущем этапе pipeline поддерживает два источника:
- `van3twin_ns3`
- `simu5g`

## Поддерживаемые источники

### `van3twin_ns3`
Источник на базе `VaN3Twin / ns-3 / NEWWAY`.

Ожидаемый вход:
- директория с CSV-артефактами VaN3Twin/ns-3

Поддерживаемые типы входных CSV определяются по структуре заголовков и ожидаемым ns-3-артефактам.
Чужие CSV-файлы, не соответствующие формату `van3twin_ns3`, должны игнорироваться.

### `simu5g`
Источник на базе `Simu5G / OMNeT++`.

Ожидаемый вход:
- CSV-файл, полученный после экспорта результатов через `opp_scavetool`

## Общий CLI
Для обоих источников используется единая команда:

```powershell
python -m tools.results_pipeline.cli build --source van3twin_ns3 --input <artifacts_dir> --output <output_dir> --scenario <scenario> --run-id <run_id>

python -m tools.results_pipeline.cli build --source simu5g --input <exported_csv> --output <output_dir> --scenario <scenario> --run-id <run_id>
```

## Основные выходные файлы

### `normalized_events.csv`
Базовый слой нормализованных записей.
- для `van3twin_ns3` это event-oriented представление
- для `simu5g` это нормализованные metric rows, пришедшие из CSV-экспорта

### `normalized_metrics.csv`
Общий unified layer для двух поддерживаемых источников.
Этот файл нужен для сопоставления метрик между `van3twin_ns3` и `simu5g`, общего downstream-анализа и дальнейшей унификации результатов в контуре CAVISE.

### `aggregates_overall.csv`
Сводные агрегаты по прогону.
- для `van3twin_ns3` агрегаты строятся по event-данным
- для `simu5g` агрегаты строятся по нормализованным метрикам

### `aggregates_by_metric.csv`
Используется в `simu5g` pipeline для агрегирования по каждой нормализованной метрике.

### `diagnostics.csv`
Диагностическая информация о неполных строках, проблемах структуры входных данных и иных замечаниях по качеству входа.

### `run_metadata.json` / `run_metadata.yaml`
Метаданные прогона: `run_id`, `scenario`, источник, список входных файлов, git branch / commit, время создания.

## Практический смысл
- `van3twin_ns3` остаётся основным стеком для существующего контура CAVISE
- `simu5g` подключён как дополнительный внешний сетевой источник данных
- `normalized_metrics.csv` является общей точкой сопоставления результатов двух стеков

## Связанные документы
- `docs/results_pipeline_user_guide.md`
- `docs/unified_results_schema.md`
- `docs/simu5g_input_contract.md`
- `docs/simu5g_usage.md`
- `docs/simu5g_vs_ns3_metric_mapping.md`
- `docs/stack_comparison_simu5g_vs_ns3.md`

## Дополнительные эксплуатационные замечания
- рекомендуется использовать отдельную выходную директорию для каждого запуска;
- если используется старая директория, перед повторным запуском её лучше очистить;
- `normalized_metrics.csv` является основным unified layer для сопоставления результатов `van3twin_ns3` и `simu5g`;
- `diagnostics.csv`, содержащий только строку заголовка, считается нормальным результатом и означает отсутствие существенных замечаний.

## Рекомендация по clean run
Для чистого ручного прогона и корректных скриншотов рекомендуется удалять старую output-папку перед повторным запуском.

Примеры:
```powershell
Remove-Item -Recurse -Force .\tmp-cli-van3twin -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\tmp-cli-simu5g -ErrorAction SilentlyContinue
```
