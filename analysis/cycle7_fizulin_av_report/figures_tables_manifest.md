# Манифест фигур и таблиц для отчета

## 1. Обязательные фигуры — lane-change кейс

| № | Файл в пакете | Исходный смысл | Где использовать |
|---|---|---|---|
| 1 | `evidence/img/lane_change/collision_risk_timeseries.png` | временной профиль safety-метрик | раздел с доказательными артефактами |
| 2 | `evidence/img/lane_change/decision_delay_scatter.png` | задержка между drop и decision | раздел `связь -> решение` |
| 3 | `evidence/img/lane_change/decision_type_counts.png` | распределение decision-событий | раздел `связь -> решение` |
| 4 | `evidence/img/lane_change/intuitive_dbm_prr_maneuver_chain.png` | цепочка `dBm -> PRR -> решение -> исход` | раздел подтвержденных результатов |
| 5 | `evidence/img/lane_change/intuitive_packet_raster.png` | packet-level raster | раздел подтвержденных результатов |
| 6 | `evidence/img/lane_change/intuitive_prr_cumulative.png` | накопительный PRR по времени | раздел подтвержденных результатов |
| 7 | `evidence/img/lane_change/intuitive_truck_speed_observed.png` | наблюдаемая скорость грузовика | раздел подтвержденных результатов |
| 8 | `evidence/img/lane_change/event_chain_timeline.png` | причинная шкала событий | раздел подтвержденных результатов |
| 9 | `evidence/img/lane_change/gap_ttc_timeseries.png` | gap/TTC по времени | раздел safety |
| 10 | `evidence/img/lane_change/ns3_events_per_second.png` | ns-3 события по секундам | раздел доказательной аналитики |
| 11 | `evidence/img/lane_change/speed_lane_timeseries.png` | скорости и полосы | раздел подтвержденных результатов |

## 2. Обязательные фигуры — intersection кейс

| № | Файл в пакете | Исходный смысл | Где использовать |
|---|---|---|---|
| 12 | `evidence/img/intersection/behavioral_dashboard.png` | сводка поведенческого слоя | раздел intersection кейса |
| 13 | `evidence/img/intersection/cross_layer_causal_chain.png` | сквозная causal chain | раздел `связь -> решение -> исход` |
| 14 | `evidence/img/intersection/network_kpi_dashboard.png` | network KPI | раздел intersection кейса |
| 15 | `evidence/img/intersection/vehicle_profiles.png` | профили автомобилей | раздел intersection кейса |
| 16 | `evidence/img/intersection/intersection_decision_delay_scatter.png` | задержка decision | раздел `связь -> решение` |
| 17 | `evidence/img/intersection/intersection_decision_type_counts.png` | типы решений | раздел `связь -> решение` |

Отдельная важная оговорка:

- `transport_safety_dashboard.png` и `intersection_collision_risk_timeseries.png`
  полезны как supporting-visualization, но для этого run-а их не стоит делать
  центральным доказательством, потому что в исходном `collision_risk_summary.csv`
  поля `min_gap_m` и `min_ttc_s` заполнены не полностью.

## 3. Дополнительные визуальные приложения

| № | Файл в пакете | Назначение |
|---|---|---|
| 20 | `evidence/img/extras/circle_v2v_animation.gif` | 3D/визуализационное приложение для V2V кейса |
| 21 | `evidence/img/extras/intersection_v2i_animation.gif` | 3D/визуализационное приложение для intersection кейса |

## 3a. Фигуры EVA-серии

| № | Файл в пакете | Назначение |
|---|---|---|
| 22 | `evidence/img/eva_series/eva_prr_latency_summary.png` | сравнение `PRR` и `latency` по режимам EVA-серии |
| 23 | `evidence/img/eva_series/eva_cam_gap_summary.png` | сравнение числа CAM от emergency vehicle и максимального inter-CAM gap |
| 24 | `evidence/img/eva_series/eva_good_speed_timeline.png` | speed timeline для baseline good-режима |
| 25 | `evidence/img/eva_series/eva_vbad_speed_timeline.png` | speed timeline для very-bad режима |
| 26 | `evidence/img/eva_series/eva_lowpen_speed_timeline.png` | speed timeline для low-penetration режима |

