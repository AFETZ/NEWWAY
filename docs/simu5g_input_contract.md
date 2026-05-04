# Input contract для Simu5G / OMNeT++ scavetool CSV

Документ описывает поддерживаемый входной формат Simu5G для NEWWAY results pipeline.

## Поддерживаемый вход

Pipeline поддерживает один CSV-файл, экспортированный из OMNeT++ / Simu5G через scavetool.

Ожидаемые колонки:

```text
run,type,module,name,attrname,attrvalue,vectime,vecvalue
```

Директория для Simu5G на текущем этапе не поддерживается.
Режим `--source simu5g` ожидает один `.csv` файл.

## Служебные строки

Следующие типы строк игнорируются:

```text
attr
config
runattr
```

## Vector rows

Строки с `type = vector` разворачиваются из одной строки scavetool в несколько строк `normalized_metrics.csv`.

Пример входа:

```text
vectime  = "0.1 0.2 0.3"
vecvalue = "37.1 38.2 39.3"
```

Результат нормализации:

```text
ts_us=100000, value=37.1
ts_us=200000, value=38.2
ts_us=300000, value=39.3
```

## Поддерживаемые SINR-названия

```text
measuredSinrDl:vector -> sinr_db
measuredSinrUl:vector -> sinr_db
rcvdSinrDl:vector     -> sinr_db
rcvdSinrUl:vector     -> sinr_db
rcvdSinrD2D:vector    -> sinr_db
```

Оригинальное имя статистики Simu5G сохраняется в поле:

```text
stat_name
```

Оригинальный OMNeT++ module path сохраняется в поле:

```text
module_path
```

`entity_id` извлекается из `module_path`, если это возможно:

```text
Network.ue[0].nrNic.phy -> entity_id = ue[0]
Network.ue[1].nrNic.phy -> entity_id = ue[1]
```

## Diagnostics

Reader может фиксировать следующие проблемы:

```text
empty_vector
vector_length_mismatch
vector_missing_timestamp
non_numeric_value
unknown_metric
```

## Выходные артефакты

```text
normalized_events.csv
normalized_metrics.csv
aggregates_by_metric.csv
aggregates_overall.csv
diagnostics.csv
run_metadata.json
run_metadata.yaml
```

Для Simu5G главным смысловым файлом является `normalized_metrics.csv`.
Файл `normalized_events.csv` сохраняется для совместимости общего output-набора.

## Пример запуска

```powershell
python -m tools.results_pipeline.cli build `
  --source simu5g `
  --input .\scripts\results_pipeline\sample_inputs\simu5g_scavetool\output_all_sample.csv `
  --output .\scripts\results_pipeline\sample_outputs\simu5g_scavetool `
  --scenario simu5g_vector_user_sample `
  --run-id simu5g_vector_user_sample_001
```
