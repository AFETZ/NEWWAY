# Results Pipeline MVP (v0)

## Что делает
Минимальный CSV-first pipeline для артефактов VaN3Twin / NEWWAY.

## Поддержано в v0
- чтение CSV из директории артефактов;
- приоритетно ищет:
  - `*phy_with_sionna_nrv2x*.csv`
  - `*prr_with_sionna_nrv2x*.csv`
- если таких файлов нет, читает все `*.csv` под указанной директорией.

## Выходные файлы
- `normalized_events.csv`
- `aggregates_overall.csv`
- `diagnostics.csv`
- `run_metadata.json`
- `run_metadata.yaml`

## Нормализованные поля
- `run_id`
- `scenario`
- `source_kind`
- `event_type`
- `ts_us`
- `src_id`
- `dst_id`
- `pkt_id`
- `size_bytes`
- `latency_us`
- `rssi_dbm`
- `sinr_db`
- `bler`
- `prr_value`
- `pdr_value`
- `success`
- `drop_reason`
- `raw_file`
- `raw_row_num`

## Агрегаты v0
- общее число строк
- число входных файлов
- число успешных строк
- `tx_count`, `rx_count`
- `prr_mean`, `pdr_mean`
- `latency_mean_us`, `latency_p50_us`, `latency_p95_us`
- `sinr_mean_db`
- `bler_mean`

## Диагностика v0
- отсутствие входных файлов
- пустой CSV
- ошибка чтения CSV
- отрицательная задержка
- отсутствующий `pkt_id`
- отсутствующий `ts_us`
- отсутствие сигнала `prr/pdr/success`

## Пример запуска
```bash
python -m tools.results_pipeline.cli build `
  --input analysis/scenario_runs/.../artifacts `
  --output .\tmp-results `
  --scenario v2v-cam-exchange-sionna-nrv2x
```

## Что отложено
- адаптер для 5G-LENA / SQLite
- оконные агрегаты
- plotting
- интеграция во все сценарии
