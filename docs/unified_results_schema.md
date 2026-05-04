# Единая схема результатов (`normalized_metrics.csv`)

## Зачем нужен этот документ
Этот документ описывает общий формат `normalized_metrics.csv`, в который приводятся результаты из двух источников:
- `van3twin_ns3`
- `simu5g`

Смысл схемы простой:
- разные симуляторы дают результаты в разной форме;
- после нормализации они приводятся к одному общему виду;
- этот общий вид можно одинаково агрегировать, сравнивать и передавать дальше.

## Поддерживаемые источники
- `van3twin_ns3` — стек VaN3Twin / ns-3 / NEWWAY
- `simu5g` — стек Simu5G / OMNeT++

## Общий принцип
Каждая строка `normalized_metrics.csv` описывает одну нормализованную метрику.
Схема является metric-oriented, а не широкой таблицей со всеми полями сразу.

Например:
- если известен `sinr_db`, создаётся строка с `metric_name = sinr_db`
- если известен `distance_m`, создаётся строка с `metric_name = distance_m`
- если известен `throughput_bps`, создаётся строка с `metric_name = throughput_bps`

## Поля схемы
| Поле | Смысл | Обязательно |
|---|---|---|
| `run_id` | идентификатор конкретного прогона | да |
| `scenario` | имя сценария моделирования | да |
| `source_stack` | источник данных: `van3twin_ns3` или `simu5g` | да |
| `sample_kind` | тип записи: `scalar`, `vector`, `derived` | да |
| `metric_name` | нормализованное имя метрики | да |
| `metric_scope` | уровень метрики: `global`, `node`, `link`, `flow` | да |
| `entity_id` | идентификатор узла/сущности, если есть | нет |
| `src_id` | идентификатор источника передачи, если есть | нет |
| `dst_id` | идентификатор получателя, если есть | нет |
| `ts_us` | время в микросекундах, если применимо | нет |
| `value` | числовое значение метрики | да |
| `unit` | единица измерения | нет |
| `module_path` | путь до модуля симулятора, если есть | нет |
| `stat_name` | исходное имя статистики из источника | нет |
| `input_file` | файл, из которого взята запись | да |
| `raw_row_num` | номер строки во входном файле | да |

## Что важно понимать
Поля типа `sinr_db`, `rssi_dbm`, `distance_m`, `prr_value`, `delay_us`, `throughput_bps`
в `normalized_metrics.csv` не существуют как отдельные колонки.

Они представлены так:
- имя метрики хранится в `metric_name`
- числовое значение хранится в `value`
- единица измерения хранится в `unit`

## Пример строки для ns-3
```csv
run_id,scenario,source_stack,sample_kind,metric_name,metric_scope,entity_id,src_id,dst_id,ts_us,value,unit,module_path,stat_name,input_file,raw_row_num
run-001,v2v-cam-exchange-sionna-nrv2x,van3twin_ns3,derived,sinr_db,link,car2,car1,car2,1000,20.0,dB,,sinr_db,mini_phy_with_sionna_nrv2x.csv,2
```

## Пример строки для Simu5G
```csv
run_id,scenario,source_stack,sample_kind,metric_name,metric_scope,entity_id,src_id,dst_id,ts_us,value,unit,module_path,stat_name,input_file,raw_row_num
run-002,minimal-simu5g,simu5g,scalar,throughput_bps,node,ue[0],,,,1250000.0,bps,Network.ue[0].app[0],throughput,simu5g_export.csv,2
```

## Правила нормализации
1. Общий смысл метрики фиксируется в `metric_name`.
2. Числовое значение фиксируется в `value`.
3. Единица измерения фиксируется в `unit`.
4. Если метрики нет, поле не заполняется искусственным нулём.
5. Если запись пришла как временной ряд, используется `sample_kind = vector`.
6. Если запись вычислена в ходе обработки, используется `sample_kind = derived`.

## Практический смысл
`normalized_metrics.csv` — это первый действительно общий слой,
на котором можно сравнивать `van3twin_ns3` и `simu5g`
без полной зависимости от внутреннего формата исходных CSV.

## Дополнительное пояснение по структуре
Текущая unified-схема является metric-oriented.

Это означает, что разные метрики не раскладываются по отдельным колонкам вида `sinr_db`, `throughput_bps`, `delay_us` внутри одной широкой таблицы.

Вместо этого используется общий принцип:
- имя метрики хранится в поле `metric_name`;
- числовое значение хранится в поле `value`;
- единица измерения хранится в поле `unit`.

Такой подход упрощает:
- сопоставление разных источников данных;
- downstream-агрегацию;
- расширение схемы новыми метриками без изменения структуры CSV.
