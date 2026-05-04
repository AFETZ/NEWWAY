# Использование Simu5G в общем results pipeline

## Зачем нужен этот файл
Этот документ описывает, как использовать поддержку Simu5G в общем пайплайне обработки результатов.

Сейчас Simu5G уже не рассматривается как отдельный внешний скрипт: он подключён к общему CLI и обрабатывается через тот же входной интерфейс, что и `VaN3Twin/ns-3`.

## Общая идея
В проекте теперь есть единая точка входа:

```powershell
python -m tools.results_pipeline.cli build ...
```

Разница между источниками задаётся через параметр `--source`.

## Поддерживаемые источники
- `van3twin_ns3` — для артефактов VaN3Twin / ns-3 / NEWWAY
- `simu5g` — для CSV, экспортированного из Simu5G через `opp_scavetool`

## Общая схема работы для Simu5G
```text
Simu5G scenario
-> .sca / .vec
-> opp_scavetool export
-> CSV
-> tools.results_pipeline.cli --source simu5g
-> normalized_events.csv
-> normalized_metrics.csv
-> aggregates_by_metric.csv
-> aggregates_overall.csv
-> diagnostics.csv
-> run_metadata.json / yaml
```

## Что требуется на вход для Simu5G
Минимально требуется CSV-файл, полученный после экспорта результатов Simu5G.

Желательно также сохранять рядом:
- `omnetpp.ini`
- `*.ned`
- исходные `*.sca` и `*.vec`

## Команда запуска для Simu5G
Из корня репозитория:

```powershell
python -m tools.results_pipeline.cli build --source simu5g --input .\tests\smoke_results_pipeline\data\simu5g_scavetool_sample.csv --output .\tmp-cli-simu5g --scenario minimal-simu5g --run-id cli-simu5g-002
```

## Что делает эта команда
- читает экспортированный CSV;
- определяет записи как `scalar` или `vector`;
- нормализует метрики в общий формат;
- считает агрегаты по метрикам;
- считает общий агрегированный summary;
- пишет diagnostics и metadata.

## Что получается на выходе
В выходной папке формируются:
- `normalized_events.csv`
- `normalized_metrics.csv`
- `aggregates_by_metric.csv`
- `aggregates_overall.csv`
- `diagnostics.csv`
- `run_metadata.json`
- `run_metadata.yaml`

## Смысл выходных файлов
### `normalized_events.csv`
Нормализованные записи в единой схеме.

### `normalized_metrics.csv`
Единый metric-oriented слой для сопоставления Simu5G и `van3twin_ns3`.
На текущем этапе для Simu5G он близок по содержанию к `normalized_events.csv`,
но сохраняется отдельно как основной унифицированный слой для downstream-анализа
и последующего сравнения двух стеков.

### `aggregates_by_metric.csv`
Сводка отдельно по каждой метрике: сколько строк, сколько сущностей, среднее, минимум, максимум, временной диапазон.

### `aggregates_overall.csv`
Общий summary по ключевым метрикам прогона, например:
- `throughput_mean_bps`
- `delay_mean_us`
- `delay_p50_us`
- `delay_p95_us`
- `sinr_mean_db`
- `sinr_p50_db`
- `sinr_p95_db`
- `loss_ratio_mean`

### `diagnostics.csv`
Диагностика проблем во входе или на этапе нормализации.

### `run_metadata.json / yaml`
Контекст запуска: run_id, scenario, branch, commit, input files.

## Команда запуска для VaN3Twin/ns-3
Тот же общий CLI используется и для существующего CSV-first стека:

```powershell
python -m tools.results_pipeline.cli build --source van3twin_ns3 --input .\tests\smoke_results_pipeline\data --output .\tmp-cli-van3twin --scenario v2v-cam-exchange-sionna-nrv2x --run-id cli-van3twin-001
```

## Практический смысл
Это значит, что оба источника данных теперь запускаются через один интерфейс:
- различается только `--source`;
- downstream-логика обработки остаётся общей;
- результаты двух стеков проще сравнивать на уровне унифицированных артефактов.

## Что поддерживается сейчас
- Simu5G через CSV после `opp_scavetool`;
- scalar и vector записи;
- базовые метрики: throughput, delay, sinr, packet loss;
- нормализация в unified format;
- агрегаты по метрикам;
- общий summary;
- metadata и diagnostics.

## Что пока не поддерживается
- прямой парсинг `.sca/.vec` без промежуточного CSV;
- автоматическое извлечение всех метрик OMNeT++;
- полная интерпретация всех PHY/MAC статистик Simu5G;
- полноценное практическое сравнение с реальным dual-run набором Simu5G и ns-3.

## Итог
На текущем этапе Simu5G уже встроен в общий `results pipeline` как поддерживаемый источник данных и обрабатывается через тот же CLI, что и `VaN3Twin/ns-3`.

## Практическая рекомендация по повторным запускам
Перед повторным запуском Simu5G pipeline рекомендуется очищать старую выходную директорию либо использовать новую.

Пример:
```powershell
Remove-Item -Recurse -Force .\tmp-cli-simu5g -ErrorAction SilentlyContinue
python -m tools.results_pipeline.cli build --source simu5g --input .\path\to\export.csv --output .\tmp-cli-simu5g --scenario <scenario> --run-id <run_id>
```

Это позволяет избежать смешивания артефактов разных запусков и упрощает ручную проверку результатов.

## Дополнительные замечания по использованию
- команды предполагают запуск из корня репозитория;
- перед запуском желательно активировать `.venv`;
- в текущей версии Simu5G поддерживается через CSV после `opp_scavetool`, а не через прямой парсинг `.sca/.vec`;
- если `diagnostics.csv` содержит только заголовок, это считается нормальным результатом.