## 4. Обязательные таблицы внутри отчета

| № | Таблица | Содержание |
|---|---|---|
| 1 | Структура репозитория | ключевые каталоги и их назначение |
| 2 | Карта сценариев и команд запуска | `сценарий -> назначение -> команда запуска -> артефакты` |
| 3 | Структура артефактов | `тип файла -> назначение -> где появляется` |
| 4 | Подтвержденные результаты lane-change | PRR, collision, decision chain |
| 5 | Подтвержденные результаты intersection | PRR, first decision, forced speed, collision |
| 6 | Аналитические скрипты и их роль | `script -> функция -> output` |
| 7 | Ограничения и открытые вопросы | зависимости, нестабильные прогоны, неполные summary |
| 8 | Оценка затраченных часов | разбивка по блокам работ |
| 9 | Инвентарь raw SQLite dataset | таблицы, строки и временные диапазоны по `cttc-nr-v2x-demo-simple` |

## 5. CSV-таблицы, на которые нужно ссылаться напрямую

| Файл в пакете | Для какого раздела |
|---|---|
| `evidence/csv/lane_change/intuitive_prr_summary.csv` | основные результаты lane-change |
| `evidence/csv/lane_change/intuitive_dbm_prr_maneuver_chain.csv` | причинная цепочка качества связи |
| `evidence/csv/lane_change/intuitive_key_events.csv` | ключевые времена |
| `evidence/csv/lane_change/drop_decision_summary.csv` | strict match по decision timeline |
| `evidence/csv/lane_change/collision_causality.csv` | strongest causal window для lane-change |
| `evidence/csv/intersection/intersection_summary.csv` | основные результаты intersection |
| `evidence/csv/intersection/drop_decision_summary.csv` | strict match в junction кейсе |
| `evidence/csv/intersection/collision_causality.csv` | strongest causal window для junction кейса |
| `evidence/csv/sweeps/rssi_safety_summary.csv` | RSSI/safety sweep |
| `evidence/csv/sweeps/sionna_incident_summary_success.csv` | успешный Sionna incident sweep |
| `evidence/csv/sweeps/sionna_incident_summary_zero_attempt.csv` | промежуточный неудачный запуск как ограничение |
| `evidence/csv/eva_series/summary-all-runs.csv` | дополнительная EVA-серия из 6 прогонов |
| `evidence/csv/eva_series/per-vehicle-cam-from-ev.csv` | распределение CAM от emergency vehicle по автомобилям |
| `evidence/csv/eva_series/inter-cam-gaps.csv` | inter-CAM gap по EVA-серии |
| `evidence/csv/eva_series/eva-good-speed-timeseries.csv` | baseline speed/lane timeseries |
| `evidence/csv/eva_series/eva-vbad-speed-timeseries.csv` | very-high-loss speed/lane timeseries |
| `evidence/csv/eva_series/eva-lowpen-speed-timeseries.csv` | low-penetration speed/lane timeseries |
| `evidence/csv/lena_db_dataset_inventory.csv` | raw SQLite dataset inventory по `cttc-nr-v2x-demo-simple` |
| `evidence/csv/lena_pktTxRx_ide.csv` | sample экспорт `pktTxRx` из raw `.db` |
| `evidence/csv/lena_psschRxUePhy_ide.csv` | sample экспорт PHY-таблицы `psschRxUePhy` |

## 6. Дополнительные потенциальные фигуры из EVA-серии

| № | Основа | Что можно построить |
|---|---|---|
| 22 | `evidence/csv/eva_series/summary-all-runs.csv` | bar chart `PRR + latency` по 6 прогонам |
| 23 | `evidence/csv/eva_series/inter-cam-gaps.csv` | CDF `inter-CAM gap` |
| 24 | `evidence/csv/eva_series/per-vehicle-cam-from-ev.csv` | box plot по числу CAM от emergency vehicle |
| 25 | `evidence/csv/eva_series/eva-good-speed-timeseries.csv` + `eva-vbad-speed-timeseries.csv` + `eva-lowpen-speed-timeseries.csv` | сравнение скоростей/полос отдельных автомобилей |
