# Developer guide results pipeline NEWWAY

Документ описывает developer-facing архитектуру results pipeline проекта NEWWAY.

Pipeline реализован как CSV-first интеграционный слой для результатов моделирования из разных V2X-стеков.

## Главная идея

```text
raw CSV / logs / scavetool export / SQL-export
        -> reader / adapter layer
        -> normalized_events.csv
        -> normalized_metrics.csv
        -> aggregates_*.csv
        -> diagnostics.csv
        -> run_metadata.json / run_metadata.yaml
```

Центральный артефакт:

```text
normalized_metrics.csv
```

Это единый metric-oriented слой для downstream-анализа, отчётов, графиков и будущих интеграций.

## Слои репозитория

```text
scripts/results_pipeline/                 пользовательская точка входа
tools/results_pipeline/   внутренняя реализация pipeline
tests/smoke_results_pipeline/ smoke tests и fixtures
docs/           input contracts поддерживаемых источников
docs/           developer-документация
local_inputs/             локальные raw inputs команды, игнорируются git
runs/                     локальные временные outputs, игнорируются git
tmp/                      локальные backup/scratch файлы, игнорируются git
```

## Поддерживаемые источники

### VaN3Twin / ns-3

CLI source:

```text
van3twin_ns3
```

Поддерживаемые входы:

```text
mini synthetic PHY fixture
mini synthetic PRR fixture
real-style PHY CSV
real-style PRR CSV
CAM receiver CSV directory
```

CAM receiver logs маппятся так:

```text
camId        -> src_id
vehN         -> dst_id
timestamp    -> ts_us
speed        -> speed_mps
acceleration -> acceleration_mps2
```

Поддерживаемые CAM-метрики:

```text
cam_rx_count
speed_mps
acceleration_mps2
```

Строгий PRR/PDR не считается только по CAM receiver logs.
Для этого нужен TX/generation log.

### Simu5G / OMNeT++

CLI source:

```text
simu5g
```

Поддерживаемый вход:

```text
один CSV-файл, экспортированный через OMNeT++ / Simu5G scavetool
```

Ожидаемые колонки:

```text
run,type,module,name,attrname,attrvalue,vectime,vecvalue
```

Reader игнорирует служебные строки:

```text
attr
config
runattr
```

Vector rows разворачиваются из одной строки scavetool в несколько normalized metric rows.

Пример:

```text
vectime  = "0.1 0.2 0.3"
vecvalue = "37.1 38.2 39.3"
```

превращается в:

```text
ts_us=100000, value=37.1
ts_us=200000, value=38.2
ts_us=300000, value=39.3
```

Поддерживаемые SINR mappings:

```text
measuredSinrDl:vector -> sinr_db
measuredSinrUl:vector -> sinr_db
rcvdSinrDl:vector     -> sinr_db
rcvdSinrUl:vector     -> sinr_db
rcvdSinrD2D:vector    -> sinr_db
```

## Ключевые файлы реализации

```text
tools/results_pipeline/cli.py
tools/results_pipeline/pipeline.py
tools/results_pipeline/simu5g_pipeline.py
tools/results_pipeline/schema.py
tools/results_pipeline/metrics_projection.py
tools/results_pipeline/diagnostics.py
tools/results_pipeline/aggregate.py
tools/results_pipeline/metadata.py
tools/results_pipeline/writers.py
tools/results_pipeline/readers/van3twin_csv.py
tools/results_pipeline/readers/simu5g_scavetool_csv.py
```

## CLI

Общий формат команды:

```powershell
python -m tools.results_pipeline.cli build `
  --source <van3twin_ns3|simu5g> `
  --input <input_path> `
  --output <output_path> `
  --scenario <scenario_name> `
  --run-id <run_id>
```

## Выходные артефакты

VaN3Twin/ns-3:

```text
normalized_events.csv
normalized_metrics.csv
aggregates_overall.csv
diagnostics.csv
run_metadata.json
run_metadata.yaml
```

Simu5G:

```text
normalized_events.csv
normalized_metrics.csv
aggregates_by_metric.csv
aggregates_overall.csv
diagnostics.csv
run_metadata.json
run_metadata.yaml
```

Для Simu5G файл normalized_events.csv пока сохраняется для совместимости output-набора.
Главный смысловой артефакт для Simu5G — normalized_metrics.csv.

## Схема normalized_metrics.csv

```text
run_id
scenario
source_stack
sample_kind
metric_name
metric_scope
entity_id
src_id
dst_id
ts_us
value
unit
module_path
stat_name
input_file
raw_row_num
```

## Diagnostics

Diagnostics записываются в:

```text
diagnostics.csv
```

Типовые diagnostics:

```text
empty_input
missing_pkt_id
missing_ts_us
negative_latency
no_prr_pdr_success_signal
empty_vector
vector_length_mismatch
vector_missing_timestamp
non_numeric_value
unknown_metric
```

## Tests

Smoke tests находятся здесь:

```text
tests/smoke_results_pipeline/
```

Fixtures находятся здесь:

```text
tests/smoke_results_pipeline/data/
```

Запуск тестов:

```powershell
python -m pytest .\tests\smoke_results_pipeline -q
```

Ожидаемый результат:

```text
all smoke tests passed
```

## Как добавить новый VaN3Twin-формат

1. Добавить header или filename detection в readers/van3twin_csv.py.
2. Добавить отдельную функцию _read_*, которая возвращает NormalizedEvent.
3. Добавить поля в schema.py, если событию нужны новые атрибуты.
4. Добавить metric projection в metrics_projection.py.
5. Добавить маленький fixture в tests/smoke_results_pipeline/data/.
6. Добавить smoke test.
7. Обновить docs/.

## Как добавить новую Simu5G-метрику

1. Расширить _normalize_metric() в readers/simu5g_scavetool_csv.py.
2. Сохранить исходное имя статистики в stat_name.
3. Сохранить исходный module path в module_path.
4. Нормализовать единицы измерения в _normalize_value_and_unit().
5. Добавить fixture row.
6. Добавить или обновить smoke tests.
7. Обновить docs/simu5g_input_contract.md.

## SQL / SQLite integration

Текущая реализация является CSV-first.
Она не выполняет SQL напрямую.

Если SQL используется upstream, результат SQL должен быть экспортирован в CSV и передан в pipeline.

Если позже будет предоставлена реальная SQLite-схема, можно добавить отдельный reader:

```text
tools/results_pipeline/readers/van3twin_sqlite.py
```

и при необходимости новый CLI source.

## Git safety rules

Нельзя stage-ить посторонние generated ASN1 files.

Нельзя использовать:

```powershell
git add .
```

Использовать selective staging:

```powershell
git add .gitignore
git add tools/results_pipeline
git add tests/smoke_results_pipeline
git add docs
git add scripts/results_pipeline
```

Перед commit:

```powershell
python -m pytest .\tests\smoke_results_pipeline -q
git diff --check -- .\tools\results_pipeline .\tests\smoke_results_pipeline .\docs .\scripts/results_pipeline
git diff --cached --name-only
```

В staged не должны попасть:

```text
emulation-support/
src/automotive/model/ASN1/
local_inputs/
tmp/
runs/
```

## Текущие ограничения

```text
CAM-only logs не дают строгий PRR/PDR.
VaN3Twin SINR/BLER требует отдельный PHY/radio-quality source.
Simu5G source сейчас ожидает один CSV-файл, а не директорию.
Полные реальные raw dumps должны оставаться в local_inputs/ и не коммититься.
```
